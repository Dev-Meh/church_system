"""Edit existing church-wide contribution records (accountant corrections)."""

from django.utils import timezone

from members.language_utils import get_translation
from .forms import (
    SUNDAY_OFFERING_NOTE_PREFIX,
    TitheEntryForm,
    MalimbukoEntryForm,
    SundayOfferingEntryForm,
    AnonymousContributionEntryForm,
)

SUNDAY_PREFIX = SUNDAY_OFFERING_NOTE_PREFIX


def _build_sunday_notes(cleaned_data, language="en"):
    session = cleaned_data.get("service_session") or ""
    user_notes = (cleaned_data.get("notes") or "").strip()
    parts = [SUNDAY_PREFIX]
    if session:
        session_labels = {
            "morning": get_translation("sunday_session_morning", language),
            "afternoon": get_translation("sunday_session_afternoon", language),
            "evening": get_translation("sunday_session_evening", language),
        }
        label = session_labels.get(session, session)
        parts.append(f'{get_translation("sunday_service_label", language)}: {label}')
    if user_notes:
        parts.append(user_notes)
    return ". ".join(parts)


def donation_edit_kind(donation):
    """Return edit form kind or None if record cannot be edited here."""
    if donation.recorded_for_group_id:
        return None
    notes = donation.notes or ""
    if "Malipo ya deni la ujenzi" in notes:
        return None
    if donation.category_id and getattr(donation.category, "name", "").lower() == "ujenzi":
        return None

    dtype = donation.donation_type
    if dtype == "tithe":
        return "tithe"
    if dtype == "offering":
        if SUNDAY_PREFIX in notes:
            return "sunday_offering"
        return "offering"
    if dtype == "special":
        return "malimbuko"
    if dtype == "other":
        return "shukrani"
    return None


def donation_list_url_name(donation):
    kind = donation_edit_kind(donation)
    return {
        "tithe": "donations:tithe_list",
        "offering": "donations:offering_list",
        "sunday_offering": "donations:offering_list",
        "malimbuko": "donations:malimbuko_list",
        "shukrani": "donations:shukrani_list",
    }.get(kind, "donations:home")


def _tithe_initial(donation):
    notes = (donation.notes or "").strip()
    if donation.tithe_gift_type == "asset" and notes.startswith("Zaka ya mali:"):
        notes = notes.split(":", 1)[-1].strip()
    return {
        "donor": donation.donor_id,
        "contribution_date": donation.contribution_date,
        "payment_method": donation.payment_method,
        "zaka_type": donation.tithe_gift_type or "money",
        "amount": donation.amount if donation.tithe_gift_type == "money" else None,
        "asset_description": donation.tithe_asset_description or "",
        "notes": notes,
    }


def _malimbuko_initial(donation):
    notes = donation.notes or ""
    extra_notes = ""
    if notes.startswith("Malimbuko (miladi ya kanisa)"):
        remainder = notes[len("Malimbuko (miladi ya kanisa)") :].strip()
        if remainder.startswith("."):
            remainder = remainder[1:].strip()
        parts = [p.strip() for p in remainder.split(".") if p.strip()]
        filtered = []
        for part in parts:
            if part.startswith("Miladi:"):
                continue
            if part.startswith("Mavuno:"):
                continue
            filtered.append(part)
        extra_notes = ". ".join(filtered)
    return {
        "contribution_date": donation.contribution_date,
        "payment_method": donation.payment_method,
        "gift_type": donation.tithe_gift_type or "money",
        "amount": donation.amount if donation.tithe_gift_type == "money" else None,
        "asset_description": donation.tithe_asset_description or "",
        "miladi_source": donation.malimbuko_miladi_source,
        "notes": extra_notes,
    }


def _anonymous_initial(donation):
    notes = (donation.notes or "").strip()
    if donation.donation_type == "offering" and notes.startswith(SUNDAY_PREFIX):
        notes = ""
    return {
        "contribution_date": donation.contribution_date,
        "payment_method": donation.payment_method,
        "amount": donation.amount,
        "notes": notes,
    }


def _parse_sunday_session(notes):
    lower = (notes or "").lower()
    for code in ("morning", "afternoon", "evening"):
        if code in lower:
            return code
    return ""


def _sunday_user_notes(notes):
    text = notes or ""
    if not text.startswith(SUNDAY_PREFIX):
        return text.strip()
    remainder = text[len(SUNDAY_PREFIX) :].strip()
    if remainder.startswith("."):
        remainder = remainder[1:].strip()
    parts = [p.strip() for p in remainder.split(".") if p.strip()]
    kept = []
    for part in parts:
        lower = part.lower()
        if lower.startswith("service:") or lower.startswith("ibada:"):
            continue
        kept.append(part)
    return ". ".join(kept)


def _sunday_initial(donation):
    notes = donation.notes or ""
    return {
        "contribution_date": donation.contribution_date,
        "service_session": _parse_sunday_session(notes),
        "payment_method": donation.payment_method,
        "amount": donation.amount,
        "notes": _sunday_user_notes(notes),
    }


