
import uuid
import os
from django.db import models

class File(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to='uploads/', null=True, blank=True)
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=100)
    size = models.BigIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    user_id = models.CharField(max_length=255)
    file_hash = models.CharField(max_length=64)
    is_reference = models.BooleanField(default=False)
    original_file = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='references')

    @property
    def reference_count(self):
        if self.is_reference:
            return 1
        return self.references.count() + 1
        
    def delete(self, *args, **kwargs):
        if not self.is_reference:
            # If there are references, promote one of them
            refs = list(self.references.all())
            if refs:
                new_original = refs.pop(0)
                new_original.is_reference = False
                new_original.file = self.file
                new_original.original_file = None
                new_original.save()
                for ref in refs:
                    ref.original_file = new_original
                    ref.save()
                self.file = None # Prevent deleting the actual file
            else:
                # No references, actual file can be deleted
                if self.file and os.path.isfile(self.file.path):
                    os.remove(self.file.path)
        super().delete(*args, **kwargs)
