from django.contrib import admin
from django.utils.html import format_html
from .models import SenderEmail, MailLog

@admin.register(SenderEmail)
class SenderEmailAdmin(admin.ModelAdmin):
    list_display = ('name', 'email')
    search_fields = ('name', 'email')  # Added name to search as well
    ordering = ('name',) # Explicit ordering is good practice


@admin.register(MailLog)
class MailLogAdmin(admin.ModelAdmin):
    list_display = (
        'client', 
        'mail_type', 
        'template_used', 
        'sender_email', 
        'created_by', 
        'task_id', 
        'campaign_name', 
        'status', 
        'subject', 
        'sent_at'
    )
    list_filter = (
        'status',
        'mail_type',
        'client',
        'sender_email',
        'created_by',
        'campaign_name',
        'sent_at',
    )
    search_fields = (
        'client__name',  # Assuming Client model has 'name' field
        'subject',
        'task_id',
        'campaign_name',
        'sender_email__email',  # Assuming SenderEmail model has 'email' field
        'created_by__username', # or 'created_by__email' depending on your User model
    )
    ordering = ('-sent_at',)
    readonly_fields = (
        'sent_at', 
        'task_id',
    )
    # Optional: Add filters for status choices
    list_editable = ('status',)
    # To make it easier to filter by status via dropdown
    list_select_related = (
        'client',
        'mail_type',
        'template_used',
        'sender_email',
        'created_by',
    )