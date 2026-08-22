import re
import urllib.parse
from typing import List, Tuple, Set, Dict
from app.job_discovery.schemas import DiscoveredJob


class JobDeduplicator:
    """
    Deterministic 4-tier job deduplication engine.
    Filters duplicates without AI hallucination.
    """

    TRACKING_PARAMS = {
        "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
        "ref", "source", "gh_jid", "lever-origin", "lever-source", "mode", "sid"
    }

    @classmethod
    def canonicalize_url(cls, url: str) -> str:
        """
        Normalize URL by stripping tracking queries, lowercase host, and removing fragments.
        """
        if not url:
            return ""

        parsed = urllib.parse.urlparse(url.strip())
        query_dict = urllib.parse.parse_qs(parsed.query)

        # Filter out tracking params
        clean_query = {
            k: v for k, v in query_dict.items()
            if k.lower() not in cls.TRACKING_PARAMS
        }

        encoded_query = urllib.parse.urlencode(clean_query, doseq=True)
        path = parsed.path.rstrip("/")

        return urllib.parse.urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            path,
            "",
            encoded_query,
            ""
        ))

    @staticmethod
    def normalize_text(text: str) -> str:
        if not text:
            return ""
        text = text.lower().strip()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        return " ".join(text.split())

    @classmethod
    def generate_fingerprint(cls, job: DiscoveredJob) -> Tuple[str, str, str, str]:
        """
        Produce 4 distinct identification keys for a job:
        1. Exact provider + external_id
        2. Canonical source URL
        3. Normalized company + title + location
        4. Content signature
        """
        ext_key = f"{job.provider}:{job.external_id}" if job.external_id else ""
        url_key = cls.canonicalize_url(job.source_url)
        norm_company = cls.normalize_text(job.company)
        norm_title = cls.normalize_text(job.title)
        norm_loc = cls.normalize_text(job.location or "remote")
        entity_key = f"{norm_company}|{norm_title}|{norm_loc}"
        norm_desc = cls.normalize_text(job.description[:400])
        content_key = f"{norm_company}|{norm_desc[:200]}" if norm_desc else ""

        return ext_key, url_key, entity_key, content_key

    @classmethod
    def deduplicate(cls, jobs: List[DiscoveredJob]) -> Tuple[List[DiscoveredJob], int]:
        """
        Deduplicates a list of discovered jobs in deterministic order.
        Returns (unique_jobs, duplicates_skipped_count).
        """
        seen_ext_ids: Set[str] = set()
        seen_urls: Set[str] = set()
        seen_entities: Set[str] = set()
        seen_contents: Set[str] = set()

        unique_jobs: List[DiscoveredJob] = []
        duplicates_skipped = 0

        for job in jobs:
            ext_key, url_key, entity_key, content_key = cls.generate_fingerprint(job)

            is_duplicate = False

            if ext_key and ext_key in seen_ext_ids:
                is_duplicate = True
            elif url_key and url_key in seen_urls:
                is_duplicate = True
            elif entity_key and entity_key in seen_entities:
                is_duplicate = True
            elif content_key and content_key in seen_contents:
                is_duplicate = True

            if is_duplicate:
                duplicates_skipped += 1
                continue

            if ext_key:
                seen_ext_ids.add(ext_key)
            if url_key:
                seen_urls.add(url_key)
            if entity_key:
                seen_entities.add(entity_key)
            if content_key:
                seen_contents.add(content_key)

            unique_jobs.append(job)

        return unique_jobs, duplicates_skipped
