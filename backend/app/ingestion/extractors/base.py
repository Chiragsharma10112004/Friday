from abc import ABC, abstractmethod
import json
import urllib.parse
from typing import Optional, List, Dict, Any
from bs4 import BeautifulSoup

from app.ingestion.schemas import NormalizedJobPosting
from app.ingestion.errors import IngestionErrorCode, IngestionException


class BaseJobExtractor(ABC):
    """
    Abstract base class for all platform-specific job extractors.
    """

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Name of the platform (e.g. 'greenhouse', 'lever', 'generic')."""
        pass

    @abstractmethod
    def can_handle(self, url: str, parsed: urllib.parse.ParseResult) -> bool:
        """Return True if this extractor can process the given URL."""
        pass

    @abstractmethod
    def extract(self, url: str, parsed: urllib.parse.ParseResult) -> NormalizedJobPosting:
        """
        Execute extraction and return a NormalizedJobPosting instance
        or raise IngestionException.
        """
        pass

    # ==========================================
    # Common HTML / Text Extraction Utilities
    # ==========================================

    @staticmethod
    def clean_html_to_text(html_content: str) -> str:
        """
        Convert HTML content to clean, readable plain text / markdown representation.
        """
        if not html_content or not isinstance(html_content, str):
            return ""

        soup = BeautifulSoup(html_content, "html.parser")

        # Strip non-text or dangerous tags
        for element in soup(["script", "style", "noscript", "iframe", "svg", "canvas", "form", "button", "input"]):
            element.decompose()

        # Format bullet list items
        for li in soup.find_all("li"):
            li.insert_before("\n• ")

        # Format headings and paragraphs with newlines
        for block in soup.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6", "div", "br", "section", "article"]):
            block.append("\n")

        text = soup.get_text(separator=" ")
        
        # Clean up whitespace
        lines = [line.strip() for line in text.splitlines()]
        cleaned_lines = []
        for line in lines:
            if line:
                cleaned_lines.append(line)
            elif cleaned_lines and cleaned_lines[-1] != "":
                cleaned_lines.append("")

        return "\n".join(cleaned_lines).strip()

    @staticmethod
    def extract_json_ld_objects(html_content: str) -> List[Dict[str, Any]]:
        """
        Extract all JSON-LD script blocks from HTML.
        """
        if not html_content:
            return []

        soup = BeautifulSoup(html_content, "html.parser")
        results = []

        for script in soup.find_all("script", type="application/ld+json"):
            content = script.string
            if not content:
                continue
            try:
                data = json.loads(content.strip())
                if isinstance(data, list):
                    results.extend(data)
                elif isinstance(data, dict):
                    # Handle @graph wrapper
                    if "@graph" in data and isinstance(data["@graph"], list):
                        results.extend(data["@graph"])
                    else:
                        results.append(data)
            except Exception:
                continue

        return results

    @classmethod
    def find_job_posting_json_ld(cls, html_content: str) -> Optional[Dict[str, Any]]:
        """
        Find the first JSON-LD object representing a JobPosting schema.
        """
        for obj in cls.extract_json_ld_objects(html_content):
            obj_type = obj.get("@type", "")
            if isinstance(obj_type, list):
                if any(t.lower() == "jobposting" for t in obj_type if isinstance(t, str)):
                    return obj
            elif isinstance(obj_type, str) and obj_type.lower() == "jobposting":
                return obj
        return None

