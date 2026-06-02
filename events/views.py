from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET
from .models import Event
from .forms import EventForm
from members.permissions import can_manage_events

class EventListView(ListView):
    """List all events"""
    model = Event
    template_name = 'events/event_list.html'
    context_object_name = 'events'
    
    def get_queryset(self):
        return Event.objects.filter(is_published=True).order_by('-start_date')

class EventDetailView(DetailView):
    """View event details"""
    model = Event
    template_name = 'events/event_detail.html'
    context_object_name = 'event'

class EventCreateView(LoginRequiredMixin, CreateView):
    """Create new event - pastor, secretary (katibu) or accountant (muhasibu)."""
    model = Event
    template_name = 'events/event_form.html'
    form_class = EventForm
    success_url = reverse_lazy('events:event_list')
    
    def dispatch(self, request, *args, **kwargs):
        if not can_manage_events(request.user):
            from django.contrib import messages
            messages.error(request, 'Access denied. Pastor, secretary or accountant privileges required.')
            return redirect('events:event_list')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.organizer = self.request.user
        return super().form_valid(form)

class EventUpdateView(LoginRequiredMixin, UpdateView):
    """Update event - pastor, secretary (katibu) or accountant (muhasibu)."""
    model = Event
    template_name = 'events/event_form.html'
    form_class = EventForm
    
    def dispatch(self, request, *args, **kwargs):
        if not can_manage_events(request.user):
            from django.contrib import messages
            messages.error(request, 'Access denied. Pastor, secretary or accountant privileges required.')
            return redirect('events:event_list')
        return super().dispatch(request, *args, **kwargs)

class EventDeleteView(LoginRequiredMixin, DeleteView):
    """Delete event - pastor, secretary (katibu) or accountant (muhasibu)."""
    model = Event
    success_url = reverse_lazy('events:event_list')
    
    def dispatch(self, request, *args, **kwargs):
        if not can_manage_events(request.user):
            from django.contrib import messages
            messages.error(request, 'Access denied. Pastor, secretary or accountant privileges required.')
            return redirect('events:event_list')
        return super().dispatch(request, *args, **kwargs)

class EventResourceCreateView(LoginRequiredMixin, CreateView):
    """Create event resource"""
    model = Event
    template_name = 'events/resource_form.html'
    fields = ['title', 'description', 'file']
    success_url = reverse_lazy('events:event_list')

@login_required
def register_for_event(request, event_id):
    """Register user for an event"""
    event = get_object_or_404(Event, id=event_id)
    # Add registration logic here
    return render(request, 'events/registration_success.html', {'event': event})

@login_required
def cancel_registration(request, event_id):
    """Cancel event registration"""
    event = get_object_or_404(Event, id=event_id)
    # Add cancellation logic here
    return render(request, 'events/cancellation_success.html', {'event': event})

def event_dashboard(request):
    """Pastor dashboard for events"""
    return render(request, 'events/dashboard.html')


@require_GET
def public_events_api(request):
    """Public JSON feed of published, upcoming/ongoing events for the website.

    No authentication required (public marketing data). The Lovable website
    fetches this to display events & services with their posters.
    """
    now = timezone.now()
    events = (
        Event.objects.filter(is_published=True, end_date__gte=now)
        .order_by('start_date')[:24]
    )

    def poster_url(ev):
        if ev.image and hasattr(ev.image, 'url'):
            try:
                return request.build_absolute_uri(ev.image.url)
            except Exception:
                return None
        return None

    data = [
        {
            'id': ev.id,
            'title': ev.title,
            'description': ev.description,
            'tag': ev.get_event_type_display(),
            'event_type': ev.event_type,
            'start': ev.start_date.isoformat() if ev.start_date else None,
            'end': ev.end_date.isoformat() if ev.end_date else None,
            'location': ev.location,
            'frequency': ev.frequency,
            'is_recurring': ev.is_recurring,
            'poster': poster_url(ev),
        }
        for ev in events
    ]

    response = JsonResponse({'events': data})
    # Allow the static website (different port in dev / same domain in prod) to read it.
    response['Access-Control-Allow-Origin'] = '*'
    response['Cache-Control'] = 'public, max-age=300'
    return response
