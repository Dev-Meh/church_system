"""Mobile-friendly birth date: year, month, day dropdowns."""

import calendar
from datetime import date

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .language_utils import get_translation


def _month_choices(language):
    lang = language or "en"
    if lang == "sw":
        return [(m, get_translation(f"month_{m}", lang)) for m in range(1, 13)]
    return [(m, get_translation(f"month_{m}", lang)) for m in range(1, 13)]


def _year_choices(language):
    lang = language or "en"
    current = timezone.localdate().year
    choices = [("", get_translation("dob_year", lang))]
    for y in range(current - 5, current - 101, -1):
        choices.append((y, str(y)))
    return choices


class MobileBirthDateWidget(forms.MultiWidget):
    """Year first — easier to pick birth year on phones."""

    template_name = "members/widgets/mobile_birth_date.html"

    def __init__(self, attrs=None, language="en"):
        lang = language or "en"
        widgets = (
            forms.Select(
                choices=_year_choices(lang),
                attrs={"class": "form-control dob-select", "aria-label": get_translation("dob_year", lang)},
            ),
            forms.Select(
                choices=[("", get_translation("dob_month", lang))] + _month_choices(lang),
                attrs={"class": "form-control dob-select", "aria-label": get_translation("dob_month", lang)},
            ),
            forms.Select(
                choices=[("", get_translation("dob_day", lang))] + [(d, str(d)) for d in range(1, 32)],
                attrs={"class": "form-control dob-select", "aria-label": get_translation("dob_day", lang)},
            ),
        )
        super().__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            return [value.year, value.month, value.day]
        return [None, None, None]


class MobileBirthDateField(forms.MultiValueField):
    widget = MobileBirthDateWidget

    def __init__(self, *args, language="en", **kwargs):
        self._language = language or "en"
        lang = self._language
        fields = (
            forms.IntegerField(required=False),
            forms.IntegerField(required=False),
            forms.IntegerField(required=False),
        )
        error_messages = kwargs.pop("error_messages", {})
        default_error_messages = {
            "required": get_translation("dob_required", lang),
            "invalid": get_translation("dob_invalid", lang),
        }
        default_error_messages.update(error_messages)
        kwargs["error_messages"] = default_error_messages
        kwargs.setdefault("label", get_translation("date_of_birth", lang))
        super().__init__(fields=fields, require_all_fields=False, *args, **kwargs)
        self.widget = MobileBirthDateWidget(language=lang)

    def compress(self, data_list):
        lang = getattr(self, "_language", "en")
        t = lambda key: get_translation(key, lang)

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
            raise ValidationError(t("dob_day_invalid"), code="invalid")

        today = timezone.localdate()
        born = date(year, month, day)
        if born > today:
            raise ValidationError(t("dob_future"), code="invalid")
        if (today - born).days > 365 * 120:
            raise ValidationError(t("dob_unlikely"), code="invalid")

        return born
