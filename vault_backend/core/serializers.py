from rest_framework import serializers
from .models import User, PhysicalBlob, FileMetadata

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'storage_quota_bytes']

class FileMetadataSerializer(serializers.ModelSerializer):
    size_bytes = serializers.IntegerField(source='blob.size_bytes', read_only=True)
    file_hash = serializers.CharField(source='blob.file_hash', read_only=True)

    class Meta:
        model = FileMetadata
        fields = ['id', 'original_filename', 'extension', 'uploaded_at', 'tags', 'size_bytes', 'file_hash']
