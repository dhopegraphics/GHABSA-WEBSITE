from rest_framework import serializers
from timeline.models import Timeline
from utils.cloudinary_utils import get_card_image_url


class TimelineSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Timeline
        fields = "__all__"

    def get_image_url(self, obj):
        # Prioritize URL over upload, apply optimization (fixed method name to match field)
        url = obj.image_url if obj.image_url else (obj.image.url if obj.image else None)
        return get_card_image_url(url, width=400)
