from django.db import models
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Q
from .models import Sermon, SermonSeries, SermonCategory, SermonNote, SermonBookmark
from .forms import SermonForm, SermonSeriesForm, SermonCategoryForm, SermonSearchForm
from members.models import ChurchUser

class PastorRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'pastor'

class SermonListView(LoginRequiredMixin, ListView):
    model = Sermon
    template_name = 'sermons/sermon_list.html'
    context_object_name = 'sermons'
    paginate_by = 12

    def get_queryset(self):
        queryset = Sermon.objects.filter(is_published=True)
        
        # Apply search filters
        form = SermonSearchForm(self.request.GET)
        if form.is_valid():
            query = form.cleaned_data.get('query')
            if query:
                queryset = queryset.filter(
                    Q(title__icontains=query) |
                    Q(description__icontains=query) |
                    Q(bible_references__icontains=query)
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
        
        return queryset.order_by('-sermon_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = SermonSearchForm(self.request.GET)
        context['featured_sermons'] = Sermon.objects.filter(
            is_published=True, is_featured=True
        ).order_by('-sermon_date')[:3]
        
        # Add speakers and series for search filters
        context['speakers'] = ChurchUser.objects.filter(
            role__in=['pastor', 'admin', 'elder', 'deacon']
        ).distinct()
        context['series_list'] = SermonSeries.objects.filter(is_active=True)
        
        return context

class SermonDetailView(LoginRequiredMixin, DetailView):
    model = Sermon
    template_name = 'sermons/sermon_detail.html'
    context_object_name = 'sermon'

    def get_object(self):
        sermon = super().get_object()
        # Increment view count
        sermon.increment_view_count()
        return sermon

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sermon = self.get_object()
        user = self.request.user
        
        # Check if user has bookmarked this sermon
        if user.is_authenticated:
            context['user_bookmarks'] = SermonBookmark.objects.filter(
                sermon=sermon, user=user
            ).order_by('timestamp')
            context['user_notes'] = SermonNote.objects.filter(
                sermon=sermon, user=user
            ).order_by('timestamp')
        
        # Get related sermons
        context['related_sermons'] = Sermon.objects.filter(
            is_published=True,
            speaker=sermon.speaker
        ).exclude(id=sermon.id).order_by('-sermon_date')[:5]
        
        return context

class SermonCreateView(PastorRequiredMixin, LoginRequiredMixin, CreateView):
    model = Sermon
    form_class = SermonForm
    template_name = 'sermons/sermon_form.html'
    success_url = reverse_lazy('sermons:sermon_list')

    def form_valid(self, form):
        form.instance.speaker = self.request.user
        form.instance.sermon_date = timezone.now()
        messages.success(self.request, 'Sermon created successfully!')
        return super().form_valid(form)

class SermonUpdateView(PastorRequiredMixin, LoginRequiredMixin, UpdateView):
    model = Sermon
    form_class = SermonForm
    template_name = 'sermons/sermon_form.html'
    success_url = reverse_lazy('sermons:sermon_list')

    def form_valid(self, form):
        messages.success(self.request, 'Sermon updated successfully!')
        return super().form_valid(form)

class SermonDeleteView(PastorRequiredMixin, LoginRequiredMixin, DeleteView):
    model = Sermon
    template_name = 'sermons/sermon_confirm_delete.html'
    success_url = reverse_lazy('sermons:sermon_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Sermon deleted successfully!')
        return super().delete(request, *args, **kwargs)

class SermonSeriesCreateView(PastorRequiredMixin, LoginRequiredMixin, CreateView):
    model = SermonSeries
    form_class = SermonSeriesForm
    template_name = 'sermons/series_form.html'
    success_url = reverse_lazy('sermons:series_list')

    def form_valid(self, form):
        form.instance.speaker = self.request.user
        messages.success(self.request, 'Sermon series created successfully!')
        return super().form_valid(form)

class SermonSeriesListView(LoginRequiredMixin, ListView):
    model = SermonSeries
    template_name = 'sermons/series_list.html'
    context_object_name = 'series_list'
    paginate_by = 12

    def get_queryset(self):
        return SermonSeries.objects.filter(is_active=True).order_by('-start_date')

class SermonSeriesUpdateView(PastorRequiredMixin, LoginRequiredMixin, UpdateView):
    model = SermonSeries
    form_class = SermonSeriesForm
    template_name = 'sermons/series_form.html'
    success_url = reverse_lazy('sermons:series_list')

    def form_valid(self, form):
        messages.success(self.request, 'Sermon series updated successfully!')
        return super().form_valid(form)

class SermonSeriesDeleteView(PastorRequiredMixin, LoginRequiredMixin, DeleteView):
    model = SermonSeries
    template_name = 'sermons/series_confirm_delete.html'
    success_url = reverse_lazy('sermons:series_list')

    def delete(self, *args, **kwargs):
        messages.success(self.request, 'Sermon series deleted successfully!')
        return super().delete(*args, **kwargs)

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
            note=note
        )
        
        return JsonResponse({
            'success': True,
            'bookmark_id': bookmark.id,
            'message': 'Bookmark added successfully!'
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
                'is_private': is_private
            }
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Note saved successfully!'
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
def sermon_dashboard(request):
    """Dashboard for pastors to manage sermons"""
    if not request.user.role in ['pastor', 'admin', 'elder', 'deacon']:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('sermons:sermon_list')
    
    recent_sermons = Sermon.objects.filter(
        speaker=request.user
    ).order_by('-sermon_date')[:5]
    
    total_sermons = Sermon.objects.filter(speaker=request.user).count()
    total_views = Sermon.objects.filter(speaker=request.user).aggregate(
        total=models.Sum('view_count')
    )['total'] or 0
    
    total_downloads = Sermon.objects.filter(speaker=request.user).aggregate(
        total=models.Sum('download_count')
    )['total'] or 0
    
    context = {
        'recent_sermons': recent_sermons,
        'total_sermons': total_sermons,
        'total_views': total_views,
        'total_downloads': total_downloads,
    }
    
    return render(request, 'sermons/sermon_dashboard.html', context)
