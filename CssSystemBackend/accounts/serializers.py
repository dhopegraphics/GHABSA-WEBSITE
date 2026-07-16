from rest_framework.serializers import (
    ModelSerializer,
    SerializerMethodField,
    Serializer,
    CharField,
    BooleanField,
    UUIDField,
)
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers
from accounts.models import (
    UserSavedPastQueations,
    PastQuestions,
    UserSavedBlogs,
    AcademicSlides,
    UserSavedSlides,
    UserSavedOnlineTutorialTips,
    OnlineTutorialTips,
    News,
)
from accounts.repository import (
    UserSavedPastQuestionsRepo,
    UserSavedBlogsRepo,
    UserSavedSlidesRepo,
    UserSavedOnlineTutorialTipsRepo,
)
from academics.serializers import (
    OnlineTutorialTipsSerializer,
    PastQuestionsSerializer,
    SlidesSerializer,
)
from news.serializers import NewsSerializer
from accounts.models import CustomUser
from django.contrib.auth.models import update_last_login
from typing import Dict, Any
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.utils import timezone
from accounts.models import CustomUser
from phonenumber_field.serializerfields import PhoneNumberField


def get_valid_graduation_year_range():
    """
    Calculate valid graduation year range based on current academic calendar.
    
    After November 30th, students are "promoted" to the next academic year.
    Valid graduation years are only for Years 1-4.
    
    Returns:
        tuple: (min_year, max_year) - inclusive range of valid graduation years
    """
    now = timezone.now()
    current_year = now.year
    current_month = now.month
    current_day = now.day
    
    # Academic year adjustment: After November 30th, use next year as effective year
    adjustment = 1 if (current_month == 12 or (current_month == 11 and current_day > 30)) else 0
    effective_year = current_year + adjustment
    
    # Valid graduation years:
    # - Min: effective_year (Year 4 students graduating this academic year)
    # - Max: effective_year + 3 (Year 1 freshers just starting)
    return (effective_year, effective_year + 3)


def validate_graduation_year(graduation_year):
    """
    Validate that graduation year is within valid range for current academic calendar.
    
    Args:
        graduation_year: The graduation year to validate
        
    Returns:
        int: The validated graduation year
        
    Raises:
        serializers.ValidationError: If graduation year is invalid
    """
    min_year, max_year = get_valid_graduation_year_range()
    
    try:
        grad_year = int(graduation_year)
    except (TypeError, ValueError):
        raise serializers.ValidationError("Graduation year must be a valid number.")
    
    if grad_year < min_year:
        raise serializers.ValidationError(
            f"Invalid graduation year. Year {grad_year} indicates you have already graduated. "
            f"Valid graduation years are {min_year} to {max_year}."
        )
    
    if grad_year > max_year:
        raise serializers.ValidationError(
            f"Invalid graduation year. Year {grad_year} is too far in the future. "
            f"You cannot register before starting Year 1. "
            f"Valid graduation years are {min_year} to {max_year}."
        )
    
    return grad_year


class AccountSignupSerializer(ModelSerializer):

    class Meta:
        model = CustomUser
        fields = (
            "first_name",
            "middle_name",
            "last_name",
            "phone",
            "graduation_year",
            "password",
            "program",
            "student_id",
            "gender",
            "personal_email",
        )
    
    def validate_graduation_year(self, value):
        """Validate graduation year is within valid range"""
        return validate_graduation_year(value)


