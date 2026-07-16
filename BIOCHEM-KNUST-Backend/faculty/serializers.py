from rest_framework import serializers
from faculty.models import Staff, ResearchArea


class ResearchAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResearchArea
        fields = ['id', 'name']


class StaffSerializer(serializers.ModelSerializer):
    research_areas = ResearchAreaSerializer(many=True, read_only=True)
    position_display = serializers.CharField(source='get_position_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = Staff
        fields = [
            'id',
            'name',
            'position',
            'position_display',
            'status',
            'status_display',
            'specialization',
            'bio',
            'publications_count',
            'awards_count',
            'research_areas',
            'email',
            'office_location',
            'image',
            'order'
        ]
    
    def get_image(self, obj):
        # Prioritize URL over upload
        if obj.image_url:
            return obj.image_url
        if obj.image:
            return obj.image.url
        return None
