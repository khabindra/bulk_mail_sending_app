from django.contrib import admin
from .models import MailType, EmailTemplate, InlineImage

@admin.register(MailType)
class MailTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)

@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('mail_type', 'template_name', 'version', 'is_active', 'created_at', 'updated_at')
    list_filter = ('mail_type', 'is_active', 'version')
    search_fields = ('template_name',)
    ordering = ('mail_type__name', '-version')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('mail_type', 'template_name', 'description', 'template_content', 'available_variables', 'version', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

@admin.register(InlineImage)
class InlineImageAdmin(admin.ModelAdmin):
    list_display = ('content_id', 'mail_type', 'name', 'alt_text', 'display_order', 'is_active')
    list_filter = ('mail_type', 'is_active')
    search_fields = ('content_id', 'name', 'alt_text')
    ordering = ('mail_type', 'display_order', 'content_id')
    readonly_fields = ('public_id', 'version')
    fieldsets = (
        (None, {
            'fields': ('mail_type', 'content_id', 'name', 'alt_text', 'display_order', 'is_active', 'image', 'public_id', 'version')
        }),
    )
    # To display image previews in admin (optional)
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs

    # To show image preview (optional)
    def thumbnail_preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" style="max-height:100px; max-width:100px;" />'
        return ""
    thumbnail_preview.allow_tags = True
    thumbnail_preview.short_description = 'Preview'
