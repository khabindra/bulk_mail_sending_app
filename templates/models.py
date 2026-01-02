from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from cloudinary.models import CloudinaryField

class MailType(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name



class EmailTemplate(models.Model):
    mail_type = models.OneToOneField(
        MailType,
        on_delete=models.CASCADE,
        related_name="template"
    )

    subject = models.CharField(max_length=255, blank=True)
    template_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    template_content = models.TextField(
        blank=True,
        null=True,
        help_text="If set, overrides template_name"
    )

    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    available_variables = models.CharField(max_length=255, default="",blank=True)

    class Meta:
        ordering = ['mail_type__name', '-version']
        indexes = [
            models.Index(fields=['mail_type', 'is_active']),
        ]

    def clean(self):
        if not self.template_content and not self.template_name:
            raise ValidationError(
                "Either template_content or template_name must be provided."
            )

    def render_template(self, context_data):
        from django.template import Template, Context
        from django.template.loader import render_to_string

        if self.template_content:
            template = Template(self.template_content)
            return template.render(Context(context_data))

        return render_to_string(self.template_name, context_data)

    @property
    def variables_list(self):
        if not self.available_variables:
            return []
        return [v.strip() for v in self.available_variables.split(',') if v.strip()]



class InlineImage(models.Model):
    mail_type = models.ForeignKey(
        MailType,
        on_delete=models.CASCADE,
        related_name='inline_images'
    )

    content_id = models.CharField(
        max_length=100,
        help_text="CID referenced in the HTML template"
    )

    image = CloudinaryField(
        'image',
        folder='email_inline_images',
        resource_type='image',
        blank=True,
        null=True
    )

    public_id = models.CharField(
        max_length=255,
        unique=True,
        editable=False,
        null=True,blank=True
    )

    version = models.PositiveIntegerField(default=1)

    name = models.CharField(max_length=255, blank=True)
    alt_text = models.CharField(max_length=255, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['mail_type', 'display_order', 'content_id']
        indexes = [
            models.Index(fields=['mail_type', 'content_id', 'is_active']),
        ]

    def __str__(self):
        return f"{self.content_id} v{self.version}"


