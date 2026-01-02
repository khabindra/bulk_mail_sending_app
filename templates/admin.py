from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.core.exceptions import ValidationError
from .models import MailType, EmailTemplate, InlineImage

class InlineImageInline(admin.TabularInline):
    """Allows managing images directly within the MailType or EmailTemplate screen."""
    model = InlineImage
    extra = 0
    fields = ('content_id', 'image_preview', 'name', 'is_active', 'display_order')
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 50px; height: 50px; object-fit: cover;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Preview'

@admin.register(MailType)
class MailTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'template_count', 'image_count')
    search_fields = ('name',)
    ordering = ('name',)
    inlines = [InlineImageInline] # Manage images here as well

    def template_count(self, obj):
        return 1 if getattr(obj, 'template', None) else 0
    template_count.short_description = 'Templates'

    def image_count(self, obj):
        return obj.inline_images.count()
    image_count.short_description = 'Images'

@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('get_mail_type', 'version', 'status_badge', 'source_type', 'updated_at')
    list_filter = ('mail_type', 'is_active', 'version')
    search_fields = ('subject', 'template_name', 'description')
    ordering = ('mail_type__name', '-version')
    readonly_fields = ('created_at', 'updated_at', 'template_preview_html')

    fieldsets = (
        (None, {
            'fields': ('mail_type', 'subject', 'description', 'template_name', 'template_content')
        }),
        ('Meta & Validation', {
            'fields': ('available_variables', 'version', 'is_active')
        }),
        ('Preview', {
            'fields': ('template_preview_html',),
            'classes': ('collapse',) # Collapsed by default to save space
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def get_mail_type(self, obj):
        return obj.mail_type.name
    get_mail_type.short_description = 'Type'
    get_mail_type.admin_order_field = 'mail_type__name'

    def status_badge(self, obj):
        color = 'green' if obj.is_active else 'grey'
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, "Active" if obj.is_active else "Inactive")
    status_badge.short_description = 'Status'

    def source_type(self, obj):
        if obj.template_content:
            return format_html('<span style="color: blue;">DB Content</span>')
        return format_html('<span style="color: orange;">File ({})</span>', obj.template_name)
    source_type.short_description = 'Source'

    def save_model(self, request, obj, form, change):
        """
        Validate template syntax before saving to ensure production doesn't break.
        """
        try:
            # We try rendering with a dummy context to catch syntax errors early
            obj.render_template({'test': 'validation'})
        except Exception as e:
            raise ValidationError(f"Template Validation Failed: {str(e)}")
        
        super().save_model(request, obj, form, change)

    def template_preview_html(self, obj):
        # Read-only preview of what the HTML looks like
        if obj.template_content:
            return mark_safe(f"<div style='border:1px solid #ccc; padding:10px; max-height:200px; overflow:auto;'>{obj.template_content[:500]}...</div>")
        return "Using File Template"
    template_preview_html.short_description = 'HTML Preview'

@admin.register(InlineImage)
class InlineImageAdmin(admin.ModelAdmin):
    list_display = ('thumbnail', 'content_id', 'mail_type', 'name', 'is_active')
    list_filter = ('mail_type', 'is_active')
    search_fields = ('content_id', 'name')
    ordering = ('mail_type', 'display_order')

    def thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 40px; height: 40px; border-radius: 4px;" />', obj.image.url)
        return "-"
    thumbnail.short_description = 'Image'

