import os
import uuid
import logging
from django.conf import settings
from io import BytesIO

logger = logging.getLogger(__name__)

def save_attachments_to_disk(uploaded_files):
    attachments_data = []
    
    # 1. Determine the Path
    media_root = getattr(settings, 'MEDIA_ROOT', None)
    if not media_root:
        raise ValueError("MEDIA_ROOT is not defined in settings.py. Cannot save files.")

    # Ensure the path is absolute
    media_root = os.path.abspath(media_root)
    temp_dir = os.path.join(media_root, 'temp_emails') # It is 'temp_emails' (plural)
    
    # Force create the directory
    os.makedirs(temp_dir, exist_ok=True)

    # ✅ PRINT THIS TO CONSOLE SO YOU CAN FIND IT
    print(f"🔥 SAVING FILES TO: {temp_dir}") 

    for f in uploaded_files:
        try:
            ext = f.name.split('.')[-1]
            filename = f"{uuid.uuid4()}.{ext}"
            temp_path = os.path.join(temp_dir, filename)

            # Write to disk
            with open(temp_path, 'wb+') as destination:
                for chunk in f.chunks():
                    destination.write(chunk)
            
            # Verify existence
            if not os.path.exists(temp_path):
                raise IOError(f"File was not created at {temp_path}")

            attachments_data.append({
                "path": temp_path,
                "filename": f.name,
                "content_type": getattr(f, 'content_type', 'application/octet-stream')
            })
            
            print(f"✅ Successfully saved: {filename} at {temp_path}")
            
        except Exception as e:
            logger.error(f"Failed to save attachment {f.name}: {e}")
            raise  # Crash the request if saving fails

    return attachments_data

def normalize_attachments(uploaded_files):
    # Keep existing
    attachments = []
    for f in uploaded_files:
        f.seek(0)
        attachments.append({
            "filename": f.name,
            "content": f.read(),
            "content_type": f.content_type
        })
    return attachments

def recreate_attachments(attachment_data):
    # Keep existing
    files = []
    for a in attachment_data:
        bio = BytesIO(a["content"])
        bio.name = a["filename"]
        bio.content_type = a["content_type"]
        files.append(bio)
    return files