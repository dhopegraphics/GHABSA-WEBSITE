from rest_framework import serializers
from .models import SocietyHistory, HistoricalLeader, HistoricalMilestone
from utils.cloudinary_utils import get_avatar_url, get_card_image_url


class HistoricalLeaderSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = HistoricalLeader
        fields = [
            "leader_id",
            "name",
            "position",
            "image",
            "bio",
            "order",
        ]

    def get_image(self, obj):
        # Prioritize image_url over Cloudinary upload, apply optimization
        url = obj.image_url if obj.image_url else (obj.image.url if obj.image else None)
        return get_avatar_url(url, size=200)


class HistoricalMilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistoricalMilestone
        fields = [
            "milestone_id",
            "title",
            "description",
            "date",
            "order",
        ]


class SocietyHistorySerializer(serializers.ModelSerializer):
    leaders = HistoricalLeaderSerializer(many=True, read_only=True)
    milestones = HistoricalMilestoneSerializer(many=True, read_only=True)
    image = serializers.SerializerMethodField()
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = SocietyHistory
        fields = [
            "history_id",
            "title",
            "session_year",
            "category",
            "category_display",
            "description",
            "start_date",
            "end_date",
            "image",
            "leaders",
            "milestones",
            "order",
            "is_published",
            "created_at",
            "updated_at",
        ]

    def get_image(self, obj):
        # Prioritize image_url over Cloudinary upload, apply optimization
        url = obj.image_url if obj.image_url else (obj.image.url if obj.image else None)
        return get_card_image_url(url, width=600)


class SocietyHistoryListSerializer(serializers.ModelSerializer):
    """Lighter serializer for list views without nested data"""
    image = serializers.SerializerMethodField()
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    leaders_count = serializers.SerializerMethodField()
    milestones_count = serializers.SerializerMethodField()

    class Meta:
        model = SocietyHistory
        fields = [
            "history_id",
            "title",
            "session_year",
            "category",
            "category_display",
            "description",
            "start_date",
            "end_date",
            "image",
            "leaders_count",
            "milestones_count",
            "order",
            "is_published",
        ]

    def get_image(self, obj):
        # Prioritize image_url over upload, apply optimization
        url = obj.image_url if obj.image_url else (obj.image.url if obj.image else None)
        return get_card_image_url(url, width=400)

    def get_leaders_count(self, obj):
        return obj.leaders.count()

    def get_milestones_count(self, obj):
        return obj.milestones.count()
