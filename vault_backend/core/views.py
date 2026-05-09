import os
import uuid
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from .models import FileMetadata, PhysicalBlob
from .serializers import FileMetadataSerializer
from .tasks import stitch_and_process_upload

class FileViewSet(viewsets.ModelViewSet):
    serializer_class = FileMetadataSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FileMetadata.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    def init_upload(self, request):
        file_hash = request.data.get('file_hash')
        total_size = int(request.data.get('total_size', 0))
        filename = request.data.get('filename')
        
        if not file_hash or not filename or total_size <= 0:
            return Response({"error": "Missing fields"}, status=status.HTTP_400_BAD_REQUEST)

        if request.user.current_storage_usage() + total_size > request.user.storage_quota_bytes:
            return Response({"error": "Quota exceeded"}, status=status.HTTP_403_FORBIDDEN)

        existing_blob = PhysicalBlob.objects.filter(file_hash=file_hash).first()
        if existing_blob:
            _, ext = os.path.splitext(filename)
            metadata = FileMetadata.objects.create(
                user=request.user, blob=existing_blob, original_filename=filename, extension=ext
            )
            return Response({"status": "deduplicated", "id": metadata.id}, status=status.HTTP_201_CREATED)

        upload_id = str(uuid.uuid4())
        return Response({"upload_id": upload_id, "status": "ready"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def upload_chunk(self, request):
        upload_id = request.data.get('upload_id')
        chunk_number = request.data.get('chunk_number')
        chunk_file = request.FILES.get('file')

        if not all([upload_id, chunk_number, chunk_file]):
            return Response({"error": "Missing data"}, status=status.HTTP_400_BAD_REQUEST)

        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_uploads', upload_id)
        os.makedirs(temp_dir, exist_ok=True)
        
        with open(os.path.join(temp_dir, f"{int(chunk_number):05d}.chunk"), 'wb+') as dest:
            for c in chunk_file.chunks():
                dest.write(c)

        return Response({"status": "chunk received"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def complete_upload(self, request):
        upload_id = request.data.get('upload_id')
        file_hash = request.data.get('file_hash')
        filename = request.data.get('filename')

        if not all([upload_id, file_hash, filename]):
            return Response({"error": "Missing data"}, status=status.HTTP_400_BAD_REQUEST)

        stitch_and_process_upload.delay(request.user.id, upload_id, file_hash, filename)
        return Response({"status": "processing"}, status=status.HTTP_202_ACCEPTED)
