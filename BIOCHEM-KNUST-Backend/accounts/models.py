from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from phonenumber_field.modelfields import PhoneNumberField
from django.utils.translation import gettext_lazy as _
from uuid import uuid4
from news.models import News
from academics.models import OnlineTutorialTips, AcademicSlides, PastQuestions
from django.utils import timezone

# Create your models here.


class ActiveStudentQuerySet(models.QuerySet):
    """Custom QuerySet that provides methods to filter students."""
    
    def active_students(self):
        """
        Filter to only include currently enrolled (non-graduated) students.
        Uses graduation_year to determine if a student has completed their program.
        
        A student is considered graduated if:
        - Their graduation year has passed
        - Their graduation year is the current year and we're past October (semester completed)
        """
        now = timezone.now()
        current_year = now.year
        current_month = now.month
        
        # After November 30th, use next year as effective year
        adjustment = 1 if (current_month == 12 or (current_month == 11 and now.day > 30)) else 0
        effective_year = current_year + adjustment
        
        # Active students have graduation_year >= effective_year
        # (they haven't graduated yet)
        return self.filter(
            graduation_year__gte=effective_year,
            is_active=True
        )
    
    def graduated_students(self):
        """
        Filter to only include students who have completed their program.
        """
        now = timezone.now()
        current_year = now.year
        current_month = now.month
        
        # After November 30th, use next year as effective year
        adjustment = 1 if (current_month == 12 or (current_month == 11 and now.day > 30)) else 0
        effective_year = current_year + adjustment
        
        # Graduated students have graduation_year < effective_year
        return self.filter(graduation_year__lt=effective_year)
    
    def non_graduated_active(self):
        """
        Filter for active students who haven't graduated.
        This is the primary method to use when querying for current students.
        """
        return self.active_students()


class ActiveStudentManager(BaseUserManager):
    """
    Manager that returns only active (non-graduated) students by default.
    Use this for queries where you only want current students.
    """
    
    def get_queryset(self):
        return ActiveStudentQuerySet(self.model, using=self._db).active_students()


class CustomUserManager(BaseUserManager):
    """
    Custom manager for CustomUser model with methods for creating users
    and querying active/graduated students.
    """
    
    def get_queryset(self):
        return ActiveStudentQuerySet(self.model, using=self._db)
    
    def active_students(self):
        """Get only currently enrolled students (non-graduated)."""
        return self.get_queryset().active_students()
    
    def graduated_students(self):
        """Get only graduated students."""
        return self.get_queryset().graduated_students()
    
    def non_graduated_active(self):
        """Alias for active_students - primary method for current students."""
        return self.active_students()
    
    def create_user(
        self,
        first_name,
        last_name,
        # index_number,
        graduation_year,
        phone,
        password,
        **extra_fields,
    ):
        """
        Create and save a user with the given email and password.
        """
        if not phone:
            raise ValueError(_("The Phone must be set"))
        user = self.model(
            first_name=first_name,
            last_name=last_name,
            # index_number=index_number,
            phone=phone,
            graduation_year=graduation_year,
            **extra_fields,
        )
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, graduation_year, phone, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))
        return self.create_user(
            phone=phone,
            # index_number=index_number,
            password=password,
            graduation_year=graduation_year,
            **extra_fields,
        )


