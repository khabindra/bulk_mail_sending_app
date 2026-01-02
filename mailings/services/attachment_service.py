# third one : 

# import os
# import uuid
# import logging
# from django.conf import settings
# from io import BytesIO

# logger = logging.getLogger(__name__)

# def save_attachments_to_disk(uploaded_files):
#     """
#     Production Grade: Saves uploaded files to disk and returns their paths.
#     This version FAILS LOUDLY if saving fails, so you can debug it.
#     """
#     attachments_data = []
    
#     # 1. Debug: Print exactly where we are trying to save
#     media_root = getattr(settings, 'MEDIA_ROOT', None)
#     if not media_root:
#         raise ValueError("MEDIA_ROOT is not defined in settings.py. Cannot save files.")

#     temp_dir = os.path.join(media_root, 'temp_emails')
    
#     # Convert to absolute path to be sure
#     temp_dir = os.path.abspath(temp_dir)

#     logger.info(f"Attempting to save attachments to: {temp_dir}")
    
#     # Ensure temp directory exists
#     os.makedirs(temp_dir, exist_ok=True)

#     for f in uploaded_files:
#         try:
#             # Generate a safe filename to prevent overwriting
#             ext = f.name.split('.')[-1]
#             filename = f"{uuid.uuid4()}.{ext}"
#             temp_path = os.path.join(temp_dir, filename)

#             # Write to disk
#             logger.info(f"Writing file {f.name} to {temp_path}...")
#             with open(temp_path, 'wb+') as destination:
#                 for chunk in f.chunks():
#                     destination.write(chunk)
            
#             # Verify it was written
#             if not os.path.exists(temp_path):
#                 raise IOError(f"File was not created at {temp_path}")

#             attachments_data.append({
#                 "path": temp_path,
#                 "filename": f.name,  # Original filename for the email
#                 "content_type": getattr(f, 'content_type', 'application/octet-stream')
#             })
            
#             logger.info(f"Successfully saved: {temp_path}")
            
#         except Exception as e:
#             # Raising the error is CRITICAL. If this fails, the View should return 500.
#             # Do not swallow the exception.
#             logger.error(f"CRITICAL: Failed to save attachment {f.name}: {e}")
#             raise  # Re-raise the exception so the API fails

#     return attachments_data

# def normalize_attachments(uploaded_files):
#     # ... (Keep existing logic as is) ...
#     attachments = []
#     for f in uploaded_files:
#         f.seek(0)
#         attachments.append({
#             "filename": f.name,
#             "content": f.read(),
#             "content_type": f.content_type
#         })
#     return attachments

# def recreate_attachments(attachment_data):
#     # ... (Keep existing logic as is) ...
#     files = []
#     for a in attachment_data:
#         bio = BytesIO(a["content"])
#         bio.name = a["filename"]
#         bio.content_type = a["content_type"]
#         files.append(bio)
#     return files

# fourth : 
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