class AccountProfileSerializer(ModelSerializer):
    program_display = SerializerMethodField()
    group_display = SerializerMethodField()
    year = SerializerMethodField()
    current_semester = SerializerMethodField()
    semester_display = SerializerMethodField()
    semester_status = SerializerMethodField()
    completed_semesters = SerializerMethodField()
    has_completed_program = SerializerMethodField()
    is_fresher_waiting = SerializerMethodField()
    is_graduated = SerializerMethodField()
    gender_display = SerializerMethodField()
    current_academic_year = SerializerMethodField()
    academic_status = SerializerMethodField()

    class Meta:
        model = CustomUser
        exclude = (
            "is_staff",
            "password",
            "groups",
            "is_superuser",
            "user_permissions",
        )
        # Note: current_semester SerializerMethodField overrides the model field
    
    def get_program_display(self, obj):
        return obj.get_program_display_name()
    
    def get_group_display(self, obj):
        return obj.get_group_display_name()
    
    def get_year(self, obj):
        """Return the current year (1-4). Note: KNUST uses Year not Level."""
        return obj.get_year()
    
    def get_current_semester(self, obj):
        """Return the auto-calculated current semester"""
        return obj.calculate_current_semester()
    
    def get_semester_display(self, obj):
        """Return human-readable semester status"""
        return obj.get_semester_display()
    
    def get_semester_status(self, obj):
        """Return semester status: 'active', 'not_started', or 'completed'"""
        try:
            return obj.get_academic_status()['semester_status']
        except Exception:
            return 'unknown'
    
    def get_completed_semesters(self, obj):
        """Return the number of completed semesters"""
        return obj.get_completed_semesters()
    
    def get_has_completed_program(self, obj):
        """Return whether student has completed all 8 semesters"""
        return obj.has_completed_program()
    
    def get_is_fresher_waiting(self, obj):
        """Return whether this is a fresher waiting for first semester"""
        try:
            return obj.get_academic_status()['is_fresher_waiting']
        except Exception:
            return False
    
    def get_is_graduated(self, obj):
        """Return whether student has graduated"""
        try:
            return obj.get_academic_status()['is_graduated']
        except Exception:
            return False
    
    def get_gender_display(self, obj):
        """Return the full gender name"""
        return obj.get_gender_display_name()
    
    def get_current_academic_year(self, obj):
        """Return the current academic year"""
        return obj.get_current_academic_year()
    
    def get_academic_status(self, obj):
        """Return the complete academic status object"""
        try:
            return obj.get_academic_status()
        except Exception:
            return None


