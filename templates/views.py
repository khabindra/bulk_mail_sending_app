from rest_framework import generics, status, filters, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from django.db import IntegrityError
from .models import MailType, EmailTemplate, InlineImage
from .serializers import (
    MailTypeSerializer, 
    EmailTemplateSerializer, 
    EmailTemplateDetailSerializer,
    InlineImageSerializer
)
from rest_framework.pagination import PageNumberPagination


# --- PAGINATION ---
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


# --- 1. MAIL TYPE VIEWS ---

class MailTypeListView(generics.ListCreateAPIView):
    """
    List all Mail Types and Create new ones.
    """
    # IMPROVEMENT: Added select_related('template') to optimize the query
    # so we don't hit the database for every single item to get the template.
    queryset = MailType.objects.all().select_related('template').order_by('name')
    serializer_class = MailTypeSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class MailTypeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, Update (PUT/PATCH), or Delete a specific Mail Type.
    """
    # Also good practice to add select_related here in case GET detail is called
    queryset = MailType.objects.all().select_related('template')
    serializer_class = MailTypeSerializer
    permission_classes = [permissions.IsAuthenticated]

    

# --- 2. EMAIL TEMPLATE VIEWS ---
from django.db import transaction, IntegrityError
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.exceptions import ValidationError
import re
from templates.models import InlineImage
from django.http import HttpResponse
from django.utils.html import escape
from django.views.decorators.clickjacking import xframe_options_sameorigin


class EmailTemplateViewSet(ModelViewSet):
    queryset = EmailTemplate.objects.select_related('mail_type')
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['mail_type', 'is_active', 'version']
    search_fields = ['subject', 'description']
    ordering_fields = ['created_at', 'version']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return EmailTemplateDetailSerializer
        return EmailTemplateSerializer

    @transaction.atomic
    def perform_update(self, serializer):
        old = self.get_object()

        # Immutable rule: create new version
        new_instance = EmailTemplate.objects.create(
            mail_type=old.mail_type,
            subject=serializer.validated_data.get('subject', old.subject),
            template_name=serializer.validated_data.get('template_name', old.template_name),
            template_content=serializer.validated_data.get('template_content', old.template_content),
            description=serializer.validated_data.get('description', old.description),
            available_variables=serializer.validated_data.get('available_variables', old.available_variables),
            version=old.version + 1,
            is_active=True,
        )

        old.is_active = False
        old.save(update_fields=['is_active'])


    @action(detail=True, methods=['get'], url_path='preview')
    @xframe_options_sameorigin
    def preview_browser(self, request, pk=None):
        template = self.get_object()

        # Build context from query params
        # context_data = request.GET.dict()
        # 1️⃣ Context (from query params)
        context_data = {
            "company_name": request.GET.get("company_name", "Demo Company"),
            "message": request.GET.get("message", "Congratulations on your success!"),
            "sender_name": request.GET.get("sender_name", "CorpolaTech Team"),
            "sender_email": request.GET.get("sender_email", "no-reply@corpola.com"),
            "congrats_image_cid": "congrats_image_cid",
        }

        # Render template
        html = template.render_template(context_data)


        # Replace CID images for browser preview
        images = InlineImage.objects.filter(
            mail_type=template.mail_type,
            is_active=True
        )

        for img in images:
            if img.image:
                html = html.replace(
                    f"cid:{img.content_id}",
                    img.image.build_url(
                        secure=True,
                        transformation=[
                            {'width': 600, 'crop': 'limit'},
                            {'quality': 'auto'},
                            {'fetch_format': 'png'}
                        ]
                    )
                )

        return HttpResponse(html)

# ----3. INLINE IMAGE VIEWS ---
from django.db import transaction
from rest_framework.exceptions import ValidationError
from rest_framework.viewsets import ModelViewSet
from rest_framework import permissions, filters
from django_filters.rest_framework import DjangoFilterBackend

class InlineImageViewSet(ModelViewSet):
    queryset = InlineImage.objects.select_related('mail_type')
    serializer_class = InlineImageSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['mail_type', 'is_active']
    search_fields = ['content_id', 'name']



    @transaction.atomic

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)
    
    def perform_create(self, serializer):
        instance = serializer.save()
        instance.public_id = instance.image.public_id
        instance.save(update_fields=['public_id'])

    def perform_update(self, serializer):
        old = self.get_object()
        validated_data = serializer.validated_data

        new_image = validated_data.get('image')

        # 🚫 Prevent illegal mutations
        if 'content_id' in validated_data and validated_data['content_id'] != old.content_id:
            raise ValidationError("content_id cannot be changed once created")

        if 'mail_type' in validated_data and validated_data['mail_type'] != old.mail_type:
            raise ValidationError("mail_type cannot be changed once created")

        # 🔁 CASE 1: IMAGE + (OPTIONAL) METADATA → NEW VERSION
        if new_image:
            new_instance = InlineImage.objects.create(
                mail_type=old.mail_type,
                content_id=old.content_id,
                image=new_image,
                name=validated_data.get('name', old.name),
                alt_text=validated_data.get('alt_text', old.alt_text),
                display_order=validated_data.get('display_order', old.display_order),
                is_active=True,
                version=old.version + 1,
            )

            new_instance.public_id = new_instance.image.public_id
            new_instance.save(update_fields=['public_id'])

            # Deactivate old version
            old.is_active = False
            old.save(update_fields=['is_active'])

            return

        # ✏️ CASE 2: METADATA-ONLY UPDATE (NO NEW VERSION)
        metadata_fields = ['name', 'alt_text', 'display_order', 'is_active']
        updated = False

        for field in metadata_fields:
            if field in validated_data:
                setattr(old, field, validated_data[field])
                updated = True

        if not updated:
            raise ValidationError("No valid fields provided for update")

        old.save()


    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=['is_active'])



