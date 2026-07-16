from rest_framework import serializers
from django.contrib.auth.models import Permission, Group
from .models import (
    ExecutivePosition, Executive, ExecutiveSocialLinks,
    Committee, Appointee, AppointeeSocialLinks, AppointeeContactDetails,
    AppointeePermission, PermissionAuditLog,
)
from .models import ROLE_CHOICES
from utils.cloudinary_utils import get_avatar_url


class ExecutivePositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExecutivePosition
        fields = [
            "id",
            "name",
            "priority",
            "description",
            "created_at",
            "last_updated",
        ]


class ExecutiveSocialLinksSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExecutiveSocialLinks
        fields = ["id", "executive", "link", "platform"]


#
# class ExecutiveProfileSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ExecutiveProfile
#         fields = ["image"]
#


class ExecutiveSerializer(serializers.ModelSerializer):
    position = ExecutivePositionSerializer()
    executive_name = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    social_media_links = ExecutiveSocialLinksSerializer(many=True)

    class Meta:
        model = Executive
        fields = [
            "executive_name",
            "executive_id",
            "position",
            "phone",
            "image",
            "social_media_links",
            "office_from",
            "office_to",
            "office_year",
            "bio",
            "skills",
            "achievements",
            "is_active",
        ]

    def get_executive_name(self, obj: Executive):
        return f"{obj.user.first_name} {obj.user.last_name}"
    
    def get_phone(self, obj: Executive):
        return str(obj.user.phone) if obj.user.phone else None

    def get_image(self, obj: Executive):
        # Prioritize URL field over file field
        # Skip invalid paths (old Cloudinary paths that weren't migrated)
        if obj.image_url:
            return get_avatar_url(obj.image_url, size=300)
        
        if obj.image and obj.image.name:
            # Skip old Cloudinary paths that don't exist locally
            if 'image/upload/' in obj.image.name:
                return None
            try:
                return get_avatar_url(obj.image.url, size=300)
            except Exception:
                return None
        
        return None