class AccountUpdateSerializer(ModelSerializer):
    phone = PhoneNumberField()
    phone_confirm = BooleanField(read_only=True)
    id = UUIDField(read_only=True)
    current_semester = SerializerMethodField(read_only=True)

    class Meta:
        model = CustomUser
        exclude = (
            "is_staff",
            "password",
            "groups",
            "is_active",
            "last_login",
            "date_joined",
            "is_superuser",
            "user_permissions",
        )
    
    def get_current_semester(self, obj):
        """Return the current semester (read-only)"""
        return obj.calculate_current_semester()
    
    def validate_student_id(self, value):
        """
        Validate student_id uniqueness and write-once behavior.
        Once set, student_id cannot be changed.
        """
        # Allow empty/None values
        if not value or value.strip() == '':
            return None
        
        # Clean the value
        value = value.strip()
        
        # If user already has a student_id, don't allow changing it
        if self.instance and self.instance.student_id:
            if value != self.instance.student_id:
                raise serializers.ValidationError(
                    "Student ID cannot be changed once set."
                )
        
        # Check if student_id already exists for a different user
        user_id = self.instance.id if self.instance else None
        if CustomUser.objects.filter(student_id=value).exclude(id=user_id).exists():
            raise serializers.ValidationError(
                "A user with this Student ID already exists."
            )
        
        return value
    
    def validate_student_email(self, value):
        """
        Validate that student email ends with @st.knust.edu.gh
        Once set, student_email cannot be changed.
        """
        # Allow empty/None values
        if not value or value.strip() == '':
            return None
        
        # Clean the value
        value = value.strip().lower()
        
        # If user already has a student_email, don't allow changing it
        if self.instance and self.instance.student_email:
            if value != self.instance.student_email:
                raise serializers.ValidationError(
                    "Student email cannot be changed once set."
                )
        
        if not value.endswith('@st.knust.edu.gh'):
            raise serializers.ValidationError(
                "Student email must end with @st.knust.edu.gh"
            )
        return value
    
    def validate_phone(self, value):
        """
        Once phone is verified, it cannot be changed.
        """
        if not value:
            return value
        
        # If user's phone is verified, don't allow changing it
        if self.instance and self.instance.phone_confirm:
            if str(value) != str(self.instance.phone):
                raise serializers.ValidationError(
                    "Phone number cannot be changed once verified."
                )
        
        return value
    
    def validate_gender(self, value):
        """
        Once gender is set, it cannot be changed.
        """
        # Allow empty/None values initially
        if not value or value.strip() == '':
            return None
        
        # If user already has a gender set, don't allow changing it
        if self.instance and self.instance.gender:
            if value != self.instance.gender:
                raise serializers.ValidationError(
                    "Gender cannot be changed once set."
                )
        
        return value
    
    def validate_program(self, value):
        """
        Once program is set, it cannot be changed.
        """
        # Allow empty/None values initially
        if not value or value.strip() == '':
            return None
        
        # If user already has a program set, don't allow changing it
        if self.instance and self.instance.program:
            if value != self.instance.program:
                raise serializers.ValidationError(
                    "Program cannot be changed once set."
                )
        
        return value
    
    def validate_group(self, value):
        """
        Once group is set, it cannot be changed.
        """
        # Allow empty/None values initially
        if not value or value.strip() == '':
            return None
        
        # If user already has a group set, don't allow changing it
        if self.instance and self.instance.group:
            if value != self.instance.group:
                raise serializers.ValidationError(
                    "Class group cannot be changed once set."
                )
        
        return value
    
    def validate_index_number(self, value):
        """
        Validate index_number uniqueness and write-once behavior.
        Once set, index_number cannot be changed.
        
        Note: index_number is not optional - it's either set or unavailable.
        If unavailable (None/empty), it can be set later. Once set, it's permanent.
        """
        # Allow empty/None values (unavailable but not optional conceptually)
        if not value or value.strip() == '':
            return None
        
        # Clean the value
        value = value.strip()
        
        # If user already has an index_number, don't allow changing it
        if self.instance and self.instance.index_number:
            if value != self.instance.index_number:
                raise serializers.ValidationError(
                    "Index number cannot be changed once set."
                )
        
        # Check if index_number already exists for a different user
        user_id = self.instance.id if self.instance else None
        if CustomUser.objects.filter(index_number=value).exclude(id=user_id).exists():
            raise serializers.ValidationError(
                "A user with this index number already exists."
            )
        
        return value
    
    def validate(self, attrs):
        """Additional validation for the serializer"""
        # Validate graduation_year if provided
        if 'graduation_year' in attrs and attrs['graduation_year']:
            attrs['graduation_year'] = validate_graduation_year(attrs['graduation_year'])
        
        # Validate gender choices if provided
        if 'gender' in attrs and attrs['gender']:
            valid_genders = ['M', 'F', 'O']
            if attrs['gender'] not in valid_genders:
                raise serializers.ValidationError({
                    'gender': 'Invalid gender choice. Must be M, F, or O.'
                })
        
        # Validate group choices if provided
        if 'group' in attrs and attrs['group']:
            valid_groups = ['G1', 'G2']
            if attrs['group'] not in valid_groups:
                raise serializers.ValidationError({
                    'group': 'Invalid group choice. Must be G1 or G2.'
                })
        
        # Clean and validate student_id
        if 'student_id' in attrs:
            if attrs['student_id']:
                attrs['student_id'] = attrs['student_id'].strip()
                if not attrs['student_id']:
                    attrs['student_id'] = None
        
        # Clean and validate personal_email
        if 'personal_email' in attrs:
            if attrs['personal_email']:
                attrs['personal_email'] = attrs['personal_email'].strip().lower()
                if not attrs['personal_email']:
                    attrs['personal_email'] = None
        
        # Clean and validate student_email
        if 'student_email' in attrs:
            if attrs['student_email']:
                attrs['student_email'] = attrs['student_email'].strip().lower()
                if not attrs['student_email']:
                    attrs['student_email'] = None
        
        return super().validate(attrs)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs: Dict[str, Any]) -> Dict[str, str]:
        data = super().validate(attrs)

        refresh = self.get_token(self.user)

        data["refresh"] = str(refresh)
        data["access"] = str(refresh.access_token)
        
        # Track device login (optimized - non-blocking where possible)
        request = self.context.get('request')
        device_id = None
        is_new_device = False
        
        if request:
            try:
                from accounts.device_utils import get_device_info_from_request
                from accounts.device_repository import UserDeviceRepository, DeviceLoginHistoryRepository
                import threading
                
                # Get device information from request (fast)
                device_info = get_device_info_from_request(request)
                
                # Create or update device record
                device = UserDeviceRepository.create_or_update_device(
                    user=self.user,
                    device_info=device_info,
                    refresh_token_jti=str(refresh['jti'])
                )
                
                device_id = str(device.id)
                is_new_device = device.first_login == device.last_active
                
                # Record login history in background thread (non-blocking)
                def record_history():
                    try:
                        DeviceLoginHistoryRepository.record_login(
                            device=device,
                            user=self.user,
                            ip_address=device_info.get('ip_address'),
                            location=device.get_location_display(),
                            success=True
                        )
                    except Exception as e:
                        pass  # Silently fail, already logged
                
                thread = threading.Thread(target=record_history, daemon=True)
                thread.start()
                
            except Exception as e:
                # Don't fail login if device tracking fails
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Device tracking error: {e}", exc_info=True)
        
        # Add device info to response
        if device_id:
            data["device_id"] = device_id
            data["is_new_device"] = is_new_device
            
        # Get academic status for all calculated fields
        academic_status = self.user.get_academic_status()
        
        data["user"] = {
            "id": self.user.id,
            "graduation_year": self.user.graduation_year,
            "year": academic_status['year'],
            "phone": str(self.user.phone),
            "first_name": self.user.first_name,
            "middle_name": self.user.middle_name,
            "last_name": self.user.last_name,
            "phone_confirm": self.user.phone_confirm,
            "program": self.user.program,
            "program_display": self.user.get_program_display_name(),
            # New student information fields
            "student_id": self.user.student_id,
            "index_number": self.user.index_number,
            "personal_email": self.user.personal_email,
            "student_email": self.user.student_email,
            "gender": self.user.gender,
            "gender_display": self.user.get_gender_display_name(),
            "group": self.user.group,
            "group_display": self.user.get_group_display_name(),
            # Academic status fields (all calculated)
            "current_semester": academic_status['semester'],
            "semester_display": academic_status['semester_display'],
            "semester_status": academic_status['semester_status'],
            "completed_semesters": academic_status['completed_semesters'],
            "has_completed_program": academic_status['completed_semesters'] >= 8,
            "is_graduated": academic_status['is_graduated'],
            "academic_status": academic_status,
            # Staff permission flag (for admin features like merchandise validation)
            "is_staff": self.user.is_staff,
        }

        if api_settings.UPDATE_LAST_LOGIN:
            update_last_login(None, self.user)

        return data


