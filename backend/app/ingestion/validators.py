import socket
import ipaddress
import urllib.parse
from typing import Tuple, Optional
import requests

from app.ingestion.errors import IngestionErrorCode, IngestionException

MAX_REDIRECTS = 3
DEFAULT_TIMEOUT_SECONDS = 10
MAX_RESPONSE_BYTES = 5 * 1024 * 1024  # 5 MB
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 (compatible; FRIDAY-JobIngestion/1.0)"

# Explicit cloud metadata hostnames & IP strings
BLOCKED_HOSTNAMES = {
    "metadata.google.internal",
    "metadata.internal",
    "instance-data",
}

BLOCKED_IP_STRINGS = {
    "169.254.169.254",      # AWS, GCP, Azure, OpenStack metadata
    "fd00:ec2::254",         # AWS IPv6 IMDS
    "100.100.100.200",       # Alibaba Cloud metadata
    "169.254.169.250",       # Oracle Cloud metadata
}


def validate_url_syntax(url_str: str) -> urllib.parse.ParseResult:
    """
    Validate basic URL syntax and ensure scheme is HTTP or HTTPS.
    """
    if not url_str or not isinstance(url_str, str):
        raise IngestionException(
            code=IngestionErrorCode.INVALID_URL,
            message="Job URL must be a non-empty string."
        )

    url_str = url_str.strip()
    try:
        parsed = urllib.parse.urlparse(url_str)
    except Exception as e:
        raise IngestionException(
            code=IngestionErrorCode.INVALID_URL,
            message=f"Malformed URL structure: {str(e)}"
        )

    if parsed.scheme.lower() not in ("http", "https"):
        raise IngestionException(
            code=IngestionErrorCode.INVALID_URL,
            message=f"Unsupported URL scheme '{parsed.scheme}'. Only HTTP and HTTPS are permitted."
        )

    if not parsed.netloc:
        raise IngestionException(
            code=IngestionErrorCode.INVALID_URL,
            message="URL is missing a valid hostname / domain."
        )

    return parsed


def validate_hostname_against_ssrf(hostname: str, port: Optional[int] = None):
    """
    Perform DNS pre-resolution and verify that the target host does not resolve
    to private, loopback, link-local, multicast, or cloud metadata IP addresses.
    
    Note on Security / DNS Rebinding:
    This function verifies all resolved IP addresses immediately prior to connection.
    In environments requiring defense against advanced Time-of-Check to Time-of-Use (TOCTOU)
    DNS rebinding attacks, an egress firewall or custom IP-pinned HTTP transport adapter should
    be paired with this validator.
    """
    cleaned_host = hostname.split(":")[0].strip().lower()

    if cleaned_host in BLOCKED_HOSTNAMES:
        raise IngestionException(
            code=IngestionErrorCode.SSRF_ATTEMPT_BLOCKED,
            message="Access to internal cloud metadata hostnames is strictly prohibited."
        )

    # Check direct IP string literals
    if cleaned_host in BLOCKED_IP_STRINGS:
        raise IngestionException(
            code=IngestionErrorCode.SSRF_ATTEMPT_BLOCKED,
            message="Access to cloud metadata IP addresses is strictly prohibited."
        )

    resolved_port = port or 80

    try:
        addr_info = socket.getaddrinfo(
            cleaned_host,
            resolved_port,
            family=socket.AF_UNSPEC,
            type=socket.SOCK_STREAM
        )
    except socket.gaierror as e:
        raise IngestionException(
            code=IngestionErrorCode.NETWORK_FAILURE,
            message=f"DNS resolution failed for host '{cleaned_host}': {str(e)}",
            retryable=True
        )
    except Exception as e:
        raise IngestionException(
            code=IngestionErrorCode.NETWORK_FAILURE,
            message=f"Network error resolving host '{cleaned_host}': {str(e)}",
            retryable=True
        )

    if not addr_info:
        raise IngestionException(
            code=IngestionErrorCode.NETWORK_FAILURE,
            message=f"No IP addresses resolved for host '{cleaned_host}'.",
            retryable=True
        )

    for entry in addr_info:
        sockaddr = entry[4]
        ip_str = sockaddr[0]

        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            raise IngestionException(
                code=IngestionErrorCode.SSRF_ATTEMPT_BLOCKED,
                message=f"Invalid IP address representation encountered: {ip_str}"
            )

        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
            or str(ip) in BLOCKED_IP_STRINGS
        ):
            raise IngestionException(
                code=IngestionErrorCode.SSRF_ATTEMPT_BLOCKED,
                message=f"Access to private, loopback, or metadata IP addresses ({ip_str}) is prohibited."
            )


class SafeHttpClient:
    """
    Hardened outbound HTTP client enforcing:
    - Pre-request DNS validation against SSRF
    - Strict manual redirect loop with re-validation on every hop
    - Timeout constraints
    - Maximum payload size constraints
    """

    @staticmethod
    def get(
        url: str,
        headers: Optional[dict] = None,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
        max_redirects: int = MAX_REDIRECTS,
        max_bytes: int = MAX_RESPONSE_BYTES
    ) -> requests.Response:
        current_url = url
        req_headers = {
            "User-Agent": DEFAULT_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json;q=0.8,*/*;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
        }
        if headers:
            req_headers.update(headers)

        session = requests.Session()

        for hop in range(max_redirects + 1):
            parsed = validate_url_syntax(current_url)
            validate_hostname_against_ssrf(parsed.hostname, parsed.port)

            try:
                response = session.get(
                    current_url,
                    headers=req_headers,
                    timeout=timeout,
                    allow_redirects=False,
                    stream=True
                )
            except requests.Timeout as e:
                raise IngestionException(
                    code=IngestionErrorCode.REQUEST_TIMEOUT,
                    message=f"Request to '{current_url}' timed out after {timeout} seconds.",
                    retryable=True
                )
            except requests.RequestException as e:
                raise IngestionException(
                    code=IngestionErrorCode.NETWORK_FAILURE,
                    message=f"Network request failed: {str(e)}",
                    retryable=True
                )

            # Check for redirect status codes (301, 302, 303, 307, 308)
            if response.status_code in (301, 302, 303, 307, 308):
                location = response.headers.get("Location")
                if not location:
                    break  # No location header to follow

                # Resolve relative redirect URLs to absolute
                current_url = urllib.parse.urljoin(current_url, location)
                if hop >= max_redirects:
                    raise IngestionException(
                        code=IngestionErrorCode.NETWORK_FAILURE,
                        message=f"Exceeded maximum redirect limit ({max_redirects})."
                    )
                continue

            # Read content with payload size enforcement
            content_chunks = []
            bytes_read = 0
            try:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        bytes_read += len(chunk)
                        if bytes_read > max_bytes:
                            raise IngestionException(
                                code=IngestionErrorCode.MALFORMED_PAGE,
                                message=f"Response body exceeded maximum allowed limit of {max_bytes // (1024*1024)} MB."
                            )
                        content_chunks.append(chunk)
            except IngestionException:
                raise
            except Exception as e:
                raise IngestionException(
                    code=IngestionErrorCode.NETWORK_FAILURE,
                    message=f"Error reading response body: {str(e)}",
                    retryable=True
                )

            # Cache full content onto response object
            response._content = b"".join(content_chunks)
            return response

        return response

