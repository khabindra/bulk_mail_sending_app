# from django.template import Context
# from django.template.loader import render_to_string
# from templates.models import MailType, InlineImage

# def render_preview_html(mail_type_id, context_data):
#     """
#     Renders the email HTML and replaces CID (email-only) links
#     with public Cloudinary URLs so they render in a browser/API response.
#     """
#     mail_type = MailType.objects.get(id=mail_type_id)
    
#     # 1. Render the HTML using the context (Client Name, Sender Name, etc.)
#     # Your model has a method render_template, let's use that.
#     html_content = mail_type.template.render_template(context_data)

#     # 2. Handle Inline Images
#     # In a real email, images look like <img src="cid:logo_header">.
#     # Browsers can't display "cid:".
#     # We must replace "cid:logo_header" with "https://cloudinary.com/.../logo_header.jpg"
    
#     inline_images = InlineImage.objects.filter(mail_type=mail_type, is_active=True)
    
#     for img in inline_images:
#         # Generate the public URL
#         # Note: Using .image.url relies on your CloudinaryField having that attribute
#         if img.image:
#             public_url = img.image.url 
#             # The cid is defined in your InlineImage model (content_id)
#             cid_signature = f'cid:{img.content_id}'
            
#             # Replace all occurrences of this CID with the Public URL
#             html_content = html_content.replace(cid_signature, public_url)

#     return html_content


from django.template import Context
from django.template.loader import render_to_string
from templates.models import MailType, InlineImage

def render_preview_html(mail_type_id, context_data):
    """
    Renders the email HTML and replaces CID (email-only) links
    with public Cloudinary URLs so they render in a browser/API response.
    """
    # 1. Get Mail Type
    mail_type = MailType.objects.get(id=mail_type_id)
    
    # 2. Render the HTML using the context
    html_content = mail_type.template.render_template(context_data)

    # 3. Handle Inline Images
    # We must MIRROR the logic in inline_image_service.py (filter is_active, order by display_order)
    inline_images = InlineImage.objects.filter(
        mail_type=mail_type, 
        is_active=True
    ).order_by('display_order')
    
    for img in inline_images:
        # Skip if no image file exists
        if not img.image:
            continue

        # Use build_url(secure=True) to match inline_image_service.py logic
        # This ensures we get HTTPS links
        public_url = img.image.build_url(secure=True) 
        
        # The cid is defined in your InlineImage model (content_id)
        # The email sender expects <img src="cid:logo_header">
        cid_signature = f'cid:{img.content_id}'
        
        # Replace cid: with http:// for browser viewing
        html_content = html_content.replace(cid_signature, public_url)

    return html_content