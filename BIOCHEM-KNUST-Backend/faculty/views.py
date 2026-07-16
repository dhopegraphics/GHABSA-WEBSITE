from django.shortcuts import render
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from faculty.models import Staff
from faculty.serializers import StaffSerializer

# Create your views here.


class StaffListView(ListAPIView):
    """
    API endpoint to list all active department staff members
    Can be filtered by position using query parameter: ?position=PROFESSOR
    """
    serializer_class = StaffSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = Staff.objects.filter(is_active=True).prefetch_related('research_areas')
        
        # Filter by position if provided
        position = self.request.query_params.get('position', None)
        if position:
            queryset = queryset.filter(position=position)
        
        return queryset
