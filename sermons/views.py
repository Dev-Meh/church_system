from django.db import models
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from django.http import JsonResponse, FileResponse, Http404
from django.db.models import Q

from members.models import ChurchUser
from members.permissions import can_manage_sermons

from .models import Sermon, SermonSeries, SermonNote, SermonBookmark
from .forms import SermonForm, SermonSeriesForm, SermonSearchForm


class SermonManagerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return can_manage_sermons(self.request.user)


class SermonListView(LoginRequiredMixin, ListView):
    model = Sermon
    template_name = 'sermons/sermon_list.html'
    context_object_name = 'sermons'
    paginate_by = 12

    def get_queryset(self):
        if can_manage_sermons(self.request.user):
            queryset = Sermon.objects.all()
        else:
            queryset = Sermon.objects.filter(is_published=True)

        form = SermonSearchForm(self.request.GET)
        if form.is_valid():
            query = form.cleaned_data.get('query')
            if query:
                queryset = queryset.filter(
                    Q(title__icontains=query)
                    | Q(description__icontains=query)
                    | Q(bible_references__icontains=query)
                )

            speaker = form.cleaned_data.get('speaker')
            if speaker:
                queryset = queryset.filter(speaker=speaker)

            series = form.cleaned_data.get('series')
            if series:
                queryset = queryset.filter(series=series)

            category = form.cleaned_data.get('category')
            if category:
                queryset = queryset.filter(categories=category)

            sermon_type = form.cleaned_data.get('sermon_type')
            if sermon_type:
                queryset = queryset.filter(sermon_type=sermon_type)

            date_from = form.cleaned_data.get('date_from')
            if date_from:
                queryset = queryset.filter(sermon_date__gte=date_from)

            date_to = form.cleaned_data.get('date_to')
            if date_to:
                queryset = queryset.filter(sermon_date__lte=date_to)

        series_id = self.request.GET.get('series')
        if series_id:
            try:
                queryset = queryset.filter(series_id=int(series_id))
            except (TypeError, ValueError):
                pass

        return queryset.select_related('speaker', 'series').order_by('-sermon_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = SermonSearchForm(self.request.GET)
        context['featured_sermons'] = Sermon.objects.filter(
            is_published=True, is_featured=True
        ).select_related('speaker').order_by('-sermon_date')[:3]
        context['can_manage_sermons'] = can_manage_sermons(self.request.user)
        return context


class SermonDetailView(LoginRequiredMixin, DetailView):
    model = Sermon
    template_name = 'sermons/sermon_detail.html'
    context_object_name = 'sermon'

    def get_queryset(self):
        qs = Sermon.objects.select_related('speaker', 'series')
        if not can_manage_sermons(self.request.user):
            qs = qs.filter(is_published=True)
        return qs

    def get_object(self, queryset=None):
        sermon = super().get_object(queryset)
        sermon.increment_view_count()
        return sermon

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sermon = context['sermon']
        user = self.request.user

        if user.is_authenticated:
            context['user_bookmarks'] = SermonBookmark.objects.filter(
                sermon=sermon, user=user
            ).order_by('timestamp')
            context['user_notes'] = SermonNote.objects.filter(
                sermon=sermon, user=user
            ).order_by('timestamp')

        context['related_sermons'] = Sermon.objects.filter(
            is_published=True,
            speaker=sermon.speaker,
        ).exclude(id=sermon.id).order_by('-sermon_date')[:5]
        context['can_manage_sermons'] = can_manage_sermons(user)
        return context


class SermonCreateView(SermonManagerRequiredMixin, LoginRequiredMixin, CreateView):
    model = Sermon
    form_class = SermonForm
    template_name = 'sermons/sermon_form.html'
    success_url = reverse_lazy('sermons:sermon_list')

    def form_valid(self, form):
        form.instance.speaker = self.request.user
        if not form.instance.sermon_date:
            form.instance.sermon_date = timezone.now()
        messages.success(self.request, 'Mahubiri yamehifadhiwa.')
        return super().form_valid(form)


class SermonUpdateView(SermonManagerRequiredMixin, LoginRequiredMixin, UpdateView):
    model = Sermon
    form_class = SermonForm
    template_name = 'sermons/sermon_form.html'
    success_url = reverse_lazy('sermons:sermon_list')

    def form_valid(self, form):
        messages.success(self.request, 'Mahubiri yamesasishwa.')
        return super().form_valid(form)


class SermonDeleteView(SermonManagerRequiredMixin, LoginRequiredMixin, DeleteView):
    model = Sermon
    template_name = 'sermons/sermon_confirm_delete.html'
    success_url = reverse_lazy('sermons:sermon_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Mahubiri yamefutwa.')
        return super().delete(request, *args, **kwargs)


class SermonSeriesCreateView(SermonManagerRequiredMixin, LoginRequiredMixin, CreateView):
    model = SermonSeries
    form_class = SermonSeriesForm
    template_name = 'sermons/series_form.html'
    success_url = reverse_lazy('sermons:series_list')

    def form_valid(self, form):
        if not form.instance.speaker_id:
            form.instance.speaker = self.request.user
        messages.success(self.request, 'Mfululizo wa mahubiri umeundwa.')
        return super().form_valid(form)


class SermonSeriesListView(LoginRequiredMixin, ListView):
    model = SermonSeries
    template_name = 'sermons/series_list.html'
    context_object_name = 'series_list'
    paginate_by = 12

    def get_queryset(self):
        return SermonSeries.objects.filter(is_active=True).order_by('-start_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_manage_sermons'] = can_manage_sermons(self.request.user)
        return context


class SermonSeriesUpdateView(SermonManagerRequiredMixin, LoginRequiredMixin, UpdateView):
    model = SermonSeries
    form_class = SermonSeriesForm
    template_name = 'sermons/series_form.html'
    success_url = reverse_lazy('sermons:series_list')

    def form_valid(self, form):
        messages.success(self.request, 'Mfululizo umesasishwa.')
        return super().form_valid(form)


class SermonSeriesDeleteView(SermonManagerRequiredMixin, LoginRequiredMixin, DeleteView):
    model = SermonSeries
    template_name = 'sermons/series_confirm_delete.html'
    success_url = reverse_lazy('sermons:series_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Mfululizo umefutwa.')
        return super().delete(request, *args, **kwargs)


@login_required
def add_bookmark(request, sermon_id):
    sermon = get_object_or_404(Sermon, id=sermon_id)

    if request.method == 'POST':
        timestamp = request.POST.get('timestamp')
        note = request.POST.get('note', '')

        bookmark = SermonBookmark.objects.create(
            sermon=sermon,
            user=request.user,
            timestamp=timestamp if timestamp else None,
            note=note,
        )

        return JsonResponse({
            'success': True,
            'bookmark_id': bookmark.id,
            'message': 'Bookmark added successfully!',
        })

    return JsonResponse({'success': False, 'message': 'Invalid request'})


@login_required
def add_note(request, sermon_id):
    sermon = get_object_or_404(Sermon, id=sermon_id)

    if request.method == 'POST':
        notes_text = request.POST.get('notes')
        timestamp = request.POST.get('timestamp')
        is_private = request.POST.get('is_private', 'off') == 'on'

        SermonNote.objects.update_or_create(
            sermon=sermon,
            user=request.user,
            defaults={
                'notes': notes_text,
                'timestamp': timestamp if timestamp else None,
                'is_private': is_private,
            },
        )

        return JsonResponse({
            'success': True,
            'message': 'Note saved successfully!',
        })

    return JsonResponse({'success': False, 'message': 'Invalid request'})


@login_required
def sermon_download(request, pk, file_type):
    sermon = get_object_or_404(Sermon, pk=pk)
    if not sermon.is_published and not can_manage_sermons(request.user):
        raise Http404

    if file_type == 'audio' and sermon.audio_file:
        sermon.increment_download_count()
        return FileResponse(sermon.audio_file.open('rb'), as_attachment=True, filename=sermon.audio_file.name.split('/')[-1])
    if file_type == 'video' and sermon.video_file:
        sermon.increment_download_count()
        return FileResponse(sermon.video_file.open('rb'), as_attachment=True, filename=sermon.video_file.name.split('/')[-1])
    if file_type == 'slides' and sermon.slides:
        sermon.increment_download_count()
        return FileResponse(sermon.slides.open('rb'), as_attachment=True, filename=sermon.slides.name.split('/')[-1])

    raise Http404


@login_required
def sermon_dashboard(request):
    if not can_manage_sermons(request.user):
        messages.error(request, 'Huna ruhusa ya kusimamia mahubiri.')
        return redirect('sermons:sermon_list')

    speaker_filter = Q(speaker=request.user)
    if request.user.role == 'admin' or getattr(request.user, 'is_superuser', False):
        speaker_filter = Q()

    recent_sermons = Sermon.objects.filter(speaker_filter).order_by('-sermon_date')[:8]
    total_sermons = Sermon.objects.filter(speaker_filter).count()
    published_sermons = Sermon.objects.filter(speaker_filter, is_published=True).count()
    total_views = Sermon.objects.filter(speaker_filter).aggregate(
        total=models.Sum('view_count')
    )['total'] or 0
    total_downloads = Sermon.objects.filter(speaker_filter).aggregate(
        total=models.Sum('download_count')
    )['total'] or 0

    return render(
        request,
        'sermons/sermon_dashboard.html',
        {
            'recent_sermons': recent_sermons,
            'total_sermons': total_sermons,
            'published_sermons': published_sermons,
            'total_views': total_views,
            'total_downloads': total_downloads,
        },
    )
