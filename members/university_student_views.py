"""Wanafunzi wa chuo — mchungaji huwasajili na kuhifadhi rekodi baada ya kuhitimu."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from donations.print_branding import church_print_context

from .forms import UniversityStudentRecordForm
from .language_utils import LanguageManager, get_translation
from .models import UniversityStudentRecord
from .permissions import can_manage_members
from .university_student_services import sync_university_student_records

VALID_TABS = ("studying", "completed", "paused", "final_year", "all")

_TAB_LABEL_KEYS = {
    "studying": "uni_tab_studying",
    "completed": "uni_tab_completed",
    "paused": "uni_tab_paused",
    "final_year": "uni_tab_final_year",
    "all": "uni_tab_all",
}

_REPORT_TITLE_KEYS = {
    "studying": "uni_report_studying",
    "completed": "uni_report_completed",
    "paused": "uni_report_paused",
    "final_year": "uni_report_final_year",
    "all": "uni_report_all",
}


def _tab_label(tab, lang, current_year=None):
    label = get_translation(_TAB_LABEL_KEYS[tab], lang)
    if tab == "final_year" and current_year:
        return f"{label} ({current_year})"
    return label


def _tab_report_title(tab, current_year, lang):
    key = _REPORT_TITLE_KEYS[tab]
    text = get_translation(key, lang)
    if tab == "final_year":
        return text.format(year=current_year)
    return text


def _require_pastor(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        lang = LanguageManager.get_current_language(request)
        if not can_manage_members(request.user):
            messages.error(request, get_translation("uni_err_pastor_only", lang))
            return redirect("dashboard")
        return view_func(request, *args, **kwargs)

    return wrapper


def _current_year():
    return timezone.now().year


def _search_filter(qs, q):
    if not q:
        return qs
    return qs.filter(
        Q(member__first_name__icontains=q)
        | Q(member__last_name__icontains=q)
        | Q(institution__icontains=q)
        | Q(course__icontains=q)
        | Q(faculty__icontains=q)
    )


def get_university_student_queryset(tab, q="", current_year=None):
    current_year = current_year or _current_year()
    qs = UniversityStudentRecord.objects.select_related(
        "member", "recorded_by"
    ).order_by("member__last_name", "member__first_name", "-year_started")

    if tab == "studying":
        qs = qs.filter(status="studying")
    elif tab == "completed":
        qs = qs.filter(status="completed")
    elif tab == "paused":
        qs = qs.filter(status="paused")
    elif tab == "final_year":
        qs = qs.filter(status="studying", expected_completion_year=current_year)

    return _search_filter(qs, q)


def get_university_student_counts(current_year=None):
    current_year = current_year or _current_year()
    return {
        "studying": UniversityStudentRecord.objects.filter(status="studying").count(),
        "completed": UniversityStudentRecord.objects.filter(status="completed").count(),
        "paused": UniversityStudentRecord.objects.filter(status="paused").count(),
        "final_year": UniversityStudentRecord.objects.filter(
            status="studying",
            expected_completion_year=current_year,
        ).count(),
        "all": UniversityStudentRecord.objects.count(),
    }


@_require_pastor
def university_student_list(request):
    lang = LanguageManager.get_current_language(request)
    sync = sync_university_student_records()
    if sync["backfilled"]:
        messages.success(
            request,
            get_translation("uni_msg_backfilled", lang).format(count=sync["backfilled"]),
        )
    if sync["reverted"]:
        messages.info(
            request,
            get_translation("uni_msg_reverted", lang).format(count=sync["reverted"]),
        )
    if sync["promoted"]:
        messages.info(
            request,
            get_translation("uni_msg_promoted", lang).format(count=sync["promoted"]),
        )

    tab = request.GET.get("tab", "studying")
    if tab not in VALID_TABS:
        tab = "studying"
    q = (request.GET.get("q") or "").strip()
    current_year = _current_year()
    qs = get_university_student_queryset(tab, q, current_year)

    return render(
        request,
        "members/university_student_list.html",
        {
            "records": qs[:200],
            "tab": tab,
            "search_q": q,
            "counts": get_university_student_counts(current_year),
            "current_year": current_year,
        },
    )


@_require_pastor
def university_student_print(request):
    lang = LanguageManager.get_current_language(request)
    tab = request.GET.get("tab", "studying")
    if tab not in VALID_TABS:
        tab = "studying"
    q = (request.GET.get("q") or "").strip()
    current_year = _current_year()
    records = list(get_university_student_queryset(tab, q, current_year))

    return render(
        request,
        "members/university_student_print.html",
        church_print_context(
            records=records,
            tab=tab,
            tab_label=_tab_label(tab, lang, current_year),
            search_q=q,
            counts=get_university_student_counts(current_year),
            current_year=current_year,
            report_title=_tab_report_title(tab, current_year, lang),
            report_date=timezone.now(),
        ),
    )


@_require_pastor
def university_student_create(request):
    lang = LanguageManager.get_current_language(request)
    if request.method == "POST":
        form = UniversityStudentRecordForm(request.POST, language=lang)
        if form.is_valid():
            record = form.save(commit=False)
            record.recorded_by = request.user
            record.save()
            messages.success(
                request,
                get_translation("uni_msg_record_saved", lang).format(
                    name=record.member.full_name
                ),
            )
            return redirect("members:university_student_detail", pk=record.pk)
    else:
        member_id = request.GET.get("member")
        initial = {}
        if member_id:
            try:
                initial["member"] = int(member_id)
            except (TypeError, ValueError):
                pass
        form = UniversityStudentRecordForm(initial=initial, language=lang)

    return render(
        request,
        "members/university_student_form.html",
        {"form": form, "is_edit": False},
    )


@_require_pastor
def university_student_edit(request, pk):
    lang = LanguageManager.get_current_language(request)
    record = get_object_or_404(
        UniversityStudentRecord.objects.select_related("member"),
        pk=pk,
    )
    if request.method == "POST":
        form = UniversityStudentRecordForm(request.POST, instance=record, language=lang)
        if form.is_valid():
            form.save()
            messages.success(request, get_translation("uni_msg_record_updated", lang))
            return redirect("members:university_student_detail", pk=pk)
    else:
        form = UniversityStudentRecordForm(instance=record, language=lang)

    return render(
        request,
        "members/university_student_form.html",
        {"form": form, "record": record, "is_edit": True},
    )


@_require_pastor
def university_student_detail(request, pk):
    sync_university_student_records()
    record = get_object_or_404(
        UniversityStudentRecord.objects.select_related("member", "recorded_by"),
        pk=pk,
    )
    member_history = UniversityStudentRecord.objects.filter(
        member=record.member
    ).order_by("-year_started", "-created_at")

    return render(
        request,
        "members/university_student_detail.html",
        {
            "record": record,
            "member_history": member_history,
        },
    )


@_require_pastor
@require_POST
def university_student_mark_completed(request, pk):
    lang = LanguageManager.get_current_language(request)
    record = get_object_or_404(UniversityStudentRecord, pk=pk)
    year = request.POST.get("year_completed", "").strip()
    if year:
        try:
            record.year_completed = int(year)
        except ValueError:
            messages.error(request, get_translation("uni_err_invalid_year", lang))
            return redirect("members:university_student_detail", pk=pk)
    elif not record.year_completed:
        record.year_completed = timezone.now().year

    record.status = "completed"
    record.save(update_fields=["status", "year_completed", "updated_at"])
    messages.success(
        request,
        get_translation("uni_msg_marked_graduated", lang).format(
            name=record.member.full_name
        ),
    )
    return redirect("members:university_student_detail", pk=pk)
