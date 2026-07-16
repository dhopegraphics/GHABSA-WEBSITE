from rest_framework import serializers
from .models import (
    AdmissionCriteria, SubjectGradeMapping, AdmissionGuideline,
    EligibilityCheck, FAQ, ImportantDate, WhatsAppHelpdesk, WhatsAppAccessLog,
    KNUSTAdmission
)


class AdmissionCriteriaSerializer(serializers.ModelSerializer):
    program_display = serializers.CharField(source='get_program_display', read_only=True)
    updated_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = AdmissionCriteria
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'updated_by']
    
    def get_updated_by_name(self, obj):
        if obj.updated_by:
            return f"{obj.updated_by.first_name} {obj.updated_by.last_name}"
        return None


class SubjectGradeMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubjectGradeMapping
        fields = '__all__'


class AdmissionGuidelineSerializer(serializers.ModelSerializer):
    guide_type_display = serializers.CharField(source='get_guide_type_display', read_only=True)
    
    class Meta:
        model = AdmissionGuideline
        fields = '__all__'


class EligibilityCheckSerializer(serializers.ModelSerializer):
    program_display = serializers.CharField(source='get_preferred_program_display', read_only=True)
    
    class Meta:
        model = EligibilityCheck
        fields = '__all__'
        read_only_fields = ['checked_at', 'ip_address', 'user_agent']  # Removed is_eligible, eligibility_details, recommendations from read_only


class EligibilityCheckInputSerializer(serializers.Serializer):
    """
    Serializer for eligibility check input
    """
    # Student information (required)
    full_name = serializers.CharField(max_length=200)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=15)
    shs_school = serializers.CharField(max_length=300)
    completion_year = serializers.IntegerField(min_value=2000, max_value=2030)
    
    # Program preference
    preferred_program = serializers.ChoiceField(choices=['CS', 'IT'])
    
    # Admission type
    admission_type = serializers.ChoiceField(
        choices=['REGULAR', 'FEE_PAYING', 'MATURE'],
        default='REGULAR',
        required=False
    )
    
    # Aggregate score
    aggregate_score = serializers.IntegerField(min_value=6, max_value=54)
    
    # Core subjects (all required)
    core_math_grade = serializers.CharField(max_length=2)
    english_grade = serializers.CharField(max_length=2)
    integrated_science_grade = serializers.CharField(max_length=2)
    social_studies_grade = serializers.CharField(max_length=2)
    
    # Elective subjects (some required based on program)
    elective_math_grade = serializers.CharField(max_length=2, required=False, allow_blank=True)
    physics_grade = serializers.CharField(max_length=2, required=False, allow_blank=True)
    chemistry_grade = serializers.CharField(max_length=2, required=False, allow_blank=True)
    biology_grade = serializers.CharField(max_length=2, required=False, allow_blank=True)
    elective_ict_grade = serializers.CharField(max_length=2, required=False, allow_blank=True)
    
    # Other electives
    other_elective_1 = serializers.CharField(max_length=50, required=False, allow_blank=True)
    other_elective_1_grade = serializers.CharField(max_length=2, required=False, allow_blank=True)
    other_elective_2 = serializers.CharField(max_length=50, required=False, allow_blank=True)
    other_elective_2_grade = serializers.CharField(max_length=2, required=False, allow_blank=True)
    
    def validate(self, data):
        """
        Validate that at least 3 elective subjects are provided
        """
        elective_fields = [
            'elective_math_grade',
            'physics_grade',
            'chemistry_grade',
            'biology_grade',
            'elective_ict_grade',
            'other_elective_1_grade',
            'other_elective_2_grade'
        ]
        
        elective_count = sum(1 for field in elective_fields if data.get(field) and data.get(field).strip())
        
        if elective_count < 3:
            raise serializers.ValidationError(
                f"You must provide at least 3 elective subjects. You provided {elective_count}. "
                "Elective subjects include: Elective Mathematics, Physics, Chemistry, Biology, ICT, or other electives."
            )
        
        return data


class FAQSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = FAQ
        fields = '__all__'


