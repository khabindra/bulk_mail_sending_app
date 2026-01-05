# working correctly -------------------------------------------
# import os
# import logging
# from django.db import transaction
# from mailings.models import MailLog
# from mailings.services.email_sender import send_email
# from mailings.services.context_builder import build_email_context
# from celery import shared_task

# from client.models import Client
# from templates.models import MailType, EmailTemplate
# from mailings.models import SenderEmail

# logger = logging.getLogger(__name__)


# @shared_task(
#     bind=True,
#     autoretry_for=(Exception,),
#     retry_kwargs={"max_retries": 5},
#     retry_backoff=10,
#     retry_jitter=True,
# )
# def send_bulk_mails(
#     self,
#     client_ids,
#     mail_type_id,
#     email_template_id,
#     sender_id,
#     subject,
#     message,
#     inline_images,
#     attachments, # Now expects list of dicts: [{'path': '/path...', 'filename': 'doc.pdf'}]
#     request_data
# ):
#     clients = Client.objects.filter(id__in=client_ids, is_active=True)
#     mail_type = MailType.objects.get(id=mail_type_id)
#     email_template = EmailTemplate.objects.get(id=email_template_id)
#     sender = SenderEmail.objects.get(id=sender_id)

#     results = []

#     # We read files from disk here to attach them.
#     # We do NOT load all files into RAM at once to prevent memory crash.
#     # We open/close files for each client.
    
#     for client in clients:
#         try:
#             with transaction.atomic():
#                 context = build_email_context(client, sender, message, request_data)

#                 # 🔥 THIS IS REQUIRED (Inline Images Context)
#                 for cid in inline_images.keys():
#                     context[cid] = cid

#                 html = email_template.render_template(context)
                
#                 # Prepare attachments for this specific email
#                 # We construct the dict structure expected by send_email
#                 client_attachments_data = []
#                 for att in attachments:
#                     try:
#                         # Read content from temporary disk path
#                         with open(att['path'], 'rb') as f:
#                             file_content = f.read()
                        
#                         client_attachments_data.append({
#                             "filename": att['filename'],
#                             "content": file_content,
#                             "content_type": att.get('content_type', 'application/octet-stream')
#                         })
#                     except FileNotFoundError:
#                         logger.error(f"Temp file missing during send: {att['path']}")
#                         continue

#                 send_email(
#                     subject=subject,
#                     html_body=html,
#                     from_email=f"{sender.name} <{sender.email}>",
#                     to_email=client.contact_email,
#                     inline_images=inline_images,
#                     attachments=client_attachments_data
#                 )

#                 MailLog.objects.create(
#                     client=client,
#                     mail_type=mail_type,
#                     subject=subject,
#                     template_used=email_template, # Link template instead of body
#                     sender_email=sender.name,
#                     status="SENT",
#                     task_id=self.request.id
#                 )

#                 results.append({"client": client.id, "status": "sent"})

#         except Exception as e:
#             # This runs ONLY if atomic block fails
#             MailLog.objects.create(
#                 client=client,
#                 mail_type=mail_type,
#                 subject=subject,
#                 status="FAILED",
#                 error_message=str(e)
#             )
#             results.append(
#                 {"client": client.id, "status": "failed", "error": str(e)}
#             )

#     # ✅ CLEANUP: Delete all temporary files after the loop finishes
#     for att in attachments:
#         try:
#             os.remove(att['path'])
#             logger.info(f"Deleted temp file: {att['path']}")
#         except OSError as e:
#             logger.error(f"Error deleting temp file {att['path']}: {e}")

#     return results


# new updated============================
import os
import logging
from django.db import transaction
from mailings.models import MailLog
from mailings.services.email_sender import send_email
from mailings.services.context_builder import build_email_context
from celery import shared_task

from client.models import Client
from templates.models import MailType, EmailTemplate
from mailings.models import SenderEmail

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 5},
    retry_backoff=10,
    retry_jitter=True,
)
def send_bulk_mails(
    self,
    client_ids,
    mail_type_id,
    email_template_id,
    sender_id,
    subject,
    message,
    inline_images,
    attachments,
    user_id=None,         # NEW: Track who sent it
    campaign_name=None,    # NEW: Track campaign name
    dynamic_vars=None,   # 🔥 NEW
):
    clients = Client.objects.filter(id__in=client_ids, is_active=True)
    mail_type = MailType.objects.get(id=mail_type_id)
    email_template = EmailTemplate.objects.get(id=email_template_id)
    sender = SenderEmail.objects.get(id=sender_id)

    results = []
    # ✅ READ FILE CONTENT ONCE, BEFORE LOOP
    file_contents = []
    for att in attachments:
        try:
            with open(att['path'], 'rb') as f:
                file_content = f.read()
            file_contents.append({
                "filename": att['filename'],
                "content": file_content,
                "content_type": att.get('content_type', 'application/octet-stream')
            })
            logger.info(f"✅ Read file: {att['filename']} ({len(file_content)} bytes)")
        except FileNotFoundError:
            logger.error(f"❌ File not found: {att['path']}")
            # Skip this attachment for all clients
            continue

    try:
        for client in clients:
            try:
                with transaction.atomic():
                    context = build_email_context(client, sender, message, request_data=dynamic_vars)

                    # 🔥 THIS IS REQUIRED (Inline Images Context)
                    for cid in inline_images.keys():
                        context[cid] = cid

                    html = email_template.render_template(context)
                    
                
                    client_attachments_data=file_contents.copy()

                    # SEND EMAIL
                    send_email(
                        subject=subject,
                        html_body=html,
                        from_email=f"{sender.name} <{sender.email}>",
                        to_email=client.contact_email,
                        inline_images=inline_images,
                        attachments=client_attachments_data
                    )

                    # --- CREATE LOG ENTRY (Updated) ---
                    MailLog.objects.create(
                        client=client,
                        mail_type=mail_type,
                        template_used=email_template, # Link Template
                        sender_email=sender,           # Link Sender
                        created_by_id=user_id,         # Link Admin User
                        task_id=self.request.id,       # Link Celery Task
                        campaign_name=campaign_name or "", # Store campaign
                        subject=subject,
                        status="SENT",
                        error_message=''
                    )

                    results.append({"client": client.id, "status": "sent"})

            except Exception as e:
                # This runs ONLY if atomic block fails
                MailLog.objects.create(
                    client=client,
                    mail_type=mail_type,
                    template_used=email_template,
                    sender_email=sender,
                    created_by_id=user_id,
                    task_id=self.request.id,
                    campaign_name=campaign_name or "",
                    subject=subject,
                    status="FAILED",
                    error_message=str(e)
                )
                results.append(
                    {"client": client.id, "status": "failed", "error": str(e)}
                )
    finally:
        # ✅ CLEANUP: Delete all temporary files after the loop finishes
        deleted_count = 0
        for att in attachments:
            file_path = att['path']
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"✅ Deleted temp file: {file_path}")
                    deleted_count += 1
                else:
                    logger.warning(f"⚠️ Temp file not found (already deleted?): {file_path}")
            except Exception as e:
                logger.error(f"❌ Error deleting {file_path}: {e}")
        
        logger.info(f"🎯 Cleanup: Attempted to delete {len(attachments)} files, successfully deleted {deleted_count}")
    return results