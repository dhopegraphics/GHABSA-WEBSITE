from rest_framework.serializers import ModelSerializer, SerializerMethodField
from advertisements.models import Advertisement
from utils.cloudinary_utils import get_banner_image_url


class AdsSerializer(ModelSerializer):
    flyer = SerializerMethodField()
    
    class Meta:
        model = Advertisement
        exclude = ("is_active",)
    
    def get_flyer(self, obj):
        # Prioritize URL over upload, apply optimization
        url = obj.flyer_url if obj.flyer_url else (obj.flyer.url if obj.flyer else None)
        return get_banner_image_url(url, width=800)