class ImportantDateSerializer(serializers.ModelSerializer):
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    
    class Meta:
        model = ImportantDate
        fields = '__all__'


class WhatsAppHelpdeskSerializer(serializers.ModelSerializer):
    """Serializer for program-based WhatsApp groups"""
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = WhatsAppHelpdesk
        fields = [
            'id', 'program', 'academic_year', 'whatsapp_group_link',
            'group_description', 'is_active', 'access_count',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'access_count', 'created_at', 'updated_at', 'created_by_name']


class WhatsAppAccessLogSerializer(serializers.ModelSerializer):
    """Serializer for WhatsApp group access logs"""
    group_program = serializers.CharField(source='group.program', read_only=True)
    
    class Meta:
        model = WhatsAppAccessLog
        fields = [
            'id', 'group', 'group_program', 'application_id',
            'student_name', 'accessed_at', 'ip_address'
        ]
        read_only_fields = ['id', 'accessed_at']


class WhatsAppHelpdeskInputSerializer(serializers.Serializer):
    """
    Serializer for getting WhatsApp link with Application ID
    """
    application_id = serializers.CharField(max_length=20, required=True)
    
    def validate_application_id(self, value):
        """Validate that application ID contains only numbers"""
        if not value or not value.strip():
            raise serializers.ValidationError("Application ID cannot be empty")
        if not value.strip().isdigit():
            raise serializers.ValidationError("Application ID must contain only numbers")
        return value.strip()


# ========================================
# KNUST ADMISSION SERIALIZERS
# ========================================

class KNUSTAdmissionSerializer(serializers.ModelSerializer):
    """
    Full serializer for KNUSTAdmission model
    Used for listing and retrieving admission records
    """
    programme_display = serializers.CharField(source='get_programme_code_display', read_only=True)
    admission_status_display = serializers.CharField(source='get_admission_status_display', read_only=True)
    accommodation_type_display = serializers.CharField(source='get_accommodation_type_display', read_only=True)
    campus_status_display = serializers.CharField(source='get_campus_status_display', read_only=True)
    hall_name_display = serializers.CharField(source='get_hall_name_display', read_only=True)
    
    class Meta:
        model = KNUSTAdmission
        fields = [
            'id', 'applicant_id', 'name', 'programme', 'programme_code', 'programme_display',
            'academic_year', 'admission_status', 'admission_status_display', 'status', 'source',
            # Accommodation fields
            'accommodation_type', 'accommodation_type_display',
            'campus_status', 'campus_status_display',
            'hall_name', 'hall_name_display', 'hostel_name',
            'room_number', 'phone_number',
            'accommodation_updated_at', 'accommodation_verified',
            # Timestamps
            'fetched_at', 'updated_at'
        ]
        read_only_fields = ['id', 'fetched_at', 'updated_at', 'accommodation_updated_at']


