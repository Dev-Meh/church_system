from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q, Count
from django.utils import timezone
from django.http import JsonResponse
from .models import ChurchUser
from .models_message import Message, MessageRecipient, Announcement
from .message_forms import MessageForm, AnnouncementForm
from .sms_service import sms_service

@login_required(login_url='members:login')
def message_center(request):
    """Main message center for pastors"""
    # Only allow pastors to access message center
    if request.user.role not in ['pastor', 'admin']:
        messages.error(request, 'Access denied. Pastor privileges required.')
        return redirect('dashboard')
    
    # Get statistics
    total_messages = Message.objects.filter(sender=request.user).count()
    total_recipients = MessageRecipient.objects.filter(message__sender=request.user).count()
    total_reads = MessageRecipient.objects.filter(message__sender=request.user, is_read=True).count()
    
    # Get recent messages
    recent_messages = Message.objects.filter(sender=request.user).order_by('-created_at')[:10]
    
    context = {
        'total_messages': total_messages,
        'total_recipients': total_recipients,
        'total_reads': total_reads,
        'recent_messages': recent_messages,
    }
    
    return render(request, 'members/message_center.html', context)

class MessageCreateView(LoginRequiredMixin, CreateView):
    """Create and send messages to members"""
    model = Message
    form_class = MessageForm
    template_name = 'members/message_create.html'
    login_url = '/members/login/'
    
    def dispatch(self, request, *args, **kwargs):
        # Only allow pastors to send messages
        if request.user.role not in ['pastor', 'admin']:
            messages.error(request, 'Access denied. Pastor privileges required.')
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        message = form.save(commit=False)
        message.sender = self.request.user
        message.save()
        
        # Get recipients
        recipients = self.get_recipients(message)
        
        # Create message recipients
        message_recipients = []
        for recipient in recipients:
            mr = MessageRecipient(
                message=message,
                recipient=recipient,
                is_delivered=True,
                delivered_at=timezone.now()
            )
            message_recipients.append(mr)
        
        MessageRecipient.objects.bulk_create(message_recipients)
        
        # Send SMS to all recipients
        sms_text = f"NEW CHURCH MESSAGE: {message.title}\n{message.content[:100]}..."
        for recipient in recipients:
            if recipient.phone_number:
                sms_service.send_sms(recipient.phone_number, sms_text)
        
        messages.success(
            self.request, 
            f'Message sent to {len(recipients)} members successfully (and SMS notifications triggered)!'
        )
        return redirect('members:message_center')
    
    def get_recipients(self, message):
        """Get list of recipients based on message settings"""
        if message.send_to_all:
            return ChurchUser.objects.filter(role='member')
        else:
            target_roles = [role.strip() for role in message.target_roles.split(',')]
            return ChurchUser.objects.filter(role__in=target_roles)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['member_count'] = ChurchUser.objects.filter(role='member').count()
        return context

class MessageListView(LoginRequiredMixin, ListView):
    """List all sent messages with read statistics"""
    model = Message
    template_name = 'members/message_list.html'
    context_object_name = 'messages'
    paginate_by = 20
    login_url = '/members/login/'
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in ['pastor', 'admin']:
            messages.error(request, 'Access denied. Pastor privileges required.')
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        return Message.objects.filter(sender=self.request.user).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class MessageDetailView(LoginRequiredMixin, DetailView):
    """View message details and read statistics"""
    model = Message
    template_name = 'members/message_detail.html'
    context_object_name = 'message'
    login_url = '/members/login/'
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in ['pastor', 'admin']:
            messages.error(request, 'Access denied. Pastor privileges required.')
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        return Message.objects.filter(sender=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        message = context['message']
        
        # Get detailed read statistics
        recipients = MessageRecipient.objects.filter(message=message).select_related('recipient')
        
        # Group by read status
        context['recipients'] = recipients
        context['read_count'] = recipients.filter(is_read=True).count()
        context['unread_count'] = recipients.filter(is_read=False).count()
        context['total_count'] = recipients.count()
        
        return context

@login_required(login_url='members:login')
def member_messages(request):
    """Show messages received by current member"""
    # Get all messages for this member
    message_recipients = MessageRecipient.objects.filter(
        recipient=request.user
    ).select_related('message', 'message__sender').order_by('-message__created_at')
    
    # Mark all as read
    message_recipients.filter(is_read=False).update(
        is_read=True,
        read_at=timezone.now()
    )
    
    context = {
        'message_recipients': message_recipients,
    }
    
    return render(request, 'members/member_messages.html', context)

@login_required(login_url='members:login')
def mark_message_read(request, recipient_id):
    """AJAX endpoint to mark message as read"""
    try:
        recipient = MessageRecipient.objects.get(
            id=recipient_id,
            recipient=request.user
        )
        recipient.mark_as_read()
        return JsonResponse({'status': 'success'})
    except MessageRecipient.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Message not found'})

class AnnouncementCreateView(LoginRequiredMixin, CreateView):
    """Create public announcements"""
    model = Announcement
    form_class = AnnouncementForm
    template_name = 'members/announcement_create.html'
    login_url = '/members/login/'
    success_url = reverse_lazy('members:message_center')
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in ['pastor', 'admin']:
            messages.error(request, 'Access denied. Pastor privileges required.')
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        announcement = form.save(commit=False)
        announcement.author = self.request.user
        announcement.save()
        
        messages.success(self.request, 'Announcement created successfully!')
        return super().form_valid(form)
