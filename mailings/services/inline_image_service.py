# mailings/services/inline_image_service.py

import requests
from templates.models import InlineImage


def load_inline_images(mail_type):
    """
    Load active inline images from Cloudinary and return:
    {
        content_id: (filename, bytes)
    }
    """
    images = {}

    qs = InlineImage.objects.filter(
        mail_type=mail_type,
        is_active=True
    ).order_by('display_order')

    for img in qs:
        if not img.image:
            continue

        # Build ORIGINAL (non-transformed) image URL
        url = img.image.build_url(secure=True)

        response = requests.get(url, timeout=10)
        response.raise_for_status()

        # Guess filename
        filename = f"{img.content_id}.png"

        images[img.content_id] = (filename, response.content)

    return images