user_saved_blogs_repo = UserSavedBlogsRepo


class RequestPhoneVerificationSerializer(Serializer):
    phone = PhoneNumberField()


class PhoneVericationSerializer(Serializer):
    phone = PhoneNumberField()
    code = CharField()


class RequestForgotPasswordSerializer(Serializer):
    phone = PhoneNumberField()
    send_via = CharField(max_length=10, required=False, default='sms')
    
    def validate_send_via(self, value):
        if value not in ['sms', 'email']:
            raise serializers.ValidationError("send_via must be 'sms' or 'email'")
        return value


class ResetPasswordSerializer(Serializer):
    phone = PhoneNumberField()
    code = CharField(max_length=5)
    new_password = CharField(max_length=255)


class ChangePasswordSerializer(Serializer):
    new_password = CharField(max_length=255)


class UserSavedBlogsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSavedBlogs
        fields = ["id", "user", "blogs", "created_at", "last_updated"]
        read_only_fields = ["id", "user", "created_at", "last_updated"]

    def create(self, validated_data: dict):
        user = self.context.get("request").user
        validated_data.update({"user": user})
        blogs_data = validated_data.pop("blogs", [])

        user_saved_blogs = user_saved_blogs_repo.get_user_saved_blogs(user=user)

        if user_saved_blogs:
            for blog in blogs_data:
                user_saved_blogs.blogs.add(blog)
            return user_saved_blogs

        user_saved_blog = user_saved_blogs_repo.create_user_saved_blogs(
            **validated_data
        )
        user_saved_blog.blogs.set(blogs_data)
        return user_saved_blog


