
from rest_framework import serializers
from .models import File

class FileSerializer(serializers.ModelSerializer):
    file = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = [
            'id', 'file', 'original_filename', 'file_type', 
            'size', 'uploaded_at', 'user_id', 'file_hash', 
            'reference_count', 'is_reference', 'original_file'
        ]
        
    def get_file(self, obj):
        if obj.is_reference and obj.original_file and obj.original_file.file:
            return obj.original_file.file.url
        elif obj.file:
            return obj.file.url
        return None