class CustomUser(AbstractUser):
    username = None
    email = None
    id = models.UUIDField(primary_key=True, unique=True, default=uuid4)
    phone = PhoneNumberField(unique=True)
    # index_number = models.CharField(_("index number"), unique=True, max_length=255)
    """
    dont store user year directly which becomes complicated since it has
    to be increased every year for each user which will affect the system performance
    """
    # current year subtracted from graduation_year will give you the user year (1-4)
    graduation_year = models.IntegerField()
    first_name = models.CharField(max_length=255)
    middle_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Optional middle name"
    )
    last_name = models.CharField(max_length=255)
    phone_confirm = models.BooleanField(default=False)
    
    PROGRAM_CHOICES = [
        ('CS', 'BSc Computer Science'),
        ('IT', 'BSc Information Technology'),
    ]
    program = models.CharField(
        max_length=2,
        choices=PROGRAM_CHOICES,
        null=True,
        blank=True,
        help_text="The program the student is enrolled in"
    )
    
    GROUP_CHOICES = [
        ('G1', 'Group 1'),
        ('G2', 'Group 2'),
    ]
    group = models.CharField(
        max_length=2,
        choices=GROUP_CHOICES,
        null=True,
        blank=True,
        help_text="The group/section the student belongs to (G1/G2). Currently only required for Computer Science students. IT students do not have groups."
    )
    
    # New student information fields
    student_id = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text="Unique student identifier"
    )
    index_number = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text="Student index number (may not be available immediately)"
    )
    personal_email = models.EmailField(
        null=True,
        blank=True,
        help_text="Personal email address"
    )
    student_email = models.EmailField(
        null=True,
        blank=True,
        help_text="Official student email address"
    )
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        null=True,
        blank=True,
        help_text="Gender"
    )
    
    current_semester = models.IntegerField(
        null=True,
        blank=True,
        help_text="Current semester (auto-calculated)"
    )

    USERNAME_FIELD = "phone"

    REQUIRED_FIELDS = ["first_name", "last_name", "graduation_year", ]

    # Default manager - returns all users
    objects = CustomUserManager()
    
    # Manager that returns only currently enrolled (non-graduated) students
    # Use this when you need to query only active, non-graduated students
    current_students = ActiveStudentManager()

    class Meta:
        permissions = [
            ("view_sensitive_student_data", "Can view sensitive student information (emails, student ID, index number)"),
            ("view_accounts_analytics", "Can view accounts analytics dashboard"),
            ("deactivate_graduated_students", "Can deactivate graduated students"),
        ]
        indexes = [
            models.Index(fields=['phone']),  # Primary lookup field
            models.Index(fields=['graduation_year']),
            models.Index(fields=['program']),
            models.Index(fields=['phone_confirm']),
            models.Index(fields=['is_active']),  # For filtering active users
        ]

    def _get_academic_year_adjustment(self):
        """
        Determine if we should use "next year" for academic calculations.
        After November 30th, students are "promoted" to the next academic year.
        
        Returns:
            int: 0 if no adjustment, 1 if we should add a year to calculations
        """
        now = timezone.now()
        # After November 30th, consider students as being in the next academic year
        if now.month == 12 or (now.month == 11 and now.day > 30):
            return 1
        return 0
    
    def _is_semester_started(self):
        """
        Check if the current semester has started.
        
        Academic Calendar:
        - First Semester: January to mid-April (Months 1-4)
        - Second Semester: Late May to mid-September (Months 5-9)
        - Vacation/Break: October to December (Months 10-12)
        
        Returns:
            bool: True if semester is active, False if on vacation/break
        """
        current_month = timezone.now().month
        # Vacation period is October to December
        return current_month < 10
    
    def get_academic_status(self):
        """
        Get comprehensive academic status including year, semester, and status.
        
        Returns:
            dict: {
                'year': int (1-4),
                'semester': int (1 or 2),
                'semester_status': str ('active', 'not_started', 'completed'),
                'semester_display': str (human readable),
                'year_display': str (human readable),
                'is_fresher_waiting': bool,
                'is_graduated': bool,
                'completed_semesters': int (0-8)
            }
        """
        now = timezone.now()
        current_month = now.month
        current_year = now.year
        adjustment = self._get_academic_year_adjustment()
        
        # Calculate academic year (with adjustment after Nov 30th)
        effective_year = current_year + adjustment
        diff = int(self.graduation_year) - effective_year
        year_num = 4 - diff  # Year 1, 2, 3, or 4
        
        # Determine semester and status
        if current_month >= 10:  # October to December
            if adjustment == 1:
                # After Nov 30th - promoted to next year, in 1st semester
                semester = 1
                semester_status = 'active'
                semester_display = 'First Semester'
            else:
                # Oct-Nov 30th - still in vacation, 2nd semester just completed
                semester = 2
                semester_status = 'completed'
                semester_display = 'Second Semester (Completed)'
        elif 1 <= current_month <= 4:
            # January to April - First Semester active
            semester = 1
            semester_status = 'active'
            semester_display = 'First Semester'
        elif 5 <= current_month <= 9:
            # May to September - Second Semester active
            semester = 2
            semester_status = 'active'
            semester_display = 'Second Semester'
        else:
            # Fallback (shouldn't reach here)
            semester = 1
            semester_status = 'active'
            semester_display = 'First Semester'
        
        # Handle edge cases
        is_fresher_waiting = year_num == 1 and semester_status == 'not_started'
        
        # Check if graduated: Year > 4 OR graduation year has passed
        is_graduated = False
        if year_num > 4:
            is_graduated = True
        elif int(self.graduation_year) < current_year:
            is_graduated = True
        elif int(self.graduation_year) == current_year and current_month >= 10:
            # Graduated this year after completing 2nd semester
            is_graduated = True
        
        # Ensure year is within valid range (1-4)
        if year_num < 1:
            year_num = 1
            is_fresher_waiting = True
            semester_status = 'not_started'
            semester_display = 'First Semester (Not Started)'
        elif year_num > 4:
            year_num = 4
            is_graduated = True
        
        # Calculate year display
        year_suffixes = {1: 'st', 2: 'nd', 3: 'rd', 4: 'th'}
        year_display = f"Year {year_num}"
        
        # Calculate completed semesters
        completed_semesters = self._calculate_completed_semesters(
            year_num, semester, semester_status, is_graduated, is_fresher_waiting
        )
        
        return {
            'year': year_num,
            'semester': semester,
            'semester_status': semester_status,
            'semester_display': semester_display,
            'year_display': year_display,
            'is_fresher_waiting': is_fresher_waiting,
            'is_graduated': is_graduated,
            'completed_semesters': completed_semesters
        }
    
    def _calculate_completed_semesters(self, year_num, semester, semester_status, is_graduated=False, is_fresher_waiting=False):
        """
        Calculate completed semesters based on academic status.
        
        Args:
            year_num: Current year (1-4)
            semester: Current semester (1 or 2)
            semester_status: 'active', 'not_started', or 'completed'
            is_graduated: Whether the student has graduated
            is_fresher_waiting: Whether this is a fresher waiting to start
        
        Returns:
            int: Number of completed semesters (0-8)
        """
        # If graduated, they've completed all 8 semesters
        if is_graduated:
            return 8
        
        # If fresher waiting, they have 0 completed semesters
        if is_fresher_waiting:
            return 0
        
        # Semesters from previous years
        semesters_from_previous_years = (year_num - 1) * 2
        
        # Semesters in current year
        if semester_status == 'not_started':
            # Semester hasn't started yet - no additional semesters
            current_year_semesters = 0
        elif semester_status == 'active':
            # Currently in a semester
            if semester == 1:
                current_year_semesters = 0  # In 1st semester, none completed this year
            else:
                current_year_semesters = 1  # In 2nd semester, 1st is completed
        elif semester_status == 'completed':
            # Semester completed
            if semester == 2:
                current_year_semesters = 2  # Both semesters completed this year
            else:
                current_year_semesters = 1
        else:
            current_year_semesters = 0
        
        total = semesters_from_previous_years + current_year_semesters
        return max(0, min(total, 8))
    
    @property
    def year(self):
        """
        Property to get student year (1, 2, 3, 4).
        KNUST uses Year (1-4) not Level (100-400).
        """
        try:
            return self.get_academic_status()['year']
        except Exception:
            return None
    
    @property
    def level(self):
        """
        Backwards compatibility alias for year property.
        Deprecated: Use .year instead.
        """
        return self.year

    def get_year(self):
        """
        Get the student's current year (1-4).
        """
        try:
            return self.get_academic_status()['year']
        except Exception:
            return 1
    
    def get_level(self):
        """
        Backwards compatibility alias for get_year().
        Deprecated: Use get_year() instead.
        """
        return self.get_year()
    
    def calculate_current_semester(self):
        """
        Calculate current semester based on current month.
        First Semester: January to mid-April (Months 1-4)
        Second Semester: Late May to mid-September (Months 5-9)
        Vacation/Break: October to December (Months 10-12)
        
        Returns the semester number (1 or 2).
        """
        try:
            return self.get_academic_status()['semester']
        except Exception:
            return 1
    
    def get_semester_display(self):
        """Get human-readable semester status"""
        try:
            return self.get_academic_status()['semester_display']
        except Exception:
            return "Semester Unknown"
    
    def get_completed_semesters(self):
        """
        Calculate total number of semesters completed.
        Maximum is 8 semesters (4 years of education).
        """
        try:
            return self.get_academic_status()['completed_semesters']
        except Exception:
            return 0
    
    def has_completed_program(self):
        """Check if student has completed all 8 semesters (4 years)"""
        return self.get_completed_semesters() >= 8
    
    def get_program_display_name(self):
        """Return the full program name"""
        if self.program:
            return dict(self.PROGRAM_CHOICES).get(self.program, "Program not set")
        return "Program not set"
    
    def get_gender_display_name(self):
        """Return the full gender name"""
        if self.gender:
            return dict(self.GENDER_CHOICES).get(self.gender, "Not specified")
        return "Not specified"
    
    def get_group_display_name(self):
        """Return the full group name"""
        if self.group:
            return dict(self.GROUP_CHOICES).get(self.group, "Not set")
        return "Not set"
    
    def get_current_academic_year(self):
        """Calculate current academic year based on current month and graduation year"""
        current_date = timezone.now()
        current_year = current_date.year
        current_month = current_date.month
        
        # Academic year runs from ~September to ~August
        # If month > 9 (Oct-Dec), we're in the next academic year
        if current_month > 9:
            return f"{current_year}/{current_year + 1}"
        else:
            return f"{current_year - 1}/{current_year}"
    
    def clean(self):
        """Validate unique fields and graduation year"""
        from django.core.exceptions import ValidationError
        errors = {}
        
        # Validate graduation_year is within valid range
        if self.graduation_year:
            now = timezone.now()
            current_year = now.year
            current_month = now.month
            current_day = now.day
            
            # Academic year adjustment: After November 30th, use next year
            adjustment = 1 if (current_month == 12 or (current_month == 11 and current_day > 30)) else 0
            effective_year = current_year + adjustment
            
            min_year = effective_year  # Year 4 students
            max_year = effective_year + 3  # Year 1 freshers
            
            if self.graduation_year < min_year:
                errors['graduation_year'] = _(
                    f'Invalid graduation year. Year {self.graduation_year} indicates you have already graduated. '
                    f'Valid graduation years are {min_year} to {max_year}.'
                )
            elif self.graduation_year > max_year:
                errors['graduation_year'] = _(
                    f'Invalid graduation year. Year {self.graduation_year} is too far in the future. '
                    f'Valid graduation years are {min_year} to {max_year}.'
                )
        
        # Validate student_id uniqueness
        if self.student_id:
            existing = CustomUser.objects.filter(student_id=self.student_id).exclude(id=self.id)
            if existing.exists():
                errors['student_id'] = _('A user with this student ID already exists.')
        
        # Validate index_number uniqueness
        if self.index_number:
            existing = CustomUser.objects.filter(index_number=self.index_number).exclude(id=self.id)
            if existing.exists():
                errors['index_number'] = _('A user with this index number already exists.')
        
        if errors:
            raise ValidationError(errors)
        
        super().clean()
    
    @classmethod
    def program_requires_group(cls, program):
        """
        Check if a program requires group separation.
        Currently only CS has groups (G1, G2), IT does not.
        This can be easily modified in the future if IT gets groups.
        
        Args:
            program: Program code ("CS" or "IT")
            
        Returns:
            bool: True if program requires groups, False otherwise
        """
        # Programs that require group separation
        PROGRAMS_WITH_GROUPS = ["CS"]
        return program in PROGRAMS_WITH_GROUPS
    
    def requires_group(self):
        """
        Check if this user's program requires a group.
        
        Returns:
            bool: True if user's program requires groups, False otherwise
        """
        return self.program_requires_group(self.program) if self.program else False

    def save(self, *args, **kwargs):
        """Override save to automatically calculate current_semester"""
        self.current_semester = self.calculate_current_semester()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        # Display full name in admin and selects while keeping phone as the login identifier
        full_name_parts = [self.first_name, self.middle_name, self.last_name]
        full_name = " ".join(part for part in full_name_parts if part).strip()
        return f"{full_name} ({self.phone})" if full_name else f"{self.phone}"

    class Meta:
        db_table = "account"
        verbose_name = "Account"


