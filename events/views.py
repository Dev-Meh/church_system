from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Event

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
    """Create new event - pastor only"""
    model = Event
    template_name = 'events/event_form.html'
    fields = ['title', 'description', 'event_type', 'start_date', 'end_date', 'location', 'frequency', 'max_participants', 'registration_required', 'registration_deadline', 'is_published', 'image']
    success_url = reverse_lazy('events:event_list')
    
    def dispatch(self, request, *args, **kwargs):
        # Only allow pastors to create events
        if request.user.role not in ['pastor', 'admin']:
            from django.contrib import messages
            messages.error(request, 'Access denied. Pastor privileges required.')
            return redirect('events:event_list')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.organizer = self.request.user
        return super().form_valid(form)

class EventUpdateView(LoginRequiredMixin, UpdateView):
    """Update event - pastor only"""
    model = Event
    template_name = 'events/event_form.html'
    fields = ['title', 'description', 'event_type', 'start_date', 'end_date', 'location', 'frequency', 'max_participants', 'registration_required', 'registration_deadline', 'is_published', 'image']
    
    def dispatch(self, request, *args, **kwargs):
        # Only allow pastors to update events
        if request.user.role not in ['pastor', 'admin']:
            from django.contrib import messages
            messages.error(request, 'Access denied. Pastor privileges required.')
            return redirect('events:event_list')
        return super().dispatch(request, *args, **kwargs)

class EventDeleteView(LoginRequiredMixin, DeleteView):
    """Delete event - pastor only"""
    model = Event
    success_url = reverse_lazy('events:event_list')
    
    def dispatch(self, request, *args, **kwargs):
        # Only allow pastors to delete events
        if request.user.role not in ['pastor', 'admin']:
            from django.contrib import messages
            messages.error(request, 'Access denied. Pastor privileges required.')
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