class AccommodationVerifySerializer(serializers.Serializer):
    """
    Step 1: Verify student identity before allowing accommodation update
    Takes applicant_id and phone_number, checks if they exist in accounts
    """
    applicant_id = serializers.CharField(max_length=100, required=True)
    phone_number = serializers.CharField(max_length=15, required=True)
    
    def validate_applicant_id(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Application ID cannot be empty")
        return value.strip()
    
    def validate_phone_number(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Phone number cannot be empty")
        # Remove any spaces or dashes
        cleaned = value.strip().replace(' ', '').replace('-', '')
        # Handle Ghanaian phone numbers
        if cleaned.startswith('+233'):
            cleaned = '0' + cleaned[4:]
        elif cleaned.startswith('233'):
            cleaned = '0' + cleaned[3:]
        if len(cleaned) != 10:
            raise serializers.ValidationError("Phone number must be 10 digits (e.g., 0241234567)")
        if not cleaned.isdigit():
            raise serializers.ValidationError("Phone number must contain only digits")
        return cleaned


class AccommodationNameVerifySerializer(serializers.Serializer):
    """
    Step 2: Verify student name matches the admission record
    Takes the name parts to compare against the stored name
    """
    applicant_id = serializers.CharField(max_length=100, required=True)
    first_name = serializers.CharField(max_length=100, required=True)
    last_name = serializers.CharField(max_length=100, required=True)
    other_names = serializers.CharField(max_length=100, required=False, allow_blank=True)
    
    def validate(self, data):
        # Clean up names
        data['first_name'] = data['first_name'].strip().upper()
        data['last_name'] = data['last_name'].strip().upper()
        if data.get('other_names'):
            data['other_names'] = data['other_names'].strip().upper()
        return data


class AccommodationUpdateSerializer(serializers.Serializer):
    """
    Step 3: Update accommodation details after identity verification
    """
    applicant_id = serializers.CharField(max_length=100, required=True)
    
    # Accommodation details
    accommodation_type = serializers.ChoiceField(
        choices=[
            ('TRADITIONAL_HALL', 'Traditional Hall'),
            ('HOSTEL', 'Hostel'),
            ('OFF_CAMPUS', 'Off Campus'),
        ],
        required=True
    )
    campus_status = serializers.ChoiceField(
        choices=[
            ('ON_CAMPUS', 'On Campus'),
            ('OFF_CAMPUS', 'Off Campus'),
        ],
        required=True
    )
    
    # Hall name (required if accommodation_type is TRADITIONAL_HALL)
    hall_name = serializers.ChoiceField(
        choices=[
            ('UNITY_HALL', 'Unity Hall (Conti)'),
            ('QUEENS_HALL', "Queen's Hall"),
            ('INDEPENDENCE_HALL', 'Independence Hall (Indece)'),
            ('AFRICA_HALL', 'Africa Hall (Katanga)'),
            ('REPUBLIC_HALL', 'Republic Hall (Rep)'),
            ('UNIVERSITY_HALL', 'University Hall (Brunei)'),
            ('OTHER', 'Other'),
        ],
        required=False,
        allow_null=True,
        allow_blank=True
    )
    
    # Hostel name (required if accommodation_type is HOSTEL)
    hostel_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    
    # Room number (required for on-campus students)
    room_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    
    # Phone number for contact
    phone_number = serializers.CharField(max_length=15, required=True)
    
    def validate_phone_number(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Phone number is required")
        cleaned = value.strip().replace(' ', '').replace('-', '')
        if cleaned.startswith('+233'):
            cleaned = '0' + cleaned[4:]
        elif cleaned.startswith('233'):
            cleaned = '0' + cleaned[3:]
        if len(cleaned) != 10:
            raise serializers.ValidationError("Phone number must be 10 digits")
        if not cleaned.isdigit():
            raise serializers.ValidationError("Phone number must contain only digits")
        return cleaned
    
    def validate(self, data):
        accommodation_type = data.get('accommodation_type')
        hall_name = data.get('hall_name')
        hostel_name = data.get('hostel_name')
        room_number = data.get('room_number')
        campus_status = data.get('campus_status')
        
        # Validate hall name is provided for traditional hall
        if accommodation_type == 'TRADITIONAL_HALL':
            if not hall_name:
                raise serializers.ValidationError({
                    'hall_name': 'Hall name is required for traditional hall accommodation'
                })
            # Auto-set campus status to ON_CAMPUS for hall residents
            data['campus_status'] = 'ON_CAMPUS'
        
        # Validate hostel name is provided for hostel
        if accommodation_type == 'HOSTEL':
            if not hostel_name or not hostel_name.strip():
                raise serializers.ValidationError({
                    'hostel_name': 'Hostel name is required for hostel accommodation'
                })
        
        # Validate room number for on-campus students
        if campus_status == 'ON_CAMPUS' and accommodation_type != 'OFF_CAMPUS':
            if not room_number or not room_number.strip():
                raise serializers.ValidationError({
                    'room_number': 'Room number is required for on-campus students'
                })
        
        # Auto-set campus status for off-campus accommodation
        if accommodation_type == 'OFF_CAMPUS':
            data['campus_status'] = 'OFF_CAMPUS'
            # Clear hall and hostel names for off-campus
            data['hall_name'] = None
            data['hostel_name'] = None
        
        return data