class PhoneVerifcationCodes(models.Model):
    phone = PhoneNumberField(unique=True, null=True, blank=False)
    email = models.EmailField(null=True, blank=True, help_text="Email address for code delivery as fallback")
    code = models.CharField(max_length=10, null=True, blank=False)
    expires_in = models.DateTimeField(null=True, blank=True, editable=False)
    last_sent = models.DateTimeField(null=True, blank=True, editable=False, help_text="Track when SMS was last sent to prevent spam")
    last_email_sent = models.DateTimeField(null=True, blank=True, editable=False, help_text="Track when email was last sent")
    send_count = models.IntegerField(default=0, help_text="Number of times SMS has been sent for this code")
    email_send_count = models.IntegerField(default=0, help_text="Number of times email has been sent for this code")
    
    # Track which method was used to send the code
    DELIVERY_METHOD_CHOICES = [
        ('sms', 'SMS'),
        ('email', 'Email'),
    ]
    last_delivery_method = models.CharField(
        max_length=10,
        choices=DELIVERY_METHOD_CHOICES,
        default='sms',
        help_text="The last method used to deliver the code"
    )

    class Meta:
        verbose_name = _("")
        verbose_name_plural = "PhoneVerificationCodes"

    def save(self, *args, **kwargs) -> None:
        if not self.expires_in:
            self.expires_in = timezone.now() + timezone.timedelta(minutes=10)
        return super().save(*args, **kwargs)
    
    def can_resend(self, cooldown_seconds=60):
        """Check if enough time has passed to resend SMS (default 60 seconds)"""
        if not self.last_sent:
            return True
        time_since_last = timezone.now() - self.last_sent
        return time_since_last.total_seconds() >= cooldown_seconds
    
    def can_resend_email(self, cooldown_seconds=60):
        """Check if enough time has passed to resend email (default 60 seconds)"""
        if not self.last_email_sent:
            return True
        time_since_last = timezone.now() - self.last_email_sent
        return time_since_last.total_seconds() >= cooldown_seconds

    def __str__(self) -> str:
        return str(self.code)