# Committee Serializers
class CommitteeSerializer(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Committee
        fields = [
            "committee_id",
            "name",
            "description",
            "is_active",
            "member_count",
            "created_at",
            "updated_at",
        ]

    def get_member_count(self, obj):
        return obj.members.filter(is_active=True).count()


class AppointeeSocialLinksSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointeeSocialLinks
        fields = ["id", "platform", "link"]


class AppointeeContactDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointeeContactDetails
        fields = ["email", "phone", "office_location", "office_hours"]


class AppointeeSerializer(serializers.ModelSerializer):
    appointee_name = serializers.SerializerMethodField()
    committee_name = serializers.CharField(source="committee.name", read_only=True)
    image = serializers.SerializerMethodField()
    social_media_links = AppointeeSocialLinksSerializer(many=True, read_only=True)
    contact_details = AppointeeContactDetailsSerializer(read_only=True)

    class Meta:
        model = Appointee
        fields = [
            "appointee_id",
            "appointee_name",
            "committee",
            "committee_name",
            "role",
            "portfolio",
            "bio",
            "skills",
            "achievements",
            "image",
            "appointed_from",
            "appointed_to",
            "office_year",
            "is_active",
            "social_media_links",
            "contact_details",
        ]

    def get_appointee_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

    def get_image(self, obj):
        # Prioritize URL field over file field
        # Skip invalid paths (old Cloudinary paths that weren't migrated)
        if obj.image_url:
            return get_avatar_url(obj.image_url, size=300)
        
        if obj.image and obj.image.name:
            # Skip old Cloudinary paths that don't exist locally
            if 'image/upload/' in obj.image.name:
                return None
            try:
                return get_avatar_url(obj.image.url, size=300)
            except Exception:
                return None
        
        return None

    def validate(self, data):
        """
        Ensure that updating an appointee does not create a duplicate active role
        for the same user in the same office_year. This is primarily relevant
        for PATCH operations where `office_year` or `is_active` may change.
        """
        # Only validate for existing instances (updates). Creation via admin
        # will be validated at the model level (clean) and DB constraint.
        instance = getattr(self, 'instance', None)
        if not instance:
            return data

        # Determine the intended office_year and is_active values after update
        office_year = data.get('office_year', instance.office_year)
        is_active = data.get('is_active', instance.is_active)

        # If the resulting state would be active for a specific office_year,
        # ensure no other active appointee exists for the same user and year.
        if is_active and office_year:
            from executives.models import Appointee
            qs = Appointee.objects.filter(user=instance.user, office_year=office_year, is_active=True).exclude(pk=instance.pk)
            if qs.exists():
                raise serializers.ValidationError({
                    'non_field_errors': ['This user already has an active appointee role for the specified office year.']
                })

        # Also ensure singleton roles (head/deputy_head) are unique per committee + office_year
        # Determine resulting role and committee (may be in data or unchanged on instance)
        role = data.get('role', instance.role if instance else None)
        committee = data.get('committee', instance.committee if instance else None)

        if is_active and office_year and role in ('head', 'deputy_head') and committee:
            from executives.models import Appointee
            role_qs = Appointee.objects.filter(
                committee=committee,
                role=role,
                office_year=office_year,
                is_active=True,
            )
            if instance:
                role_qs = role_qs.exclude(pk=instance.pk)
            if role_qs.exists():
                raise serializers.ValidationError({
                    'non_field_errors': [f"There is already an active '{dict(ROLE_CHOICES).get(role, role)}' for this committee in the specified office year."]
                })

        return data


class CommitteeDetailSerializer(serializers.ModelSerializer):
    head = serializers.SerializerMethodField()
    deputy_head = serializers.SerializerMethodField()
    members = serializers.SerializerMethodField()

    class Meta:
        model = Committee
        fields = [
            "committee_id",
            "name",
            "description",
            "is_active",
            "head",
            "deputy_head",
            "members",
            "created_at",
            "updated_at",
        ]

    def get_head(self, obj):
        head = obj.members.filter(role="head", is_active=True).first()
        return AppointeeSerializer(head).data if head else None

    def get_deputy_head(self, obj):
        deputy = obj.members.filter(role="deputy_head", is_active=True).first()
        return AppointeeSerializer(deputy).data if deputy else None

    def get_members(self, obj):
        members = obj.members.filter(role="member", is_active=True).order_by("user__first_name")
        return AppointeeSerializer(members, many=True).data


# Permission Serializers
class PermissionDetailSerializer(serializers.Serializer):
    """Serializer for individual permission details"""
    id = serializers.IntegerField()
    codename = serializers.CharField()
    name = serializers.CharField()
    content_type = serializers.SerializerMethodField()
    
    def get_content_type(self, obj):
        return f"{obj.content_type.app_label}.{obj.content_type.model}"


class AppointeePermissionSerializer(serializers.ModelSerializer):
    appointee_name = serializers.SerializerMethodField()
    granted_by_name = serializers.SerializerMethodField()
    permissions = PermissionDetailSerializer(many=True, read_only=True)
    permission_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=Permission.objects.all(),
        source='permissions'
    )
    # Accept groups to assign to the user when granting permissions
    groups = serializers.SerializerMethodField(read_only=True)
    group_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=Group.objects.all(),
        source='groups'
    )
    
    class Meta:
        model = AppointeePermission
        fields = [
            "permission_id",
            "appointee",
            "appointee_name",
            "permissions",
            "permission_ids",
            "groups",
            "group_ids",
            "granted_by",
            "granted_by_name",
            "granted_at",
            "is_active",
            "expires_at",
            "notes",
        ]

    granted_by = serializers.PrimaryKeyRelatedField(read_only=True)
    
    def get_appointee_name(self, obj):
        return f"{obj.appointee.user.first_name} {obj.appointee.user.last_name}"
    
    def get_granted_by_name(self, obj):
        if obj.granted_by:
            return f"{obj.granted_by.first_name} {obj.granted_by.last_name}"
        return "Unknown"

    def get_groups(self, obj):
        return list(obj.groups.values('id', 'name'))

    def create(self, validated_data):
        # Prevent creating duplicate AppointeePermission for same appointee
        appointee = validated_data.get('appointee')
        if appointee and AppointeePermission.objects.filter(appointee=appointee).exists():
            raise serializers.ValidationError({
                'appointee': ['An AppointeePermission already exists for this appointee.']
            })
        # Pop out m2m data
        groups = validated_data.pop('groups', [])
        permissions = validated_data.pop('permissions', [])

        # Attempt to set granted_by from request context
        request = self.context.get('request') if hasattr(self, 'context') else None
        granted_by = None
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            granted_by = request.user

        # Create the AppointeePermission instance
        instance = AppointeePermission.objects.create(granted_by=granted_by, **validated_data)

        if permissions:
            instance.permissions.set(permissions)
        if groups:
            instance.groups.set(groups)

        # Ensure grants are applied via model hooks
        try:
            instance.apply_grants()
        except Exception:
            pass

        return instance


class PermissionAuditLogSerializer(serializers.ModelSerializer):
    target_user_name = serializers.SerializerMethodField()
    performed_by_name = serializers.SerializerMethodField()
    committee_name = serializers.CharField(source="target_committee.name", read_only=True)
    permissions = PermissionDetailSerializer(many=True, read_only=True)
    
    class Meta:
        model = PermissionAuditLog
        fields = [
            "log_id",
            "action",
            "permissions",
            "target_user",
            "target_user_name",
            "target_committee",
            "committee_name",
            "performed_by",
            "performed_by_name",
            "timestamp",
            "details",
        ]
    
    def get_target_user_name(self, obj):
        return f"{obj.target_user.first_name} {obj.target_user.last_name}"
    
    def get_performed_by_name(self, obj):
        if obj.performed_by:
            return f"{obj.performed_by.first_name} {obj.performed_by.last_name}"
        return "System"
