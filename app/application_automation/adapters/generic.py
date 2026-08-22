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
    Fallback adapter for standard HTML application forms.
    """

    @property
    def platform(self) -> FormPlatform:
        return FormPlatform.GENERIC

    def inspect_form(self, html_content: str, url: str) -> List[FieldInspectionItem]:
        fields: List[FieldInspectionItem] = []
        soup = BeautifulSoup(html_content, "html.parser")

        # Find primary form or inspect body
        form = soup.select_one("form") or soup.body or soup

        # Find all interactive controls
        controls = form.select("input:not([type='hidden']), select, textarea")
        seen_keys = set()

        for control in controls:
            html_id = control.get("id") or ""
            html_name = control.get("name") or ""
            input_type = control.get("type") or ""

            # Safety: skip submit controls
            if input_type in ("submit", "button", "reset", "image"):
                continue

            field_key = html_id or html_name
            if not field_key or field_key in seen_keys:
                continue
            seen_keys.add(field_key)

            # Resolve associated label
            label_text = ""
            if html_id:
                label_tag = soup.find("label", attrs={"for": html_id})
                if label_tag:
                    label_text = label_tag.get_text(strip=True)

            if not label_text and control.parent and control.parent.name == "label":
                label_text = control.parent.get_text(strip=True)

            if not label_text:
                label_text = (
                    control.get("aria-label")
                    or control.get("placeholder")
                    or html_name.replace("_", " ").title()
                )

            control_type = self.determine_control_type(control.name, input_type)

            options = []
            if control.name == "select":
                options = [opt.get_text(strip=True) for opt in control.find_all("option") if opt.get_text(strip=True)]

            fields.append(
                FieldInspectionItem(
                    field_id=f"#{html_id}" if html_id else f"[name='{html_name}']",
                    label=label_text.replace("*", "").strip(),
                    html_name=html_name,
                    control_type=control_type,
                    options=options,
                )
            )

        return fields

