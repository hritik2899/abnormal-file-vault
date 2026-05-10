
import hashlib
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.conf import settings
from .models import File
from .serializers import FileSerializer
from .throttles import UserIdRateThrottle
import django_filters
from django_filters import rest_framework as filters

class FileFilter(filters.FilterSet):
    search = filters.CharFilter(field_name='original_filename', lookup_expr='icontains')
    min_size = filters.NumberFilter(field_name='size', lookup_expr='gte')
    max_size = filters.NumberFilter(field_name='size', lookup_expr='lte')
    start_date = filters.DateTimeFilter(field_name='uploaded_at', lookup_expr='gte')
    end_date = filters.DateTimeFilter(field_name='uploaded_at', lookup_expr='lte')

    class Meta:
        model = File
        fields = ['file_type']

class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer
    throttle_classes = [UserIdRateThrottle]
    filterset_class = FileFilter

    def get_queryset(self):
        if hasattr(self.request, 'user') and hasattr(self.request.user, 'user_id'):
            return File.objects.filter(user_id=self.request.user.user_id)
        return File.objects.none()

    def create(self, request, *args, **kwargs):
        user_id = request.user.user_id
        uploaded_file = request.FILES.get('file')
        
        if not uploaded_file:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        size = uploaded_file.size
        
        actual_storage_used = sum(f.size for f in File.objects.filter(user_id=user_id, is_reference=False))
        
        sha256 = hashlib.sha256()
        for chunk in uploaded_file.chunks():
            sha256.update(chunk)
        file_hash = sha256.hexdigest()

        existing_file = File.objects.filter(file_hash=file_hash, is_reference=False).first()
        
        if not existing_file:
            if actual_storage_used + size > settings.STORAGE_QUOTA_BYTES:
                return Response({"detail": "Storage Quota Exceeded"}, status=429)

        original_filename = uploaded_file.name
        file_type = uploaded_file.content_type

        if existing_file:
            file_instance = File.objects.create(
                original_filename=original_filename,
                file_type=file_type,
                size=size,
                user_id=user_id,
                file_hash=file_hash,
                is_reference=True,
                original_file=existing_file
            )
        else:
            uploaded_file.seek(0)
            file_instance = File.objects.create(
                file=uploaded_file,
                original_filename=original_filename,
                file_type=file_type,
                size=size,
                user_id=user_id,
                file_hash=file_hash,
                is_reference=False
            )

        serializer = self.get_serializer(file_instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def storage_stats(self, request):
        user_id = request.user.user_id
        files = File.objects.filter(user_id=user_id)
        
        original_storage_used = sum(f.size for f in files)
        total_storage_used = sum(f.size for f in files if not f.is_reference)
        
        storage_savings = original_storage_used - total_storage_used
        savings_percentage = (storage_savings / original_storage_used * 100) if original_storage_used > 0 else 0.0

        return Response({
            "user_id": user_id,
            "total_storage_used": total_storage_used,
            "original_storage_used": original_storage_used,
            "storage_savings": storage_savings,
            "savings_percentage": savings_percentage
        })

    @action(detail=False, methods=['get'])
    def file_types(self, request):
        user_id = request.user.user_id
        file_types = File.objects.filter(user_id=user_id).values_list('file_type', flat=True).distinct()
        return Response(list(file_types))
