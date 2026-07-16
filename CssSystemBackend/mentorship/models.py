"""
Mentorship System - Models

This module contains all models for the mentorship system:
- MentorshipArea: Areas/domains for mentorship (admin-created)
- SkillTag: Dynamic tags for skills/experience per area
- Interviewer: Staff members who conduct mentor interviews
- InterviewerSchedule: Available time slots for interviewers
- MentorApplication: Mentor application with all details
- InterviewBooking: Scheduled interviews between applicants and interviewers
- MenteeApplication: Mentee application to mentors
- MentorshipRelationship: Active mentor-mentee relationships
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from uuid import uuid4
from accounts.models import CustomUser


class MentorshipArea(models.Model):
    """
    Mentorship areas/domains that admin can create and manage.
    Examples: Cyber Security, Web Development, UI/UX Design, etc.
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Name of the mentorship area (e.g., Web Development)"
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        help_text="URL-friendly version of the name"
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed description of this mentorship area"
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="Icon name for frontend display (e.g., 'code', 'security')"
    )
    color = models.CharField(
        max_length=7,
        default="#3B82F6",
        help_text="Hex color code for the area badge"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this area is currently accepting applications"
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order (lower numbers appear first)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Mentorship Area"
        verbose_name_plural = "Mentorship Areas"
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class SkillTag(models.Model):
    """
    Dynamic skill/experience tags that are specific to mentorship areas.
    Tags can be selected by both mentors and mentees.
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    area = models.ForeignKey(
        MentorshipArea,
        on_delete=models.CASCADE,
        related_name='tags',
        help_text="The mentorship area this tag belongs to"
    )
    name = models.CharField(
        max_length=100,
        help_text="Tag name (e.g., React, Python, Figma)"
    )
    description = models.TextField(
        blank=True,
        help_text="Brief description of this skill/tool"
    )
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Skill Tag"
        verbose_name_plural = "Skill Tags"
        ordering = ['area', 'order', 'name']
        unique_together = ['area', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.area.name})"


class Interviewer(models.Model):
    """
    Staff members who are designated to interview mentor applicants.
    Only staff members (is_staff=True) can be interviewers.
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='interviewer_profile',
        limit_choices_to={'is_staff': True},
        help_text="The staff member who will conduct interviews"
    )
    bio = models.TextField(
        blank=True,
        help_text="Brief bio about the interviewer"
    )
    areas = models.ManyToManyField(
        MentorshipArea,
        related_name='interviewers',
        blank=True,
        help_text="Mentorship areas this interviewer specializes in"
    )
    profile_image = models.URLField(
        blank=True,
        null=True,
        help_text="Profile image URL"
    )
    max_daily_interviews = models.PositiveIntegerField(
        default=5,
        help_text="Maximum interviews this person can conduct per day"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this interviewer is currently accepting bookings"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Interviewer"
        verbose_name_plural = "Interviewers"
        ordering = ['user__first_name', 'user__last_name']
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"
    
    def clean(self):
        if not self.user.is_staff:
            raise ValidationError("Only staff members can be interviewers.")
    
    @property
    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}"


