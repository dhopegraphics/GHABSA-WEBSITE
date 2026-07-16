from news.models import News
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from django.utils import timezone
from datetime import timedelta
from utils.cloudinary_utils import get_card_image_url, get_banner_image_url


class NewsSerializer(ModelSerializer):
    head_image_url = SerializerMethodField()
    back_image_url = SerializerMethodField()
    is_recent = SerializerMethodField()
    days_ago = SerializerMethodField()

    class Meta:
        model = News
        fields = [
            "news_id",
            "title",
            "reported_by",
            "report",
            "minutes_read",
            "head_image_url",
            "back_image_url",
            "views",
            "created_at",
            "last_updted",
            "is_recent",
            "days_ago",
        ]
        # Optionally, you can add read_only_fields for fields you do not want users to update
        read_only_fields = ["news_id", "created_at", "last_updted"]

    def get_head_image_url(self, obj):
        # Prioritize URL over upload, apply optimization
        url = obj.head_image_url if obj.head_image_url else (obj.head_image.url if obj.head_image else None)
        return get_card_image_url(url, width=600)

    def get_back_image_url(self, obj):
        # Prioritize URL over upload, apply optimization
        url = obj.back_image_url if obj.back_image_url else (obj.back_image.url if obj.back_image else None)
        return get_banner_image_url(url, width=1200)

    def get_is_recent(self, obj):
        """
        Check if blog was posted within the last 7 days
        """
        if obj.created_at:
            days_difference = (timezone.now() - obj.created_at).days
            return days_difference <= 7
        return False

    def get_days_ago(self, obj):
        """
        Calculate how many days ago the blog was posted
        """
        if obj.created_at:
            return (timezone.now() - obj.created_at).days
        return None
