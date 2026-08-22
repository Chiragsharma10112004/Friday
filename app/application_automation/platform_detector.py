import urllib.parse
from bs4 import BeautifulSoup
from app.ingestion.detector import PlatformDetector as Phase2Detector
from app.application_automation.schemas import FormPlatform


class ApplicationPlatformDetector:
    """
    Identifies ATS and career form platforms using URL signatures and DOM structural heuristics.
    """

    @classmethod
    def detect_from_url_and_dom(cls, url: str, html_content: str = "") -> FormPlatform:
        parsed = urllib.parse.urlparse(url)
        phase2_platform = Phase2Detector.detect(url, parsed)

        if phase2_platform == "greenhouse":
            return FormPlatform.GREENHOUSE
        if phase2_platform == "lever":
            return FormPlatform.LEVER
        if phase2_platform == "workday":
            return FormPlatform.WORKDAY
        if phase2_platform == "linkedin":
            return FormPlatform.LINKEDIN
        if phase2_platform == "indeed":
            return FormPlatform.INDEED

        # If URL was generic, inspect DOM for embedded ATS elements
        if html_content:
            soup = BeautifulSoup(html_content, "html.parser")
            if soup.select_one("#application_form, #grnhse_app, form[action*='greenhouse.io']"):
                return FormPlatform.GREENHOUSE
            if soup.select_one(".application-form, .lever-form, form[action*='lever.co']"):
                return FormPlatform.LEVER
            if soup.select_one("div[data-automation-id*='workday'], form[action*='myworkdayjobs.com']"):
                return FormPlatform.WORKDAY

        return FormPlatform.GENERIC