class InterviewerSchedule(models.Model):
    """
    Available time slots for interviewers.
    Mentor applicants can book these slots for their interviews.
    """
    DAY_CHOICES = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ]
    
    INTERVIEW_TYPE_CHOICES = [
        ('physical', 'Physical (In-Person)'),
        ('virtual', 'Virtual (Online)'),
        ('hybrid', 'Hybrid'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    interviewer = models.ForeignKey(
        Interviewer,
        on_delete=models.CASCADE,
        related_name='schedules',
        help_text="The interviewer this schedule belongs to"
    )
    
    # Schedule details
    date = models.DateField(
        help_text="The specific date for this interview slot"
    )
    start_time = models.TimeField(
        help_text="Start time of the available slot"
    )
    end_time = models.TimeField(
        help_text="End time of the available slot"
    )
    interview_type = models.CharField(
        max_length=10,
        choices=INTERVIEW_TYPE_CHOICES,
        default='physical',
        help_text="Type of interview"
    )
    
    # Location/Link
    location = models.CharField(
        max_length=255,
        blank=True,
        help_text="Physical location for in-person interviews"
    )
    meeting_link = models.URLField(
        blank=True,
        null=True,
        help_text="Meeting link for virtual interviews"
    )
    
    # Availability
    is_booked = models.BooleanField(
        default=False,
        help_text="Whether this slot has been booked"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this slot is available for booking"
    )
    
    # Notes
    notes = models.TextField(
        blank=True,
        help_text="Any additional notes about this schedule"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Interviewer Schedule"
        verbose_name_plural = "Interviewer Schedules"
        ordering = ['date', 'start_time']
        indexes = [
            models.Index(fields=['date', 'is_booked', 'is_active']),
            models.Index(fields=['interviewer', 'date']),
        ]
    
    def __str__(self):
        return f"{self.interviewer.full_name} - {self.date} ({self.start_time} - {self.end_time})"
    
    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time.")
        if self.date < timezone.now().date():
            raise ValidationError("Schedule date cannot be in the past.")
    
    @property
    def is_available(self):
        return self.is_active and not self.is_booked and self.date >= timezone.now().date()
    
    @property
    def duration_minutes(self):
        from datetime import datetime
        start = datetime.combine(self.date, self.start_time)
        end = datetime.combine(self.date, self.end_time)
        return int((end - start).total_seconds() / 60)


class MentorApplication(models.Model):
    """
    Application to become a mentor.
    Contains all information required from mentor applicants.
    """
    APPLICATION_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('interview_scheduled', 'Interview Scheduled'),
        ('interview_completed', 'Interview Completed'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    ]
    
    INCENTIVE_CHOICES = [
        ('certification', 'Certification'),
        ('publication', 'Publication (Subject to T&C)'),
        ('food_refreshments', 'Food & Refreshments'),
        ('monetary', 'Monetary Compensation'),
        ('recognition', 'Recognition by Society'),
        ('none', 'No Incentive'),
    ]
    
    SESSION_TYPE_CHOICES = [
        ('physical', 'Physical'),
        ('virtual', 'Virtual'),
        ('hybrid', 'Hybrid'),
    ]
    
    MENTEE_CAPACITY_CHOICES = [
        ('1-5', '1-5 Mentees'),
        ('6-10', '6-10 Mentees'),
        ('11-20', '11-20 Mentees'),
        ('20+', '20+ Mentees'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    applicant = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='mentor_applications',
        help_text="The student applying to be a mentor"
    )
    
    # Status
    status = models.CharField(
        max_length=25,
        choices=APPLICATION_STATUS_CHOICES,
        default='draft'
    )
    
    # Mentorship Areas (can select multiple)
    areas = models.ManyToManyField(
        MentorshipArea,
        related_name='mentor_applications',
        help_text="Mentorship areas the applicant wants to mentor in"
    )
    
    # Skills & Experience
    skills = models.ManyToManyField(
        SkillTag,
        related_name='mentor_applications',
        blank=True,
        help_text="Skills and experience tags"
    )
    additional_skills = models.TextField(
        blank=True,
        help_text="Additional skills not covered by tags"
    )
    experience_description = models.TextField(
        blank=True,
        help_text="Describe your experience in the selected areas"
    )
    
    # Incentive Preferences (can select multiple)
    incentive_preferences = models.JSONField(
        default=list,
        help_text="List of preferred incentives"
    )
    
    # Session Preferences
    session_type = models.CharField(
        max_length=10,
        choices=SESSION_TYPE_CHOICES,
        default='hybrid'
    )
    
    # Availability
    available_days = models.JSONField(
        default=list,
        help_text="Days of the week available for mentoring (e.g., ['monday', 'wednesday'])"
    )
    sessions_per_semester = models.PositiveIntegerField(
        default=1,
        help_text="How many sessions they can do per semester"
    )
    available_time_start = models.TimeField(
        null=True,
        blank=True,
        help_text="Start of available time range"
    )
    available_time_end = models.TimeField(
        null=True,
        blank=True,
        help_text="End of available time range"
    )
    
    # Capacity
    mentee_capacity = models.CharField(
        max_length=10,
        choices=MENTEE_CAPACITY_CHOICES,
        default='1-5'
    )
    
    # Resource Needs
    needs_classroom = models.BooleanField(
        default=False,
        help_text="Whether they need a classroom for meetings"
    )
    needs_data_support = models.BooleanField(
        default=False,
        help_text="Whether they need internet/data support"
    )
    other_resources = models.TextField(
        blank=True,
        help_text="Other resources needed for smooth mentoring"
    )
    
    # Interview
    assigned_interviewer = models.ForeignKey(
        Interviewer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_applications',
        help_text="Interviewer assigned to this application"
    )
    interview_schedule = models.OneToOneField(
        InterviewerSchedule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='booked_application',
        help_text="The scheduled interview slot"
    )
    interview_link = models.URLField(
        blank=True,
        null=True,
        help_text="Link sent by interviewer for virtual interview"
    )
    interview_notes = models.TextField(
        blank=True,
        help_text="Notes from the interview"
    )
    interview_completed_at = models.DateTimeField(
        null=True,
        blank=True
    )
    
    # Approval
    approved_by = models.ForeignKey(
        Interviewer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_applications',
        help_text="The interviewer who approved/rejected this application"
    )
    approval_notes = models.TextField(
        blank=True,
        help_text="Notes from approval/rejection"
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Timestamps
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Mentor Application"
        verbose_name_plural = "Mentor Applications"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['applicant', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"Mentor Application - {self.applicant.first_name} {self.applicant.last_name}"
    
    def clean(self):
        # Check if applicant is not a first-year student
        if self.applicant.get_year() == 1:
            raise ValidationError(
                "First-year students are not eligible to apply as mentors. "
                "You can apply starting from your second year."
            )
    
    def save(self, *args, **kwargs):
        # Validate eligibility
        if self.pk is None:  # Only on creation
            self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def is_eligible(self):
        """Check if applicant is eligible to be a mentor"""
        return self.applicant.get_year() >= 2
    
    @property
    def is_pending_interview(self):
        return self.status in ['submitted', 'interview_scheduled']
    
    @property
    def is_approved(self):
        return self.status == 'approved'
    
    def schedule_interview(self, schedule: InterviewerSchedule):
        """Book an interview slot"""
        if not schedule.is_available:
            raise ValidationError("This interview slot is not available.")
        
        self.interview_schedule = schedule
        self.assigned_interviewer = schedule.interviewer
        self.status = 'interview_scheduled'
        schedule.is_booked = True
        schedule.save()
        self.save()
    
    def complete_interview(self, notes=""):
        """Mark interview as completed"""
        self.status = 'interview_completed'
        self.interview_notes = notes
        self.interview_completed_at = timezone.now()
        self.save()
    
    def approve(self, interviewer: Interviewer, notes=""):
        """Approve the mentor application"""
        # Only the assigned interviewer can approve
        if self.assigned_interviewer != interviewer:
            raise ValidationError(
                "Only the assigned interviewer can approve this application."
            )
        
        self.status = 'approved'
        self.approved_by = interviewer
        self.approval_notes = notes
        self.approved_at = timezone.now()
        self.save()
    
    def reject(self, interviewer: Interviewer, reason=""):
        """Reject the mentor application"""
        # Only the assigned interviewer can reject
        if self.assigned_interviewer != interviewer:
            raise ValidationError(
                "Only the assigned interviewer can reject this application."
            )
        
        self.status = 'rejected'
        self.approved_by = interviewer
        self.rejection_reason = reason
        self.rejected_at = timezone.now()
        self.save()


class ApprovedMentor(models.Model):
    """
    Approved mentors who can accept mentees.
    Created when a MentorApplication is approved.
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='mentor_profile'
    )
    application = models.OneToOneField(
        MentorApplication,
        on_delete=models.CASCADE,
        related_name='approved_profile'
    )
    
    # Copied from application for easy access
    areas = models.ManyToManyField(
        MentorshipArea,
        related_name='approved_mentors'
    )
    skills = models.ManyToManyField(
        SkillTag,
        related_name='approved_mentors',
        blank=True
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this mentor is currently accepting mentees"
    )
    is_accepting_mentees = models.BooleanField(
        default=True,
        help_text="Whether this mentor is open to new mentee applications"
    )
    
    # Stats
    total_mentees = models.PositiveIntegerField(default=0)
    current_mentees = models.PositiveIntegerField(default=0)
    completed_sessions = models.PositiveIntegerField(default=0)
    
    # Rating (can be expanded later)
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00
    )
    total_ratings = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Approved Mentor"
        verbose_name_plural = "Approved Mentors"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Mentor: {self.user.first_name} {self.user.last_name}"
    
    @property
    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}"
    
    @property
    def available_slots(self):
        """Calculate remaining mentee slots"""
        capacity = self.application.mentee_capacity
        capacity_map = {'1-5': 5, '6-10': 10, '11-20': 20, '20+': 50}
        max_mentees = capacity_map.get(capacity, 5)
        return max(0, max_mentees - self.current_mentees)
    
    @property
    def has_available_slots(self):
        return self.available_slots > 0 and self.is_accepting_mentees


class MenteeApplication(models.Model):
    """
    Application from a student to become a mentee of a specific mentor.
    """
    APPLICATION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    applicant = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='mentee_applications',
        help_text="The student applying to be a mentee"
    )
    mentor = models.ForeignKey(
        ApprovedMentor,
        on_delete=models.CASCADE,
        related_name='mentee_applications',
        help_text="The mentor being applied to"
    )
    
    # Status
    status = models.CharField(
        max_length=15,
        choices=APPLICATION_STATUS_CHOICES,
        default='pending'
    )
    
    # Selected Area
    area = models.ForeignKey(
        MentorshipArea,
        on_delete=models.CASCADE,
        related_name='mentee_applications',
        help_text="The area the mentee wants guidance in"
    )
    
    # Mentee's current skills (optional)
    current_skills = models.ManyToManyField(
        SkillTag,
        related_name='mentee_current_skills',
        blank=True,
        help_text="Skills the mentee already has"
    )
    skills_description = models.TextField(
        blank=True,
        help_text="Description of current skills/experience"
    )
    
    # Skills to learn
    skills_to_learn = models.ManyToManyField(
        SkillTag,
        related_name='mentee_learning_goals',
        blank=True,
        help_text="Skills the mentee wishes to learn"
    )
    learning_goals = models.TextField(
        blank=True,
        help_text="Specific learning goals"
    )
    
    # Optional offerings to mentor
    OFFERING_CHOICES = [
        ('monetary', 'Monetary Support'),
        ('food', 'Food & Refreshments'),
        ('other', 'Other Support'),
        ('none', 'No Offering'),
    ]
    offering_type = models.CharField(
        max_length=10,
        choices=OFFERING_CHOICES,
        default='none',
        help_text="Optional offering to the mentor"
    )
    offering_description = models.TextField(
        blank=True,
        help_text="Description of what they wish to offer"
    )
    offering_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Amount for monetary offerings (processed through payment system)"
    )
    
    # Personal message
    message = models.TextField(
        blank=True,
        help_text="Personal message to the mentor"
    )
    
    # Response from mentor
    mentor_response = models.TextField(
        blank=True,
        help_text="Response message from the mentor"
    )
    responded_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Mentee Application"
        verbose_name_plural = "Mentee Applications"
        ordering = ['-created_at']
        unique_together = ['applicant', 'mentor', 'area']
        indexes = [
            models.Index(fields=['mentor', 'status']),
            models.Index(fields=['applicant', 'status']),
        ]
    
    def __str__(self):
        return f"Mentee Application - {self.applicant.first_name} to {self.mentor.full_name}"
    
    def accept(self, response_message=""):
        """Accept the mentee application"""
        if not self.mentor.has_available_slots:
            raise ValidationError("Mentor has no available slots.")
        
        self.status = 'accepted'
        self.mentor_response = response_message
        self.responded_at = timezone.now()
        self.save()
        
        # Update mentor stats
        self.mentor.current_mentees += 1
        self.mentor.total_mentees += 1
        self.mentor.save()
        
        # Create mentorship relationship
        MentorshipRelationship.objects.create(
            mentor=self.mentor,
            mentee=self.applicant,
            area=self.area,
            from_application=self
        )
    
    def reject(self, response_message=""):
        """Reject the mentee application"""
        self.status = 'rejected'
        self.mentor_response = response_message
        self.responded_at = timezone.now()
        self.save()
    
    def withdraw(self):
        """Withdraw the mentee application"""
        self.status = 'withdrawn'
        self.save()


class MentorshipRelationship(models.Model):
    """
    Active mentorship relationship between a mentor and mentee.
    Created when a mentee application is accepted.
    """
    RELATIONSHIP_STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('terminated', 'Terminated'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    mentor = models.ForeignKey(
        ApprovedMentor,
        on_delete=models.CASCADE,
        related_name='mentorship_relationships'
    )
    mentee = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='mentorship_relationships'
    )
    area = models.ForeignKey(
        MentorshipArea,
        on_delete=models.CASCADE,
        related_name='mentorship_relationships'
    )
    from_application = models.OneToOneField(
        MenteeApplication,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resulting_relationship'
    )
    
    # Status
    status = models.CharField(
        max_length=15,
        choices=RELATIONSHIP_STATUS_CHOICES,
        default='active'
    )
    
    # Sessions tracking
    sessions_completed = models.PositiveIntegerField(default=0)
    last_session_date = models.DateField(null=True, blank=True)
    next_session_date = models.DateField(null=True, blank=True)
    
    # Notes
    mentor_notes = models.TextField(
        blank=True,
        help_text="Private notes from the mentor"
    )
    
    # Timestamps
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Mentorship Relationship"
        verbose_name_plural = "Mentorship Relationships"
        ordering = ['-started_at']
        unique_together = ['mentor', 'mentee', 'area']
    
    def __str__(self):
        return f"{self.mentor.full_name} -> {self.mentee.first_name} ({self.area.name})"
    
    def complete(self):
        """Mark the mentorship as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
        
        # Update mentor stats
        self.mentor.current_mentees -= 1
        self.mentor.completed_sessions += self.sessions_completed
        self.mentor.save()
    
    def terminate(self, reason=""):
        """Terminate the mentorship"""
        self.status = 'terminated'
        self.completed_at = timezone.now()
        self.save()
        
        # Update mentor stats
        self.mentor.current_mentees -= 1
        self.mentor.save()
    
    def record_session(self, notes=""):
        """Record a completed session"""
        self.sessions_completed += 1
        self.last_session_date = timezone.now().date()
        self.save()


class MentorshipSession(models.Model):
    """
    Individual mentoring sessions between mentor and mentee.
    """
    SESSION_TYPE_CHOICES = [
        ('physical', 'Physical'),
        ('virtual', 'Virtual'),
    ]
    
    SESSION_STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rescheduled', 'Rescheduled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    relationship = models.ForeignKey(
        MentorshipRelationship,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    
    # Session details
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    session_type = models.CharField(
        max_length=10,
        choices=SESSION_TYPE_CHOICES
    )
    
    # Location
    location = models.CharField(max_length=255, blank=True)
    meeting_link = models.URLField(blank=True, null=True)
    
    # Status
    status = models.CharField(
        max_length=15,
        choices=SESSION_STATUS_CHOICES,
        default='scheduled'
    )
    
    # Notes
    agenda = models.TextField(blank=True)
    mentor_notes = models.TextField(blank=True)
    mentee_feedback = models.TextField(blank=True)
    
    # Rating (from mentee)
    rating = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Rating from 1-5"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Mentorship Session"
        verbose_name_plural = "Mentorship Sessions"
        ordering = ['-date', '-start_time']
    
    def __str__(self):
        return f"Session: {self.relationship} on {self.date}"
    
    def complete(self, mentor_notes=""):
        """Mark session as completed by mentor"""
        self.status = 'completed'
        if mentor_notes:
            self.mentor_notes = mentor_notes
        self.save()
        
        # Update relationship stats
        self.relationship.record_session()
    
    def add_mentee_review(self, feedback="", rating=None):
        """Add mentee's feedback and rating to a completed session"""
        if self.status != 'completed':
            raise ValueError("Can only review completed sessions")
        if feedback:
            self.mentee_feedback = feedback
        if rating:
            self.rating = rating
        self.save()


class MentorPayment(models.Model):
    """
    Tracks payments made to mentors from mentees through the payment system.
    Properly linked to the payments.Transaction model for full integration.
    """
    PAYMENT_TYPE_CHOICES = [
        ('offering', 'Mentee Offering'),
        ('incentive', 'Society Incentive'),
        ('bonus', 'Bonus'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    mentor = models.ForeignKey(
        ApprovedMentor,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    mentee = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='mentor_payments',
        null=True,
        blank=True
    )
    relationship = models.ForeignKey(
        MentorshipRelationship,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments'
    )
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type = models.CharField(
        max_length=15,
        choices=PAYMENT_TYPE_CHOICES
    )
    status = models.CharField(
        max_length=15,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    
    # ===== LINKED TO PAYMENT SYSTEM =====
    # Direct ForeignKey to Transaction model for full integration
    transaction = models.ForeignKey(
        'payments.Transaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mentor_payments',
        help_text="Linked transaction from payments system"
    )
    
    # Keep reference as backup/quick lookup
    transaction_reference = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        help_text="Transaction reference for quick lookup"
    )
    
    description = models.TextField(blank=True)
    
    # Callback URL for payment completion
    callback_url = models.URLField(
        blank=True,
        null=True,
        help_text="URL to redirect after payment"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Mentor Payment"
        verbose_name_plural = "Mentor Payments"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['mentor', 'status']),
            models.Index(fields=['mentee', 'status']),
        ]
    
    def __str__(self):
        return f"Payment to {self.mentor.full_name} - GHS {self.amount}"
    
    def sync_with_transaction(self):
        """Sync status with linked transaction"""
        if self.transaction:
            status_map = {
                'success': 'completed',
                'pending': 'pending',
                'processing': 'processing',
                'failed': 'failed',
                'refunded': 'refunded',
                'cancelled': 'cancelled',
            }
            self.status = status_map.get(self.transaction.status, self.status)
            self.transaction_reference = self.transaction.reference
            if self.transaction.status == 'success' and not self.completed_at:
                self.completed_at = self.transaction.completed_at or timezone.now()
            self.save()
    
    @property
    def is_paid(self):
        """Check if payment is completed"""
        return self.status == 'completed'
    
    @property
    def can_be_refunded(self):
        """Check if payment can be refunded"""
        if self.transaction:
            return self.transaction.can_be_refunded
        return self.status == 'completed'
