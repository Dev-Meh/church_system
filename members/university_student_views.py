"""Wanafunzi wa chuo — mchungaji huwasajili na kuhifadhi rekodi baada ya kuhitimu."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from donations.print_branding import church_print_context

from .forms import UniversityStudentRecordForm
from .models import UniversityStudentRecord
from .permissions import can_manage_members
from .university_student_services import promote_due_university_graduates

TAB_LABELS = {
    "studying": "Wanaosomea",
    "completed": "Waliohitimu",
    "paused": "Wamesimama",
    "final_year": "Mwaka wa mwisho",
    "all": "Wote",
}


def _require_pastor(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if not can_manage_members(request.user):
            messages.error(request, "Ni mchungaji/admin tu anaweza kusimamia wanafunzi wa chuo.")
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


def _tab_report_title(tab, current_year):
    if tab == "studying":
        return "ORODHA YA WANAFUNZI WANAOSOMEA"
    if tab == "completed":
        return "ORODHA YA WANAFUNZI WALIOHITIMU"
    if tab == "paused":
        return "ORODHA YA WANAFUNZI WAMESIMAMA"
    if tab == "final_year":
        return f"ORODHA YA WANAFUNZI WA MWAKA WA MWISHO ({current_year})"
    return "ORODHA YA WANAFUNZI WA CHUO (WOTE)"


@_require_pastor
def university_student_list(request):
    promoted = promote_due_university_graduates()
    if promoted:
        messages.info(
            request,
            f"Wanafunzi {promoted} wametambuliwa kiotomatiki kama waliohitimu "
            "(msimu wa Novemba wa mwaka wa kutarajiwa kuhitimu umekwisha).",
        )

    tab = request.GET.get("tab", "studying")
    if tab not in TAB_LABELS:
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
    tab = request.GET.get("tab", "studying")
    if tab not in TAB_LABELS:
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
            tab_label=TAB_LABELS[tab],
            search_q=q,
            counts=get_university_student_counts(current_year),
            current_year=current_year,
            report_title=_tab_report_title(tab, current_year),
            report_date=timezone.now(),
        ),
    )


@_require_pastor
def university_student_create(request):
    if request.method == "POST":
        form = UniversityStudentRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.recorded_by = request.user
            record.save()
            messages.success(
                request,
                f"Rekodi ya {record.member.full_name} imehifadhiwa.",
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
        form = UniversityStudentRecordForm(initial=initial)

    return render(
        request,
        "members/university_student_form.html",
        {"form": form, "is_edit": False},
    )


@_require_pastor
def university_student_edit(request, pk):
    record = get_object_or_404(
        UniversityStudentRecord.objects.select_related("member"),
        pk=pk,
    )
    if request.method == "POST":
        form = UniversityStudentRecordForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            messages.success(request, "Rekodi imesasishwa.")
            return redirect("members:university_student_detail", pk=pk)
    else:
        form = UniversityStudentRecordForm(instance=record)

    return render(
        request,
        "members/university_student_form.html",
        {"form": form, "record": record, "is_edit": True},
    )


@_require_pastor
def university_student_detail(request, pk):
    promote_due_university_graduates()
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
    record = get_object_or_404(UniversityStudentRecord, pk=pk)
    year = request.POST.get("year_completed", "").strip()
    if year:
        try:
            record.year_completed = int(year)
        except ValueError:
            messages.error(request, "Mwaka si sahihi.")
            return redirect("members:university_student_detail", pk=pk)
    elif not record.year_completed:
        record.year_completed = timezone.now().year

    record.status = "completed"
    record.save(update_fields=["status", "year_completed", "updated_at"])
    messages.success(
        request,
        f"{record.member.full_name} amewekwa kama aliyehitimu — rekodi inabaki kwenye database.",
    )
    return redirect("members:university_student_detail", pk=pk)
