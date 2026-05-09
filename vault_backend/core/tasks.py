import os
import hashlib
from celery import shared_task
from django.conf import settings
from .models import User, PhysicalBlob, FileMetadata

@shared_task
def stitch_and_process_upload(user_id, upload_id, expected_hash, filename):
    temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_uploads', upload_id)
    if not os.path.exists(temp_dir):
        return "Upload ID not found"

    chunks = sorted(os.listdir(temp_dir))
    final_temp_path = os.path.join(settings.MEDIA_ROOT, 'temp_uploads', f"{upload_id}_final")
    
    sha256 = hashlib.sha256()
    size_bytes = 0

    with open(final_temp_path, 'wb') as final_file:
        for chunk in chunks:
            chunk_path = os.path.join(temp_dir, chunk)
            with open(chunk_path, 'rb') as c_file:
                while chunk_data := c_file.read(8192):
                    final_file.write(chunk_data)
                    sha256.update(chunk_data)
                    size_bytes += len(chunk_data)

    actual_hash = sha256.hexdigest()
    
    if actual_hash != expected_hash:
        os.remove(final_temp_path)
        return "Hash mismatch"

    blob, created = PhysicalBlob.objects.get_or_create(
        file_hash=actual_hash,
        defaults={'size_bytes': size_bytes}
    )

    if created:
        perm_path = os.path.join('blobs', actual_hash)
        full_perm_path = os.path.join(settings.MEDIA_ROOT, perm_path)
        os.makedirs(os.path.dirname(full_perm_path), exist_ok=True)
        os.rename(final_temp_path, full_perm_path)
        blob.file_path = perm_path
        blob.save()
    else:
        os.remove(final_temp_path)

    for chunk in chunks:
        os.remove(os.path.join(temp_dir, chunk))
    os.rmdir(temp_dir)

    user = User.objects.get(id=user_id)
    _, ext = os.path.splitext(filename)
    FileMetadata.objects.create(
        user=user,
        blob=blob,
        original_filename=filename,
        extension=ext
    )
    return "Success"
