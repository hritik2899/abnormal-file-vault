import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    storage_quota_bytes = models.BigIntegerField(default=1024 * 1024 * 1024) # 1GB default

    def current_storage_usage(self):
        return sum(fm.blob.size_bytes for fm in self.files.all())

class PhysicalBlob(models.Model):
    file_hash = models.CharField(max_length=64, primary_key=True)
    file_path = models.FileField(upload_to='blobs/')
    size_bytes = models.BigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

class FileMetadata(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='files')
    blob = models.ForeignKey(PhysicalBlob, on_delete=models.PROTECT, related_name='metadata_links')
    original_filename = models.CharField(max_length=255)
    extension = models.CharField(max_length=50)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    tags = models.JSONField(default=dict, blank=True)
