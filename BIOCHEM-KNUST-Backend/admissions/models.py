from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from utils.media_mixins import MediaUrlMixin
from utils.dynamic_storage import DynamicStorage

User = get_user_model()


class AdmissionCriteria(models.Model):
    """
    Dynamic admission criteria for KNUST CS/IT programs
    Can be updated by administrators when KNUST changes requirements
    """
    PROGRAM_CHOICES = [
        ('CS', 'Computer Science'),
        ('IT', 'Information Technology'),
    ]

    program = models.CharField(max_length=2, choices=PROGRAM_CHOICES)
    academic_year = models.CharField(max_length=20, help_text="e.g., 2025/2026")
    
    # Cut-off points
    aggregate_cutoff = models.IntegerField(
        validators=[MinValueValidator(6), MaxValueValidator(54)],
        help_text="Minimum aggregate score (6 is best, 54 is worst)"
    )
    
    # Core subject requirements
    core_math_min_grade = models.CharField(
        max_length=2, 
        default='C6',
        help_text="Minimum grade for Core Mathematics (e.g., A1, B2, C6)"
    )
    english_min_grade = models.CharField(
        max_length=2,
        default='C6', 
        help_text="Minimum grade for English Language"
    )
    integrated_science_min_grade = models.CharField(
        max_length=2,
        default='C6',
        help_text="Minimum grade for Integrated Science"
    )
    social_studies_min_grade = models.CharField(
        max_length=2,
        default='C6',
        help_text="Minimum grade for Social Studies"
    )
    
    # Elective subject requirements
    elective_math_required = models.BooleanField(
        default=True,
        help_text="Is Elective Mathematics required?"
    )
    elective_math_min_grade = models.CharField(
        max_length=2,
        default='C6',
        help_text="Minimum grade for Elective Mathematics"
    )
    
    # Physics requirement
    physics_required = models.BooleanField(
        default=True,
        help_text="Is Physics required?"
    )
    physics_min_grade = models.CharField(
        max_length=2,
        default='C6',
        help_text="Minimum grade for Physics"
    )
    
    # Science electives (at least one required)
    science_electives_required = models.IntegerField(
        default=2,
        help_text="Minimum number of science electives required"
    )
    
    # Additional requirements
    additional_requirements = models.TextField(
        blank=True,
        help_text="Any additional requirements or notes"
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='updated_criteria'
    )

    class Meta:
        ordering = ['-academic_year', 'program']
        unique_together = ['program', 'academic_year']
        verbose_name_plural = "Admission Criteria"

    def __str__(self):
        return f"{self.get_program_display()} - {self.academic_year}"


class SubjectGradeMapping(models.Model):
    """
    Maps WASSCE grades to numerical values for calculation
    """
    grade = models.CharField(max_length=2, unique=True)
    numerical_value = models.IntegerField()
    description = models.CharField(max_length=100)
    
    class Meta:
        ordering = ['numerical_value']
    
    def __str__(self):
        return f"{self.grade} = {self.numerical_value}"


