"""Mobile-friendly birth date: Mwaka, Mwezi, Siku (dropdowns)."""

import calendar
from datetime import date

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone


SWAHILI_MONTHS = (
    (1, "Januari"),
    (2, "Februari"),
    (3, "Machi"),
    (4, "Aprili"),
    (5, "Mei"),
    (6, "Juni"),
    (7, "Julai"),
    (8, "Agosti"),
    (9, "Septemba"),
    (10, "Oktoba"),
    (11, "Novemba"),
    (12, "Desemba"),
)


def _year_choices():
    current = timezone.localdate().year
    choices = [("", "Mwaka")]
    for y in range(current - 5, current - 101, -1):
        choices.append((y, str(y)))
    return choices


class MobileBirthDateWidget(forms.MultiWidget):
    """Year first — easier to pick birth year on phones."""

    template_name = "members/widgets/mobile_birth_date.html"

    def __init__(self, attrs=None):
        widgets = (
            forms.Select(
                choices=_year_choices(),
                attrs={"class": "form-control dob-select", "aria-label": "Mwaka"},
            ),
            forms.Select(
                choices=[("", "Mwezi")] + list(SWAHILI_MONTHS),
                attrs={"class": "form-control dob-select", "aria-label": "Mwezi"},
            ),
            forms.Select(
                choices=[("", "Siku")] + [(d, str(d)) for d in range(1, 32)],
                attrs={"class": "form-control dob-select", "aria-label": "Siku"},
            ),
        )
        super().__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            return [value.year, value.month, value.day]
        return [None, None, None]


class MobileBirthDateField(forms.MultiValueField):
    widget = MobileBirthDateWidget
    default_error_messages = {
        "required": "Weka tarehe kamili ya kuzaliwa (mwaka, mwezi, siku).",
        "invalid": "Tarehe ya kuzaliwa si sahihi.",
    }

    def __init__(self, *args, **kwargs):
        fields = (
            forms.IntegerField(required=False),
            forms.IntegerField(required=False),
            forms.IntegerField(required=False),
        )
        kwargs.setdefault("label", "Tarehe ya kuzaliwa")
        super().__init__(fields=fields, require_all_fields=False, *args, **kwargs)

    def compress(self, data_list):
        if not data_list:
            return None
        if any(v in (None, "") for v in data_list):
            if self.required:
                raise ValidationError(self.error_messages["required"], code="required")
            return None
        try:
            year, month, day = (int(data_list[0]), int(data_list[1]), int(data_list[2]))
        except (TypeError, ValueError):
            raise ValidationError(self.error_messages["invalid"], code="invalid")

        max_day = calendar.monthrange(year, month)[1]
        if day < 1 or day > max_day:
            raise ValidationError("Siku si sahihi kwa mwezi huo.", code="invalid")

        today = timezone.localdate()
        born = date(year, month, day)
        if born > today:
            raise ValidationError("Tarehe ya kuzaliwa haiwezi kuwa baadaye.", code="invalid")
        if (today - born).days > 365 * 120:
            raise ValidationError("Tarehe ya kuzaliwa haionekani sahihi.", code="invalid")

        return born
