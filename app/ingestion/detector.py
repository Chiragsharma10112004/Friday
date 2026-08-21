import re
import urllib.parse


class PlatformDetector:
    """
    Deterministic URL pattern and hostname detector for job posting sources.
    """

    GREENHOUSE_DOMAINS = (
        "boards.greenhouse.io",
        "job-boards.greenhouse.io",
        "boards.eu.greenhouse.io",
    )

    LEVER_DOMAINS = (
        "jobs.lever.co",
        "jobs.eu.lever.co",
    )

    WORKDAY_PATTERNS = (
        re.compile(r"[\w.-]*\.myworkdayjobs\.com", re.IGNORECASE),
        re.compile(r"[\w.-]*\.workday\.com", re.IGNORECASE),
    )

    LINKEDIN_DOMAINS = (
        "linkedin.com",
        "www.linkedin.com",
        "in.linkedin.com",
        "uk.linkedin.com",
    )

    INDEED_PATTERNS = (
        re.compile(r"^([\w.-]+\.)?indeed\.(com|[a-z]{2,3}(\.[a-z]{2})?)$", re.IGNORECASE),
    )

    @classmethod
    def detect(cls, url: str, parsed: urllib.parse.ParseResult) -> str:
        """
        Identify the source platform string:
        'greenhouse' | 'lever' | 'workday' | 'linkedin' | 'indeed' | 'generic'
        """
        hostname = (parsed.hostname or "").lower()

        # Greenhouse detection
        if any(hostname == domain or hostname.endswith("." + domain) for domain in cls.GREENHOUSE_DOMAINS):
            return "greenhouse"

        # Embedded Greenhouse check (e.g. company.com/jobs?gh_jid=12345 or ?token=123)
        if "gh_jid" in parsed.query.lower() or "greenhouse.io" in parsed.path.lower():
            return "greenhouse"

        # Lever detection
        if any(hostname == domain or hostname.endswith("." + domain) for domain in cls.LEVER_DOMAINS):
            return "lever"

        # Workday detection
        if any(pattern.match(hostname) for pattern in cls.WORKDAY_PATTERNS):
            return "workday"

        # LinkedIn detection
        if any(hostname == domain or hostname.endswith("." + domain) for domain in cls.LINKEDIN_DOMAINS):
            return "linkedin"

        # Indeed detection
        if any(pattern.match(hostname) for pattern in cls.INDEED_PATTERNS):
            return "indeed"

        return "generic"