def build_edit_form(kind, donation, request_post=None, *, language="en", allowed_donor_ids=None):
    initial_map = {
        "tithe": _tithe_initial,
        "malimbuko": _malimbuko_initial,
        "offering": _anonymous_initial,
        "shukrani": _anonymous_initial,
        "sunday_offering": _sunday_initial,
    }
    initial = initial_map[kind](donation)
    form_classes = {
        "tithe": TitheEntryForm,
        "malimbuko": MalimbukoEntryForm,
        "offering": AnonymousContributionEntryForm,
        "shukrani": AnonymousContributionEntryForm,
        "sunday_offering": SundayOfferingEntryForm,
    }
    form_class = form_classes[kind]
    kwargs = {"language": language}
    if kind == "tithe":
        kwargs["allowed_donor_ids"] = allowed_donor_ids
    if kind == "offering":
        kwargs["err_amount_key"] = "offering_err_amount"
    if kind == "shukrani":
        kwargs["err_amount_key"] = "shukrani_err_amount"
    if request_post is not None:
        return form_class(request_post, **kwargs)
    return form_class(initial=initial, **kwargs)


def _update_tithe(donation, cleaned_data, user):
    donor = cleaned_data["donor"]
    zaka_type = cleaned_data.get("zaka_type") or "money"
    notes = (cleaned_data.get("notes") or "").strip()

    donation.donor = donor
    donation.donor_name = donor.full_name
    donation.is_anonymous = False
    donation.donation_type = "tithe"
    donation.contribution_date = cleaned_data["contribution_date"]
    donation.payment_method = cleaned_data["payment_method"]
    donation.processed_by = user
    donation.processed_date = timezone.now()
    donation.status = "completed"

    if zaka_type == "asset":
        asset_desc = (cleaned_data.get("asset_description") or "").strip()
        asset_note = f"Zaka ya mali: {asset_desc}"
        donation.amount = 0
        donation.notes = f"{asset_note}. {notes}".strip() if notes else asset_note
        donation.tithe_gift_type = "asset"
        donation.tithe_asset_description = asset_desc
    else:
        donation.amount = cleaned_data["amount"]
        donation.notes = notes
        donation.tithe_gift_type = "money"
        donation.tithe_asset_description = ""
    donation.save()
    return donation


def _update_malimbuko(donation, cleaned_data, user):
    gift_type = cleaned_data.get("gift_type") or "money"
    miladi = (cleaned_data.get("miladi_source") or "").strip()
    notes = (cleaned_data.get("notes") or "").strip()

    donation.donor = None
    donation.donor_name = ""
    donation.is_anonymous = True
    donation.donation_type = "special"
    donation.contribution_date = cleaned_data["contribution_date"]
    donation.payment_method = cleaned_data["payment_method"]
    donation.processed_by = user
    donation.processed_date = timezone.now()
    donation.status = "completed"

    if gift_type == "asset":
        asset_desc = (cleaned_data.get("asset_description") or "").strip()
        parts = ["Malimbuko (miladi ya kanisa)"]
        if miladi:
            parts.append(f"Miladi: {miladi}")
        parts.append(f"Mavuno: {asset_desc}")
        if notes:
            parts.append(notes)
        donation.amount = 0
        donation.notes = ". ".join(parts)
        donation.tithe_gift_type = "asset"
        donation.tithe_asset_description = asset_desc
    else:
        parts = ["Malimbuko (miladi ya kanisa)"]
        if miladi:
            parts.append(f"Miladi: {miladi}")
        if notes:
            parts.append(notes)
        donation.amount = cleaned_data["amount"]
        donation.notes = ". ".join(parts)
        donation.tithe_gift_type = "money"
        donation.tithe_asset_description = ""
    donation.save()
    return donation


def apply_donation_edit(donation, kind, cleaned_data, user, *, language="en"):
    if kind == "tithe":
        return _update_tithe(donation, cleaned_data, user)
    if kind == "malimbuko":
        return _update_malimbuko(donation, cleaned_data, user)
    if kind == "sunday_offering":
        donation.contribution_date = cleaned_data["contribution_date"]
        donation.payment_method = cleaned_data["payment_method"]
        donation.amount = cleaned_data["amount"]
        donation.notes = _build_sunday_notes(cleaned_data, language=language)
        donation.donation_type = "offering"
        donation.tithe_gift_type = "money"
        donation.tithe_asset_description = ""
        donation.donor = None
        donation.donor_name = ""
        donation.is_anonymous = True
        donation.processed_by = user
        donation.processed_date = timezone.now()
        donation.status = "completed"
        donation.save()
        return donation

    donation.contribution_date = cleaned_data["contribution_date"]
    donation.payment_method = cleaned_data["payment_method"]
    donation.amount = cleaned_data["amount"]
    donation.notes = (cleaned_data.get("notes") or "").strip()
    donation.tithe_gift_type = "money"
    donation.tithe_asset_description = ""
    donation.donor = None
    donation.donor_name = ""
    donation.is_anonymous = True
    donation.processed_by = user
    donation.processed_date = timezone.now()
    donation.status = "completed"
    donation.save()
    return donation


def edit_page_title_key(kind):
    return {
        "tithe": "don_edit_tithe",
        "malimbuko": "don_edit_malimbuko",
        "offering": "don_edit_offering",
        "sunday_offering": "don_edit_sunday",
        "shukrani": "don_edit_shukrani",
    }.get(kind, "don_edit_title")
