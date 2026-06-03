"""Wanafunzi wa chuo — mchungaji huwasajili na kuhifadhi rekodi baada ya kuhitimu."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import UniversityStudentRecordForm
from .models import ChurchUser, UniversityStudentRecord
from .permissions import can_manage_members
from .university_student_services import promote_due_university_graduates


def _require_pastor(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if not can_manage_members(request.user):
            messages.error(request, "Ni mchungaji/admin tu anaweza kusimamia wanafunzi wa chuo.")
            return redirect("dashboard")
        return view_func(request, *args, **kwargs)

    return wrapper


@_require_pastor
def university_student_list(request):
    promoted = promote_due_university_graduates()
    if promoted:
        messages.info(
            request,
            f"Wanafunzi {promoted} wametambuliwa kiotomatiki kama waliohitimu "
            "(mwaka wa kutarajiwa kuhitimu umefika).",
        )

    tab = request.GET.get("tab", "studying")
    q = (request.GET.get("q") or "").strip()

    qs = UniversityStudentRecord.objects.select_related("member", "recorded_by")
    if tab == "studying":
        qs = qs.filter(status="studying")
    elif tab == "completed":
        qs = qs.filter(status="completed")
    elif tab == "paused":
        qs = qs.filter(status="paused")

    if q:
        qs = qs.filter(
            Q(member__first_name__icontains=q)
            | Q(member__last_name__icontains=q)
            | Q(institution__icontains=q)
            | Q(course__icontains=q)
            | Q(faculty__icontains=q)
        )

    counts = {
        "studying": UniversityStudentRecord.objects.filter(status="studying").count(),
        "completed": UniversityStudentRecord.objects.filter(status="completed").count(),
        "paused": UniversityStudentRecord.objects.filter(status="paused").count(),
        "all": UniversityStudentRecord.objects.count(),
    }

    return render(
        request,
        "members/university_student_list.html",
        {
            "records": qs[:200],
            "tab": tab,
            "search_q": q,
            "counts": counts,
        },
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
