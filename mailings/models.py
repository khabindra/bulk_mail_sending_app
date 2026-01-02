from django.db import models
from client.models import Client  # Explicit import is better for type hinting
from templates.models import MailType, EmailTemplate

class SenderEmail(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()

    def __str__(self):
        return f"{self.name} <{self.email}>"

    class Meta:
        verbose_name = "Sender Email"
        verbose_name_plural = "Sender Emails"

# working model: ---------------------------------------------------------

# class MailLog(models.Model):
#     # IMPROVEMENT: Explicit imports remove reliance on string app_label references
#     client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='mail_logs')
#     mail_type = models.ForeignKey(MailType, on_delete=models.PROTECT) # PROTECT prevents deletion of active types
#     subject = models.CharField(max_length=255)
#     body = models.TextField()
    
#     # IMPROVEMENT: Use TextChoices for cleaner code
#     class StatusChoices(models.TextChoices):
#         SENT = 'SENT', 'Sent'
#         FAILED = 'FAILED', 'Failed'
#         PENDING = 'PENDING', 'Pending'

#     status = models.CharField(
#         max_length=20,
#         choices=StatusChoices.choices,
#         default=StatusChoices.PENDING
#     )
    
#     error_message = models.TextField(blank=True, null=True)
#     sent_at = models.DateTimeField(auto_now_add=True)
    
#     template_used = models.ForeignKey(
#         EmailTemplate, 
#         on_delete=models.SET_NULL, 
#         null=True, 
#         blank=True,
#         related_name='logs'
#     )
    
#     sender_email = models.ForeignKey(
#         'SenderEmail',
#         on_delete=models.SET_NULL,
#         null=True, 
#         blank=True
#     )
    
#     recipient_count = models.IntegerField(default=1, help_text="Number of recipients (usually 1 for individual logs)")
#     campaign_name = models.CharField(max_length=255, blank=True, db_index=True)
    
#     class Meta:
#         ordering = ['-sent_at']
#         verbose_name = "Mail Log"
#         verbose_name_plural = "Mail Logs"
#         indexes = [
#             models.Index(fields=['client', '-sent_at']),
#             models.Index(fields=['status', '-sent_at']),
#             models.Index(fields=['campaign_name']),
#         ]

#     def __str__(self):
#         return f"To: {self.client} | Subject: {self.subject}"

# new -----------------------------------------updated-----------------
from django.db import models
from client.models import Client
from templates.models import MailType, EmailTemplate

class MailLog(models.Model):
    # 1. RELATIONSHIPS
    client = models.ForeignKey(
        Client, 
        on_delete=models.CASCADE, 
        related_name='mail_logs'
    )
    
    mail_type = models.ForeignKey(
        MailType, 
        on_delete=models.PROTECT
    )
    
    template_used = models.ForeignKey(
        EmailTemplate, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='logs'
    )
    
    sender_email = models.ForeignKey(
        'mailings.SenderEmail',
        on_delete=models.SET_NULL,
        null=True, 
        blank=True
    )

    # 2. UPDATED USER REFERENCE
    # Because your custom user is in the 'users' app, reference it by string 'users.User'
    created_by = models.ForeignKey(
        'users.User', 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_logs'
    )

    # 3. TRACEABILITY
    task_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)

    # 4. METADATA
    campaign_name = models.CharField(max_length=255, blank=True, db_index=True)
    
    # 5. STATUS
    class StatusChoices(models.TextChoices):
        SENT = 'SENT', 'Sent'
        FAILED = 'FAILED', 'Failed'
        PENDING = 'PENDING', 'Pending'
        PROCESSING = 'PROCESSING', 'Processing'

    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
        db_index=True 
    )
    
    subject = models.CharField(max_length=255)
    error_message = models.TextField(blank=True, null=True)
    sent_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-sent_at']
        verbose_name = "Mail Log"
        verbose_name_plural = "Mail Logs"
        indexes = [
            models.Index(fields=['client', '-sent_at']),
            models.Index(fields=['status', '-sent_at']),
            models.Index(fields=['campaign_name']),
            models.Index(fields=['sender_email']),
            models.Index(fields=['created_by']), # Added for "Find all emails sent by User X"
        ]

    def __str__(self):
        return f"To: {self.client.company_name} | Status: {self.status} | {self.subject}"