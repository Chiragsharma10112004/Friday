import re
from typing import List
from bs4 import BeautifulSoup

from app.application_automation.adapters.base import BaseFormAdapter
from app.application_automation.schemas import (
    FormPlatform,
    FieldInspectionItem,
    QuestionType,
)


class GenericFormAdapter(BaseFormAdapter):
    """
    Robust generic adapter for parsing standard and dynamically structured HTML forms.
    Filters search bars, cookie banners, tracking pixels, and newsletter inputs.
    """

    IRRELEVANT_NAMES = {
        "q", "query", "search", "k", "keyword", "keywords", "site_search",
        "_csrf", "csrf", "csrf_token", "authenticity_token", "__requestverificationtoken",
        "cookie_consent", "newsletter", "subscriber_email", "subscribe_email"
    }

    @property
    def platform(self) -> FormPlatform:
        return FormPlatform.GENERIC

    def inspect_form(self, html_content: str, url: str) -> List[FieldInspectionItem]:
        fields: List[FieldInspectionItem] = []
        if not html_content:
            return fields

        soup = BeautifulSoup(html_content, "html.parser")

        # 1. Remove non-form structural distractions (scripts, styles, navs, footers, search widgets, cookie bars)
        for noise in soup.select("script, style, noscript, nav, header, footer, [id*='cookie'], [class*='cookie'], [id*='search'], [class*='search-form']"):
            noise.decompose()

        # Find primary application form or body
        container = (
            soup.select_one("form[id*='app'], form[class*='app'], form[id*='job'], form[class*='job'], form[action*='apply']")
            or soup.select_one("form")
            or soup.body
            or soup
        )

        # 2. Select interactive input controls
        controls = container.select("input:not([type='hidden']), select, textarea, [contenteditable='true']")
        seen_keys = set()

        for control in controls:
            tag_name = control.name
            html_id = (control.get("id") or "").strip()
            html_name = (control.get("name") or "").strip()
            input_type = (control.get("type") or "").strip().lower()
            autocomplete = (control.get("autocomplete") or "").strip().lower()
            aria_label = (control.get("aria-label") or "").strip()
            placeholder = (control.get("placeholder") or "").strip()

            # Safety: skip non-fillable buttons / submit / reset / search
            if input_type in ("submit", "button", "reset", "image", "search"):
                continue

            # Skip hidden / invisible elements
            style_str = (control.get("style") or "").lower()
            if "display:none" in style_str or "visibility:hidden" in style_str or control.get("aria-hidden") == "true":
                continue

            # Filter out search / csrf / newsletter inputs
            norm_name = html_name.lower().replace("-", "_")
            norm_id = html_id.lower().replace("-", "_")
            if (norm_name in self.IRRELEVANT_NAMES or norm_id in self.IRRELEVANT_NAMES) and input_type != "email":
                continue

            field_key = html_id or html_name or aria_label or placeholder
            if not field_key or field_key in seen_keys:
                continue
            seen_keys.add(field_key)

            # 3. Label Resolution
            label_text = ""

            # Check <label for="id">
            if html_id:
                label_tag = soup.find("label", attrs={"for": html_id})
                if label_tag:
                    label_text = label_tag.get_text(separator=" ", strip=True)

            # Check enclosing <label>
            if not label_text and control.parent and control.parent.name == "label":
                label_text = control.parent.get_text(separator=" ", strip=True)

            # Check aria-labelledby
            if not label_text and control.get("aria-labelledby"):
                ref_id = control.get("aria-labelledby")
                ref_tag = soup.find(id=ref_id)
                if ref_tag:
                    label_text = ref_tag.get_text(separator=" ", strip=True)

            # Check preceding sibling or parent container title
            if not label_text and control.parent:
                heading = control.parent.select_one(".label, .field-label, .question-label, label, span, h3, h4")
                if heading:
                    label_text = heading.get_text(separator=" ", strip=True)

            # Fallbacks: aria-label -> placeholder -> html_name
            if not label_text:
                label_text = aria_label or placeholder or html_name.replace("_", " ").replace("-", " ").title()

            control_type = self.determine_control_type(tag_name, input_type)

            options = []
            if tag_name == "select":
                options = [
                    opt.get_text(strip=True)
                    for opt in control.find_all("option")
                    if opt.get_text(strip=True) and not opt.get_text(strip=True).startswith("--")
                ]

            selector = f"#{html_id}" if html_id else (f"[name='{html_name}']" if html_name else f"[placeholder='{placeholder}']")

            fields.append(
                FieldInspectionItem(
                    field_id=selector,
                    label=label_text.replace("*", "").replace("✱", "").strip() or "Question",
                    html_name=html_name or html_id,
                    control_type=control_type,
                    options=options,
                )
            )

        return fields
