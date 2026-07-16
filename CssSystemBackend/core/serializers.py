from rest_framework import serializers
from core.models import ContactUs


class ContactUsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactUs
        fields = ["name", "phone", "message"]