class AdmissionGuideline(MediaUrlMixin, models.Model):
    """
    Step-by-step guides and resources for KNUST admission
    """
    # Media URL field mappings for auto-population
    MEDIA_URL_FIELDS = {
        'image': 'image_url',
    }
    
    GUIDE_TYPE_CHOICES = [
        ('VOUCHER', 'Voucher Purchase'),
        ('REGISTRATION', 'Account Registration'),
        ('APPLICATION', 'Application Form'),
        ('DOCUMENTS', 'Required Documents'),
        ('STATUS', 'Status Checking'),
        ('GENERAL', 'General Information'),
    ]
    
    title = models.CharField(max_length=200)
    guide_type = models.CharField(max_length=20, choices=GUIDE_TYPE_CHOICES)
    content = models.TextField(help_text="Detailed step-by-step instructions")
    order = models.IntegerField(default=0, help_text="Display order")
    
    # External links
    portal_url = models.URLField(blank=True, help_text="Related portal URL")
    
    # Rich content
    video_url = models.URLField(blank=True, help_text="Tutorial video URL")
    image = models.ImageField(storage=DynamicStorage(), upload_to='admission_guides/', blank=True)
    image_url = models.URLField(
        blank=True,
        null=True,
        help_text="Alternative: Provide image URL instead of uploading"
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['guide_type', 'order']
    
    def __str__(self):
        return f"{self.get_guide_type_display()} - {self.title}"


class EligibilityCheck(models.Model):
    """
    Records of eligibility checks performed by prospective students
    """
    # Student information (required)
    full_name = models.CharField(max_length=200, default='Unknown', help_text="Full name of prospective student")
    email = models.EmailField(default='unknown@example.com', help_text="Student's email address")
    phone = models.CharField(max_length=15, default='0000000000', help_text="Student's phone number")
    shs_school = models.CharField(max_length=300, default='Not Specified', help_text="Senior High School attended")
    completion_year = models.IntegerField(
        default=2024,
        validators=[MinValueValidator(2000), MaxValueValidator(2030)],
        help_text="Year completed SHS (e.g., 2024)"
    )
    
    # WASSCE results
    aggregate_score = models.IntegerField(
        validators=[MinValueValidator(6), MaxValueValidator(54)]
    )
    
    # Core subjects
    core_math_grade = models.CharField(max_length=2)
    english_grade = models.CharField(max_length=2)
    integrated_science_grade = models.CharField(max_length=2)
    social_studies_grade = models.CharField(max_length=2)
    
    # Elective subjects
    elective_math_grade = models.CharField(max_length=2, blank=True)
    physics_grade = models.CharField(max_length=2, blank=True)
    chemistry_grade = models.CharField(max_length=2, blank=True)
    biology_grade = models.CharField(max_length=2, blank=True)
    elective_ict_grade = models.CharField(max_length=2, blank=True)
    
    # Other electives
    other_elective_1 = models.CharField(max_length=50, blank=True)
    other_elective_1_grade = models.CharField(max_length=2, blank=True)
    other_elective_2 = models.CharField(max_length=50, blank=True)
    other_elective_2_grade = models.CharField(max_length=2, blank=True)
    
    # Program preference
    preferred_program = models.CharField(max_length=2, choices=[('CS', 'Computer Science'), ('IT', 'Information Technology')])
    
    # Admission type
    ADMISSION_TYPE_CHOICES = [
        ('REGULAR', 'Regular Admission'),
        ('FEE_PAYING', 'Fee-Paying/Parallel Program'),
        ('MATURE', 'Mature Applicant (25+ with experience)'),
    ]
    admission_type = models.CharField(
        max_length=20,
        choices=ADMISSION_TYPE_CHOICES,
        default='REGULAR',
        help_text="Type of admission pathway"
    )
    
    # Results
    is_eligible = models.BooleanField(default=False)
    meets_regular_requirements = models.BooleanField(default=False, help_text="Meets regular admission requirements")
    meets_feepaying_requirements = models.BooleanField(default=False, help_text="Meets fee-paying requirements")
    eligibility_details = models.JSONField(default=dict, help_text="Detailed eligibility breakdown")
    recommendations = models.TextField(blank=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    checked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-checked_at']
        verbose_name_plural = "Eligibility Checks"
    
    def __str__(self):
        return f"Check for {self.preferred_program} - {self.checked_at.strftime('%Y-%m-%d')}"


class FAQ(models.Model):
    """
    Frequently Asked Questions about KNUST admissions
    """
    question = models.CharField(max_length=300)
    answer = models.TextField()
    category = models.CharField(
        max_length=50,
        choices=[
            ('REQUIREMENTS', 'Requirements'),
            ('APPLICATION', 'Application Process'),
            ('FEES', 'Fees & Payment'),
            ('PROGRAMS', 'Programs'),
            ('DEADLINES', 'Deadlines'),
            ('DOCUMENTS', 'Documents'),
            ('OTHER', 'Other'),
        ],
        default='OTHER'
    )
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'order']
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"
    
    def __str__(self):
        return self.question


class ImportantDate(models.Model):
    """
    Important dates for KNUST admission cycles
    """
    EVENT_TYPES = [
        ('APPLICATION_OPEN', 'Application Opens'),
        ('APPLICATION_CLOSE', 'Application Closes'),
        ('RESULTS', 'Results Release'),
        ('ORIENTATION', 'Orientation'),
        ('REGISTRATION', 'Registration'),
        ('OTHER', 'Other'),
    ]
    
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    event_date = models.DateField()
    academic_year = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['event_date']
    
    def __str__(self):
        return f"{self.title} - {self.event_date}"


class WhatsAppHelpdesk(models.Model):
    """
    WhatsApp group configuration for admission programs
    Groups can be for ADMISSION helpdesk or ACADEMIC (official class groups)
    Students verify their admission status via Application ID lookup in KNUSTAdmission
    """
    GROUP_TYPE_CHOICES = [
        ('ADMISSION', 'Admission Helpdesk'),
        ('ACADEMIC', 'Academic/Class Group'),
    ]
    
    program = models.CharField(
        max_length=2,
        choices=[('CS', 'Computer Science'), ('IT', 'Information Technology')],
        help_text="Program this WhatsApp group is for"
    )
    group_type = models.CharField(
        max_length=20,
        choices=GROUP_TYPE_CHOICES,
        default='ADMISSION',
        help_text="Type of group: ADMISSION for helpdesk, ACADEMIC for official class groups"
    )
    academic_year = models.CharField(
        max_length=20,
        default='2025/2026',
        help_text="Academic year (e.g., 2025/2026)"
    )
    whatsapp_group_link = models.URLField(
        help_text="WhatsApp group invite link for admitted students"
    )
    group_description = models.TextField(
        blank=True,
        help_text="Description shown to students before joining"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Is this group currently active for new students?"
    )
    access_count = models.IntegerField(
        default=0,
        help_text="Total number of times link was accessed"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_whatsapp_groups'
    )
    
    class Meta:
        ordering = ['-academic_year', 'program', 'group_type']
        verbose_name = "WhatsApp Group"
        verbose_name_plural = "WhatsApp Groups"
        unique_together = ['program', 'group_type', 'academic_year']
    
    def __str__(self):
        return f"{self.get_program_display()} - {self.get_group_type_display()} - {self.academic_year}"


class WhatsAppAccessLog(models.Model):
    """
    Tracks when students access WhatsApp group links
    """
    helpdesk = models.ForeignKey(
        WhatsAppHelpdesk,
        on_delete=models.CASCADE,
        related_name='access_logs'
    )
    application_id = models.CharField(
        max_length=100,
        help_text="Student's application ID"
    )
    student_name = models.CharField(
        max_length=300,
        help_text="Student name from KNUSTAdmission"
    )
    accessed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-accessed_at']
        verbose_name = "WhatsApp Access Log"
        verbose_name_plural = "WhatsApp Access Logs"
    
    def __str__(self):
        return f"{self.application_id} - {self.student_name}"


def get_current_academic_year():
    """Get current academic year based on current date.
    Academic year runs from September to August.
    Returns format: '2025/2026'
    """
    from django.utils import timezone
    current_date = timezone.now()
    current_year = current_date.year
    current_month = current_date.month
    
    # If month >= 9 (Sep-Dec), we're in the next academic year
    if current_month >= 9:
        return f"{current_year}/{current_year + 1}"
    else:
        return f"{current_year - 1}/{current_year}"


class KNUSTAdmission(models.Model):
    """
    Stores scraped KNUST Computer Science admission data
    Supports multiple academic years and different admission statuses
    """
    ADMISSION_STATUS_CHOICES = [
        ('REGULAR', 'Regular/WASSCE'),
        ('FEE_PAYING', 'Fee Paying'),
        ('MATURE', 'Mature/Other'),
        ('INTERNATIONAL', 'International'),
        ('LESS_ENDOWED', 'Less Endowed Schools'),
        ('NMTC', 'NMTC Upgrade'),
        ('UNKNOWN', 'Unknown'),
    ]
    
    PROGRAMME_CHOICES = [
        ('CS', 'BSc. Computer Science'),
        ('IT', 'BSc. Information Technology'),
    ]
    
    # ========================================
    # ACCOMMODATION CHOICES (New fields)
    # ========================================
    ACCOMMODATION_TYPE_CHOICES = [
        ('TRADITIONAL_HALL', 'Traditional Hall'),
        ('HOSTEL', 'Hostel'),
        ('OFF_CAMPUS', 'Off Campus'),
    ]
    
    CAMPUS_STATUS_CHOICES = [
        ('ON_CAMPUS', 'On Campus'),
        ('OFF_CAMPUS', 'Off Campus'),
    ]
    
    # Traditional halls at KNUST
    TRADITIONAL_HALL_CHOICES = [
        ('UNITY_HALL', 'Unity Hall (Conti)'),
        ('QUEENS_HALL', "Queen's Hall"),
        ('INDEPENDENCE_HALL', 'Independence Hall (Indece)'),
        ('AFRICA_HALL', 'Africa Hall'),
        ('REPUBLIC_HALL', 'Republic Hall (Rep)'),
        ('UNIVERSITY_HALL', 'University Hall (Katanga)'),
        ('OTHER', 'Other'),
    ]
    
    applicant_id = models.CharField(
        max_length=100,
        help_text="Unique applicant ID from KNUST"
    )
    name = models.CharField(max_length=300, help_text="Full name of applicant")
    programme = models.CharField(
        max_length=200,
        help_text="Programme admitted to (e.g., BSc. Computer Science)"
    )
    programme_code = models.CharField(
        max_length=2,
        choices=PROGRAMME_CHOICES,
        default='CS',
        help_text="Programme code (CS or IT)"
    )
    academic_year = models.CharField(
        max_length=20,
        default=get_current_academic_year,
        help_text="Academic year (e.g., 2025/2026)"
    )
    admission_status = models.CharField(
        max_length=20,
        choices=ADMISSION_STATUS_CHOICES,
        default='REGULAR',
        help_text="Type of admission"
    )
    status = models.TextField(
        blank=True,
        help_text="Additional admission status/info (from scraper)"
    )
    
    # Source tracking
    source = models.CharField(
        max_length=20,
        choices=[
            ('SCRAPER', 'Web Scraper'),
            ('UPLOAD', 'Excel Upload'),
            ('MANUAL', 'Manual Entry'),
        ],
        default='SCRAPER',
        help_text="How this record was added"
    )
    
    # ========================================
    # ACCOMMODATION DETAILS (New optional fields)
    # These fields are nullable to not affect existing records
    # ========================================
    accommodation_type = models.CharField(
        max_length=20,
        choices=ACCOMMODATION_TYPE_CHOICES,
        blank=True,
        null=True,
        help_text="Type of accommodation (Hall, Hostel, or Off-campus)"
    )
    campus_status = models.CharField(
        max_length=20,
        choices=CAMPUS_STATUS_CHOICES,
        blank=True,
        null=True,
        help_text="Whether student lives on or off campus"
    )
    hall_name = models.CharField(
        max_length=50,
        choices=TRADITIONAL_HALL_CHOICES,
        blank=True,
        null=True,
        help_text="Name of traditional hall (if in hall)"
    )
    hostel_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Name of hostel (if in hostel)"
    )
    room_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Room number"
    )
    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        help_text="Student's phone number"
    )
    accommodation_updated_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When accommodation details were last updated"
    )
    accommodation_verified = models.BooleanField(
        default=False,
        help_text="Whether the student has verified and submitted their accommodation details"
    )
    
    # Timestamps
    fetched_at = models.DateTimeField(auto_now_add=True, help_text="When the data was first added")
    updated_at = models.DateTimeField(auto_now=True, help_text="Last time the data was updated")
    
    class Meta:
        ordering = ['-fetched_at']
        verbose_name = "KNUST Admission"
        verbose_name_plural = "KNUST Admissions"
        # Unique together: same applicant can't be in same programme in same year
        unique_together = ['applicant_id', 'academic_year']
        indexes = [
            models.Index(fields=['applicant_id']),
            models.Index(fields=['academic_year']),
            models.Index(fields=['programme_code']),
            models.Index(fields=['admission_status']),
            models.Index(fields=['-fetched_at']),
        ]
    
    def save(self, *args, **kwargs):
        # Auto-detect programme code from programme name
        if self.programme:
            programme_upper = self.programme.upper()
            if 'COMPUTER SCIENCE' in programme_upper:
                self.programme_code = 'CS'
            elif 'INFORMATION TECHNOLOGY' in programme_upper:
                self.programme_code = 'IT'
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.applicant_id} - {self.name} ({self.academic_year})"
    
    @classmethod
    def get_admission_status_from_group(cls, admission_group):
        """Map scraped admission group to admission status choice."""
        group_mapping = {
            'SSSCE/WASSCE': 'REGULAR',
            'Fee Paying SSSCE/WASSCE': 'FEE_PAYING',
            'Fee Paying (Mature/Other)': 'FEE_PAYING',
            'Mature/Other/Foreign Results': 'MATURE',
            'International Applicants': 'INTERNATIONAL',
            'Less Endowed Schools': 'LESS_ENDOWED',
            'NMTC Upgrade': 'NMTC',
        }
        return group_mapping.get(admission_group, 'UNKNOWN')