class FieldRequirementConfig(models.Model):
    """
    Model to manage which fields are required for different student levels.
    This allows dynamic field requirement configuration based on student progression.
    """
    
    FIELD_CHOICES = [
        ('student_id', 'Student ID'),
        ('index_number', 'Index Number'),
        ('personal_email', 'Personal Email'),
        ('student_email', 'Student Email'),
        ('gender', 'Gender'),
        ('program', 'Program'),
        ('first_name', 'First Name'),
        ('last_name', 'Last Name'),
        ('phone', 'Phone'),
        ('graduation_year', 'Graduation Year'),
    ]
    
    field_name = models.CharField(
        max_length=100,
        choices=FIELD_CHOICES,
        help_text="Name of the field this configuration applies to"
    )
    is_required = models.BooleanField(
        default=False,
        help_text="Whether this field is required"
    )
    required_from_year = models.IntegerField(
        null=True,
        blank=True,
        help_text="Year from which this field becomes required (e.g., 2, 3, 4)"
    )
    description = models.TextField(
        help_text="Description of when/why this field is required"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "field_requirement_config"
        unique_together = [['field_name', 'required_from_year']]
        verbose_name = "Field Requirement Configuration"
        verbose_name_plural = "Field Requirement Configurations"
        ordering = ['required_from_year', 'field_name']
    
    def __str__(self) -> str:
        year_text = f"from Year {self.required_from_year}" if self.required_from_year else "all years"
        required_text = "Required" if self.is_required else "Optional"
        return f"{self.get_field_name_display()} - {required_text} {year_text}"


class UserSavedBlogs(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    blogs = models.ManyToManyField(to=News)
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_saved_blogs"


class UserSavedSlides(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    slides = models.ManyToManyField(to=AcademicSlides)
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_saved_slides"


class UserSavedOnlineTutorialTips(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    online_tips = models.ManyToManyField(to=OnlineTutorialTips)
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_saved_online_tutorial_tips"


class UserSavedPastQueations(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    past_questions = models.ManyToManyField(to=PastQuestions)
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_saved_past_questions"


class ShippingAddress(models.Model):
    """
    User's saved shipping addresses for orders.
    Users can have multiple addresses with one set as default.
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='shipping_addresses'
    )
    
    # Address label (e.g., "Home", "Office", "Campus")
    label = models.CharField(
        max_length=50,
        default='Home',
        help_text="Label for this address (e.g., Home, Office, Campus)"
    )
    
    # Recipient info
    full_name = models.CharField(max_length=255)
    phone = PhoneNumberField()
    email = models.EmailField(blank=True, null=True)
    
    # Address details
    address_line_1 = models.CharField(max_length=255, help_text="Street address, P.O. box, etc.")
    address_line_2 = models.CharField(max_length=255, blank=True, help_text="Apartment, suite, unit, etc.")
    city = models.CharField(max_length=100)
    region = models.CharField(max_length=100, blank=True, help_text="State/Province/Region")
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default='Ghana')
    
    # GPS/Digital address (common in Ghana)
    digital_address = models.CharField(
        max_length=50,
        blank=True,
        help_text="Ghana Post GPS digital address (e.g., GA-123-4567)"
    )
    
    # Landmark for easier delivery
    landmark = models.CharField(
        max_length=255,
        blank=True,
        help_text="Nearby landmark to help locate the address"
    )
    
    # Delivery instructions
    delivery_instructions = models.TextField(
        blank=True,
        help_text="Special instructions for delivery"
    )
    
    # Settings
    is_default = models.BooleanField(
        default=False,
        help_text="Set as default shipping address"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "user_shipping_addresses"
        verbose_name = "Shipping Address"
        verbose_name_plural = "Shipping Addresses"
        ordering = ['-is_default', '-updated_at']
        indexes = [
            models.Index(fields=['user', 'is_default']),
        ]
    
    def __str__(self):
        return f"{self.label}: {self.address_line_1}, {self.city}"
    
    def save(self, *args, **kwargs):
        # If this is set as default, unset other defaults for this user
        if self.is_default:
            ShippingAddress.objects.filter(
                user=self.user,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        
        # If this is the user's first address, make it default
        if not self.pk and not ShippingAddress.objects.filter(user=self.user).exists():
            self.is_default = True
        
        super().save(*args, **kwargs)
    
    def get_full_address(self):
        """Return formatted full address string."""
        parts = [self.address_line_1]
        if self.address_line_2:
            parts.append(self.address_line_2)
        parts.append(self.city)
        if self.region:
            parts.append(self.region)
        if self.postal_code:
            parts.append(self.postal_code)
        parts.append(self.country)
        return ', '.join(parts)
    
    def to_order_data(self):
        """Convert to dictionary for order creation."""
        return {
            'shipping_name': self.full_name,
            'shipping_phone': str(self.phone),
            'shipping_email': self.email or '',
            'shipping_address_line_1': self.address_line_1,
            'shipping_address_line_2': self.address_line_2,
            'shipping_city': self.city,
            'shipping_region': self.region,
            'shipping_country': self.country,
            'digital_address': self.digital_address,
            'landmark': self.landmark,
            'delivery_instructions': self.delivery_instructions,
        }