class GetUserSavedBlogsSerializer(serializers.ModelSerializer):
    blogs = NewsSerializer(many=True)

    class Meta:
        model = UserSavedBlogs
        fields = ["id", "user", "blogs", "created_at", "last_updated"]
        # read_only_fields = ["id", "user", "blogs", "created_at", "last_updated"]


user_saved_slides_repo = UserSavedSlidesRepo


class UserSavedSlidesSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSavedSlides
        fields = ["id", "user", "slides", "created_at", "last_updated"]
        read_only_fields = ["id", "user", "created_at", "last_updated"]

    def create(self, validated_data: dict):
        user = self.context.get("request").user
        validated_data.update({"user": user})
        slides_data = validated_data.pop("slides", [])

        user_saved_slides = user_saved_slides_repo.get_user_saved_slides(user=user)

        if user_saved_slides:
            for slide in slides_data:
                user_saved_slides.slides.add(slide)
            return user_saved_slides

        user_saved_slide = user_saved_slides_repo.create_user_saved_slides(
            **validated_data
        )
        user_saved_slide.slides.set(slides_data)
        return user_saved_slide


class GetUserSavedSlidesSerializer(serializers.ModelSerializer):
    slides = SlidesSerializer(many=True)

    class Meta:
        model = UserSavedSlides
        fields = ["id", "user", "slides", "created_at", "last_updated"]
        read_only_fields = ["id", "user", "slides", "created_at", "last_updated"]


user_saved_tutorial_tips_repo = UserSavedOnlineTutorialTipsRepo


class UserSavedOnlineTutorialTipsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSavedOnlineTutorialTips
        fields = ["id", "user", "online_tips", "created_at", "last_updated"]
        read_only_fields = ["id", "user", "created_at", "last_updated"]

    def create(self, validated_data: dict):
        user = self.context.get("request").user
        validated_data.update({"user": user})
        online_tips_data = validated_data.pop("online_tips", [])

        user_saved_tutorial_tips = (
            user_saved_tutorial_tips_repo.get_user_saved_tutorial_tips(user=user)
        )

        if user_saved_tutorial_tips:
            for online_tip in online_tips_data:
                user_saved_tutorial_tips.online_tips.add(online_tip)
            return user_saved_tutorial_tips

        user_saved_tutorial_tip = (
            user_saved_tutorial_tips_repo.create_user_saved_tutorial_tips(
                **validated_data
            )
        )
        user_saved_tutorial_tip.online_tips.set(online_tips_data)
        return user_saved_tutorial_tip


class GetUserSavedOnlineTutorialTipsSerializer(serializers.ModelSerializer):
    online_tips = OnlineTutorialTipsSerializer(many=True)

    class Meta:
        model = UserSavedOnlineTutorialTips
        fields = ["id", "user", "online_tips", "created_at", "last_updated"]
        read_only_fields = ["id", "user", "online_tips", "created_at", "last_updated"]


user_saved_past_questions_repo = UserSavedPastQuestionsRepo


class UserSavedPastQuestionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSavedPastQueations
        fields = ["id", "user", "past_questions", "created_at", "last_updated"]
        read_only_fields = ["id", "user", "created_at", "last_updated"]

    def create(self, validated_data: dict):
        user = self.context.get("request").user
        validated_data.update({"user": user})
        past_questions_data = validated_data.pop("past_questions", [])

        user_saved_past_questions = (
            user_saved_past_questions_repo.get_user_saved_past_questions(user=user)
        )

        if user_saved_past_questions:
            for past_question in past_questions_data:
                user_saved_past_questions.past_questions.add(past_question)
            return user_saved_past_questions

        user_saved_past_question = (
            user_saved_past_questions_repo.create_user_saved_past_questions(
                **validated_data
            )
        )
        user_saved_past_question.past_questions.set(past_questions_data)
        return user_saved_past_question


class GetUserSavedPastQuestionsSerializer(serializers.ModelSerializer):
    past_questions = PastQuestionsSerializer(many=True)

    class Meta:
        model = UserSavedPastQueations
        fields = ["id", "user", "past_questions", "created_at", "last_updated"]
        read_only_fields = [
            "id",
            "user",
            "past_questions",
            "created_at",
            "last_updated",
        ]


# =====================
# EMAIL VERIFICATION SERIALIZERS
# =====================

class RequestEmailVerificationSerializer(Serializer):
    """Serializer for requesting verification code via email"""
    phone = PhoneNumberField(required=True, help_text="Phone number to verify")
    email = serializers.EmailField(required=False, allow_blank=True, help_text="Optional: Email to send code to (if not provided, uses existing email)")


class UpdateEmailAndVerifySerializer(Serializer):
    """Serializer for updating email and sending verification code"""
    phone = PhoneNumberField(required=True, help_text="Phone number to verify")
    email = serializers.EmailField(required=True, help_text="Email address to send verification code")


class CheckEmailAvailableSerializer(Serializer):
    """Serializer for checking if email verification is available"""
    phone = PhoneNumberField(required=True, help_text="Phone number to check")


# =====================
# SHIPPING ADDRESS SERIALIZERS
# =====================

from accounts.models import ShippingAddress


class ShippingAddressSerializer(serializers.ModelSerializer):
    """Full serializer for shipping addresses with all fields."""
    full_address = serializers.SerializerMethodField()
    
    class Meta:
        model = ShippingAddress
        fields = [
            'id',
            'label',
            'full_name',
            'phone',
            'email',
            'address_line_1',
            'address_line_2',
            'city',
            'region',
            'postal_code',
            'country',
            'digital_address',
            'landmark',
            'delivery_instructions',
            'is_default',
            'full_address',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'full_address']
    
    def get_full_address(self, obj):
        return obj.get_full_address()


class ShippingAddressCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new shipping addresses."""
    
    class Meta:
        model = ShippingAddress
        fields = [
            'id',  # Include id in response
            'label',
            'full_name',
            'phone',
            'email',
            'address_line_1',
            'address_line_2',
            'city',
            'region',
            'postal_code',
            'country',
            'digital_address',
            'landmark',
            'delivery_instructions',
            'is_default',
        ]
        read_only_fields = ['id']  # id is read-only (generated on create)
    
    def create(self, validated_data):
        # Get user from context
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)


class ShippingAddressListSerializer(serializers.ModelSerializer):
    """Serializer for listing addresses with all needed fields for checkout."""
    full_address = serializers.SerializerMethodField()
    
    class Meta:
        model = ShippingAddress
        fields = [
            'id',
            'label',
            'full_name',
            'phone',
            'email',
            'address_line_1',
            'address_line_2',
            'city',
            'region',
            'postal_code',
            'country',
            'digital_address',
            'landmark',
            'delivery_instructions',
            'is_default',
            'full_address',
        ]
        read_only_fields = fields
    
    def get_full_address(self, obj):
        return obj.get_full_address()


class ShippingAddressMinimalSerializer(serializers.ModelSerializer):
    """Minimal serializer for dropdown selections."""
    display = serializers.SerializerMethodField()
    
    class Meta:
        model = ShippingAddress
        fields = ['id', 'label', 'display', 'is_default']
        read_only_fields = fields
    
    def get_display(self, obj):
        return f"{obj.label}: {obj.address_line_1}, {obj.city}"

