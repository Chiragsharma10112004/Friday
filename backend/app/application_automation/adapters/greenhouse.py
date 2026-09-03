from typing import List
from bs4 import BeautifulSoup

from app.application_automation.adapters.base import BaseFormAdapter
from app.application_automation.schemas import (
    FormPlatform,
    FieldInspectionItem,
    QuestionType,
    FieldConfidence,
    FieldStatus,
)


class GreenhouseFormAdapter(BaseFormAdapter):
    """
    Adapter for inspecting and interacting with Greenhouse application forms.
    """

    @property
    def platform(self) -> FormPlatform:
        return FormPlatform.GREENHOUSE

    def inspect_form(self, html_content: str, url: str) -> List[FieldInspectionItem]:
        fields: List[FieldInspectionItem] = []
        soup = BeautifulSoup(html_content, "html.parser")

        form = soup.select_one("#application_form, #grnhse_app, form")
        if not form:
            return fields

        # 1. Inspect standard Greenhouse field containers
        field_containers = form.select(".field, .application-field, div[class*='field']")
        if not field_containers:
            # Fallback to direct input controls if structured containers not present
            field_containers = form.select("div:has(input, select, textarea)")

        seen_names = set()

        for container in field_containers:
            label_tag = container.select_one("label")
            label_text = label_tag.get_text(strip=True) if label_tag else ""

            # Check for input, select, or textarea
            control = container.select_one("input:not([type='hidden']), select, textarea")
            if not control:
                continue

            html_id = control.get("id") or ""
            html_name = control.get("name") or ""
            input_type = control.get("type") or ""

            # Skip submit / button controls (SAFETY GUARANTEE)
            if input_type in ("submit", "button", "reset"):
                continue

            field_key = html_id or html_name
            if not field_key or field_key in seen_names:
                continue
            seen_names.add(field_key)

            control_type = self.determine_control_type(control.name, input_type)

            # Extract options if select
            options = []
            if control.name == "select":
                options = [opt.get_text(strip=True) for opt in control.find_all("option") if opt.get_text(strip=True)]

            if not label_text:
                label_text = control.get("aria-label") or control.get("placeholder") or html_name.replace("_", " ").title()

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

