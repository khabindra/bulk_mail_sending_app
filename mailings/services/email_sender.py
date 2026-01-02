from django.core.mail import EmailMultiAlternatives
from email.mime.image import MIMEImage
import logging

logger = logging.getLogger(__name__)


def send_email(
    *,
    subject,
    html_body,
    from_email,
    to_email,
    inline_images=None,
    attachments=None,
    plain_text=None,
):
    """
    Correct Django-compatible email sender.
    Supports:
    - HTML
    - inline images (CID)
    - attachments
    """

    if not plain_text:
        plain_text = "Please view this email in an HTML compatible client."

    if isinstance(to_email, str):
        to_email = [to_email]

    email = EmailMultiAlternatives(
        subject=subject,
        body=plain_text,
        from_email=from_email,
        to=to_email,
    )

    # IMPORTANT: Keep multipart/mixed (default)
    email.mixed_subtype = "mixed"

    # Attach HTML
    email.attach_alternative(html_body, "text/html")

    # ---- INLINE IMAGES ----
    if inline_images:
        for cid, (filename, file_bytes) in inline_images.items():
            try:
                # Determine the subtype based on filename extension
                if filename.lower().endswith('.png'):
                    subtype = 'png'
                elif filename.lower().endswith('.jpg') or filename.lower().endswith('.jpeg'):
                    subtype = 'jpeg'
                else:
                    # fallback or default
                    subtype = 'png'  # or handle differently

                image = MIMEImage(file_bytes, _subtype=subtype)
                # image = MIMEImage(file_bytes)
                image.add_header("Content-ID", f"<{cid}>")
                image.add_header(
                    "Content-Disposition",
                    "inline",
                    filename=filename,
                )
                email.attach(image)
            except Exception as e:
                logger.warning(
                    "Failed to attach inline image %s: %s",
                    cid,
                    e,
                )

    # ---- ATTACHMENTS ----
    if attachments:
        for attachment in attachments:
            try:
                # UploadedFile or file-like
                if hasattr(attachment, "read") and hasattr(attachment, "name"):
                    attachment.seek(0)
                    content = attachment.read()
                    filename = attachment.name
                    content_type = getattr(
                        attachment,
                        "content_type",
                        "application/octet-stream",
                    )

                # dict-based attachment
                elif isinstance(attachment, dict):
                    content = attachment["content"]
                    filename = attachment["filename"]
                    content_type = attachment.get(
                        "content_type",
                        "application/octet-stream",
                    )
                else:
                    logger.warning(
                        "Unsupported attachment type: %s",
                        type(attachment),
                    )
                    continue

                email.attach(
                    filename=filename,
                    content=content,
                    mimetype=content_type,
                )
            except Exception as e:
                logger.warning("Failed to attach file: %s", e)

    email.send(fail_silently=False)
    logger.info("Email sent to %s", to_email)
    return True
