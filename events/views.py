from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from django.http import JsonResponse
from .models import Event, EventRegistration, EventResource
from .forms import EventForm, EventRegistrationForm, EventResourceForm
from members.models import ChurchUser

class PastorRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in ['pastor', 'admin', 'elder', 'deacon']

class EventListView(LoginRequiredMixin, ListView):
    model = Event
    template_name = 'events/event_list.html'
    context_object_name = 'events'
    paginate_by = 12

    def get_queryset(self):
        queryset = Event.objects.filter(is_published=True)
        
        # Filter by event type if specified
        event_type = self.request.GET.get('type')
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        # Filter by status (upcoming, past, ongoing)
        status = self.request.GET.get('status')
        if status == 'upcoming':
            queryset = queryset.filter(start_date__gt=timezone.now())
        elif status == 'past':
            queryset = queryset.filter(end_date__lt=timezone.now())
        elif status == 'ongoing':
            now = timezone.now()
            queryset = queryset.filter(start_date__lte=now, end_date__gte=now)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['event_types'] = Event.EVENT_TYPE_CHOICES
        context['current_type'] = self.request.GET.get('type', '')
        context['current_status'] = self.request.GET.get('status', '')
        return context

class EventDetailView(LoginRequiredMixin, DetailView):
    model = Event
    template_name = 'events/event_detail.html'
    context_object_name = 'event'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.get_object()
        user = self.request.user
        
        # Check if user is registered
        if user.is_authenticated:
            context['is_registered'] = EventRegistration.objects.filter(
                event=event, participant=user, status='confirmed'
            ).exists()
            context['registration'] = EventRegistration.objects.filter(
                event=event, participant=user
            ).first()
        
        # Get resources
        context['resources'] = event.resources.all()
        
        # Get registration count
        context['registration_count'] = event.registered_count
        context['now'] = timezone.now()

        return context

class EventCreateView(PastorRequiredMixin, LoginRequiredMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = 'events/event_form.html'
    success_url = reverse_lazy('events:event_list')

    def form_valid(self, form):
        form.instance.organizer = self.request.user
        messages.success(self.request, 'Event created successfully!')
        return super().form_valid(form)

class EventUpdateView(PastorRequiredMixin, LoginRequiredMixin, UpdateView):
    model = Event
    form_class = EventForm
    template_name = 'events/event_form.html'
    success_url = reverse_lazy('events:event_list')

    def form_valid(self, form):
        messages.success(self.request, 'Event updated successfully!')
        return super().form_valid(form)

class EventDeleteView(PastorRequiredMixin, LoginRequiredMixin, DeleteView):
    model = Event
    template_name = 'events/event_confirm_delete.html'
    success_url = reverse_lazy('events:event_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Event deleted successfully!')
        return super().delete(request, *args, **kwargs)

@login_required
def register_for_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    
    if not event.registration_required:
        messages.error(request, 'This event does not require registration.')
        return redirect('events:event_detail', pk=event_id)
    
    if event.registration_deadline and timezone.now() > event.registration_deadline:
        messages.error(request, 'Registration deadline has passed.')
        return redirect('events:event_detail', pk=event_id)
    
    if event.max_participants and event.registered_count >= event.max_participants:
        messages.error(request, 'Event is fully booked.')
        return redirect('events:event_detail', pk=event_id)
    
    registration, created = EventRegistration.objects.get_or_create(
        event=event, participant=request.user,
        defaults={'status': 'confirmed'}
    )
    
    if created:
        messages.success(request, 'You have been registered for this event!')
    else:
        messages.info(request, 'You are already registered for this event.')
    
    return redirect('events:event_detail', pk=event_id)

@login_required
def cancel_registration(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    registration = get_object_or_404(EventRegistration, event=event, participant=request.user)
    
    if registration.status == 'cancelled':
        messages.info(request, 'Registration is already cancelled.')
    else:
        registration.status = 'cancelled'
        registration.save()
        messages.success(request, 'Registration cancelled successfully.')
    
    return redirect('events:event_detail', pk=event_id)

class EventResourceCreateView(PastorRequiredMixin, LoginRequiredMixin, CreateView):
    model = EventResource
    form_class = EventResourceForm
    template_name = 'events/resource_form.html'

    def form_valid(self, form):
        form.instance.event_id = self.kwargs['event_id']
        form.instance.uploaded_by = self.request.user
        messages.success(self.request, 'Resource added successfully!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('events:event_detail', kwargs={'pk': self.kwargs['event_id']})

@login_required
def event_dashboard(request):
    """Dashboard for pastors to manage events"""
    if not request.user.role in ['pastor', 'admin', 'elder', 'deacon']:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('events:event_list')
    
    upcoming_events = Event.objects.filter(
        start_date__gt=timezone.now(),
        organizer=request.user
    ).order_by('start_date')[:5]
    
    past_events = Event.objects.filter(
        end_date__lt=timezone.now(),
        organizer=request.user
    ).order_by('-start_date')[:5]
    
    total_events = Event.objects.filter(organizer=request.user).count()
    total_registrations = EventRegistration.objects.filter(
        event__organizer=request.user,
        status='confirmed'
    ).count()
    
    context = {
        'upcoming_events': upcoming_events,
        'past_events': past_events,
        'total_events': total_events,
        'total_registrations': total_registrations,
    }
    
    return render(request, 'events/event_dashboard.html', context)
