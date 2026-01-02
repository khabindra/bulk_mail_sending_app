from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from client.models import Client
from templates.models import MailType, EmailTemplate
from mailings.models import MailLog, SenderEmail
from users.permissions import IsAdminUserRole

from rest_framework import generics, permissions, status, filters
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from .serializers import (
    SenderEmailSerializer, 
    MailLogListSerializer, 
    MailLogDetailSerializer
)

# --- 1. PAGINATION (Production Standard) ---
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100

# --- 2. SENDER EMAIL VIEWS (Standard CRUD) ---
class SenderEmailListCreateView(generics.ListCreateAPIView):
    """
    GET: List all sender emails.
    POST: Create a new sender email.
    """
    queryset = SenderEmail.objects.all().order_by('name')
    serializer_class = SenderEmailSerializer
    permission_classes = [permissions.IsAuthenticated] # Or IsAuthenticatedOrReadOnly
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'email']
    pagination_class = StandardResultsSetPagination

class SenderEmailDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a sender email.
    PUT/PATCH: Update a sender email.
    DELETE: Delete a sender email.
    """
    queryset = SenderEmail.objects.all()
    serializer_class = SenderEmailSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

# --- 3. MAIL LOG VIEWS (Read-Heavy / Create-Only) ---
class MailLogListView(generics.ListCreateAPIView):
    """
    GET: List all mail logs (Paginated, Filtered).
    POST: Log a new email event (used by internal services).
    """
    # Optimization: select_related prevents N+1 queries
    queryset = MailLog.objects.select_related(
        'client', 'mail_type', 'template_used', 'sender_email'
    ).order_by('-sent_at')
    
    permission_classes = [permissions.IsAuthenticated] # Production: Require auth
    pagination_class = StandardResultsSetPagination
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'mail_type', 'campaign_name']
    search_fields = ['subject', 'client__company_name', 'error_message']
    ordering_fields = ['sent_at', 'status']

    def get_serializer_class(self):
        """
        Use lightweight serializer for GET (list) to save bandwidth,
        and detailed serializer for POST (create) to accept full data.
        """
        if self.request.method == 'POST':
            return MailLogDetailSerializer
        return MailLogListSerializer

class MailLogDetailView(generics.RetrieveAPIView):
    """
    GET: Retrieve details of a specific mail log.
    
    Note: We do NOT inherit from UpdateAPIView or DestroyAPIView.
    In production, logs should be immutable (Write-Once, Read-Many).
    """
    queryset = MailLog.objects.select_related('client', 'mail_type', 'sender_email')
    serializer_class = MailLogDetailSerializer
    permission_classes = [permissions.IsAuthenticated]


# # bulk mail sending logic 

# third one: working correctly ==============================================
# from rest_framework.response import Response
# from rest_framework import status
# from .serializers import AdminBulkMailSerializer
# from .utils.parsers import parse_client_ids
# from mailings.services.attachment_service import save_attachments_to_disk
# from .services.inline_image_service import load_inline_images
# from .services.bulk_mail_service import send_bulk_mails

# class AdminBulkMailWithInlineImageAPIView(APIView):
#     permission_classes = [IsAuthenticated, IsAdminUserRole]

#     def post(self, request):

#          # --- DEBUG START ---
#         print("------------------------------------------------")
#         print("DEBUG: Full Request Content-Type:", request.content_type)
#         print("DEBUG: Files received in request.FILES:", request.FILES)
#         print("------------------------------------------------")
#         # --- DEBUG END ---
#         serializer = AdminBulkMailSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         data = serializer.validated_data
#         client_ids = parse_client_ids(data["client_id"])

#         clients = Client.objects.filter(id__in=client_ids, is_active=True)
#         mail_type = MailType.objects.get(id=data["mail_type_id"])
#         email_template = EmailTemplate.objects.get(mail_type=mail_type, is_active=True)
#         sender = SenderEmail.objects.get(id=data["sender_id"])

#         subject = data.get("subject") or email_template.subject
        
#         uploaded_files = request.FILES.getlist("attachments")
        
#         # 1. DEBUG LOG: Check if files even arrived
#         print(f"DEBUG: Received {len(uploaded_files)} files from request.")

#         # 2. Save to disk
#         attachments = []
#         if uploaded_files:
#             try:
#                 # This will now crash if MEDIA_ROOT is wrong or permissions are denied (as intended)
#                 attachments = save_attachments_to_disk(uploaded_files)
#             except Exception as e:
#                 # If saving fails, return a clear error to the user
#                 return Response(
#                     {"error": f"Failed to process attachments on server: {str(e)}"},
#                     status=status.HTTP_500_INTERNAL_SERVER_ERROR
#                 )

#         # 3. VALIDATION: If user uploaded files but we didn't save them (should not happen with code above, but safe to check)
#         if len(uploaded_files) > 0 and len(attachments) == 0:
#              return Response(
#                 {"error": "Files were uploaded but could not be processed."},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )

#         inline_images = load_inline_images(mail_type)

#         results = send_bulk_mails.delay(
#             client_ids=list(clients.values_list("id", flat=True)),
#             mail_type_id=mail_type.id,
#             email_template_id=email_template.id,
#             sender_id=sender.id,
#             subject=subject,
#             message=data.get("message", ""),
#             inline_images=inline_images,
#             attachments=attachments,
#             request_data={}
#         )

#         return Response({
#             "success": True,
#             "task_id": results.id,
#             "message": "Uploads received. Emails are being processed.",
#             "attachments_saved": len(attachments) # Helpful for debugging
#         })


# new update one: ----------------------------------

from rest_framework.response import Response
from rest_framework import status
from .serializers import AdminBulkMailSerializer
from .utils.parsers import parse_client_ids
from mailings.services.attachment_service import save_attachments_to_disk
from .services.inline_image_service import load_inline_images
from .services.bulk_mail_service import send_bulk_mails


class AdminBulkMailWithInlineImageAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserRole]

    def post(self, request):
        serializer = AdminBulkMailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        client_ids = parse_client_ids(data["client_id"])

        clients = Client.objects.filter(id__in=client_ids, is_active=True)
        mail_type = MailType.objects.get(id=data["mail_type_id"])
        email_template = EmailTemplate.objects.get(mail_type=mail_type, is_active=True)
        sender = SenderEmail.objects.get(id=data["sender_id"])

        subject = data.get("subject") or email_template.subject
        
        uploaded_files = request.FILES.getlist("attachments")
        attachments = []
        
        if uploaded_files:
            try:
                attachments = save_attachments_to_disk(uploaded_files)
            except Exception as e:
                return Response(
                    {"error": f"Failed to process attachments: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        inline_images = load_inline_images(mail_type)
        
        # Get User ID from the authenticated request
        current_user_id = request.user.id

        results = send_bulk_mails.delay(
            client_ids=list(clients.values_list("id", flat=True)),
            mail_type_id=mail_type.id,
            email_template_id=email_template.id,
            sender_id=sender.id,
            subject=subject,
            message=data.get("message", ""),
            inline_images=inline_images,
            attachments=attachments,
            # NEW ARGUMENTS:
            user_id=current_user_id,
            campaign_name=data.get('campaign_name', '') # Optional: Add a field in serializer for this
        )

        return Response({
            "success": True,
            "task_id": results.id,
            "message": "Uploads received. Emails are being processed.",
            "attachments_saved": len(attachments)
        })
    

import logging
from django.shortcuts import get_object_or_404
from .serializers import EmailPreviewSerializer, EmailPreviewResponseSerializer
from .services.preview_service import render_preview_html
from .services.context_builder import build_email_context
from templates.models import InlineImage

logger = logging.getLogger(__name__)

class EmailPreviewAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserRole]

    def post(self, request):
        # 1. Validate Input
        serializer = EmailPreviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        
        try:
            # 2. Fetch Objects with 'select_related' for Performance
            # This prevents a second DB query when accessing mail_type.template
            client = get_object_or_404(Client, id=data['client_id'])
            
            mail_type = get_object_or_404(
                MailType.objects.select_related('template'), 
                id=data['mail_type_id']
            )
            
            sender = get_object_or_404(SenderEmail, id=data['sender_id'])
            
            # 3. Build Context
            context = build_email_context(
                client=client, 
                sender=sender, 
                message=data.get('message', ''), 
                request_data={}
            )

            # 4. We need to fetch active inline images for this mail_type
            inline_images = InlineImage.objects.filter(
                mail_type=mail_type, 
                is_active=True
            )
            
            # 5. Inject 'header' instead of just 'header'
            # This ensures preview_service.py can find and replace it with a URL
            for img in inline_images:
                if img.content_id:
                    context[img.content_id] = f'{img.content_id}'

            # 6. Render HTML (CID -> URL conversion)
            try:
                final_html = render_preview_html(mail_type.id, context)
            except Exception as e:
                logger.error(f"Failed to render HTML for client {client.id}: {e}")
                raise Exception("Failed to generate email content.")

            # 7. Return JSON
            response_data = {
                "subject": mail_type.template.subject,
                "recipient_email": client.contact_email,
                "recipient_name": client.company_name,
                "html_content": final_html
            }
            
            response_serializer = EmailPreviewResponseSerializer(response_data)
            
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            # 404 errors are handled by get_object_or_404, so this handles actual server errors
            logger.error(f"Preview API Error: {e}")
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )