from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from events.models import Event
import secrets
import string
from utils.media_mixins import MediaUrlMixin
from utils.dynamic_storage import DynamicStorage


def generate_access_key(length=12):
    """Generate a unique access key for authentication"""
    characters = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))


class CodeQuestEvent(models.Model):
    """
    Extends the Event model for Code Quest specific functionality
    Links to the base Event model for timeline, images, etc.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('registration_open', 'Registration Open'),
        ('grouping', 'Grouping Phase'),
        ('voting', 'Voting Phase'),
        ('development', 'Development Phase'),
        ('presentation', 'Presentation Day'),
        ('completed', 'Completed'),
    ]
    
    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name='codequest')
    academic_year = models.CharField(max_length=20, help_text="e.g., 2024/2025")
    semester = models.CharField(max_length=50, help_text="e.g., Second Semester")
    course_code = models.CharField(max_length=20, help_text="e.g., DCIT 208")
    course_name = models.CharField(max_length=200, help_text="e.g., Mobile Application Development")
    
    # Dates
    registration_start_date = models.DateTimeField()
    registration_end_date = models.DateTimeField()
    grouping_date = models.DateTimeField(help_text="When groups are formed")
    voting_start_date = models.DateTimeField(help_text="PM election starts")
    voting_end_date = models.DateTimeField(help_text="PM election ends")
    project_submission_deadline = models.DateTimeField()
    presentation_date = models.DateTimeField(help_text="Final event/presentation day")
    
    # Event details
    venue_details = models.TextField(blank=True)
    max_group_size = models.IntegerField(null=True, blank=True, help_text="Maximum members per group")
    min_group_size = models.IntegerField(default=5, help_text="Minimum members per group")
    allow_self_grouping = models.BooleanField(default=False, help_text="Allow students to form their own groups")
    self_grouping_start_date = models.DateTimeField(null=True, blank=True, help_text="When self-grouping can start")
    self_grouping_end_date = models.DateTimeField(null=True, blank=True, help_text="When self-grouping ends (lockdown begins)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    def is_self_grouping_active(self):
        """Check if self-grouping is currently active (enabled and within date range)"""
        if not self.allow_self_grouping:
            return False
        
        now = timezone.now()
        
        # If start date is set, check if we've reached it
        if self.self_grouping_start_date and now < self.self_grouping_start_date:
            return False
        
        # If end date is set, check if we've passed it
        if self.self_grouping_end_date and now > self.self_grouping_end_date:
            return False
        
        return True
    
    def is_self_grouping_locked(self):
        """Check if self-grouping is locked (past end date)"""
        if not self.self_grouping_end_date:
            return False
        return timezone.now() > self.self_grouping_end_date
    
    def get_self_grouping_status(self):
        """Get detailed self-grouping status"""
        if not self.allow_self_grouping:
            return {
                'status': 'disabled',
                'message': 'Self-grouping is not enabled for this event'
            }
        
        now = timezone.now()
        
        if self.self_grouping_start_date and now < self.self_grouping_start_date:
            return {
                'status': 'not_started',
                'message': 'Self-grouping has not started yet',
                'starts_at': self.self_grouping_start_date.isoformat()
            }
        
        if self.self_grouping_end_date and now > self.self_grouping_end_date:
            return {
                'status': 'locked',
                'message': 'Self-grouping period has ended. Teams are now locked.',
                'ended_at': self.self_grouping_end_date.isoformat()
            }
        
        return {
            'status': 'active',
            'message': 'Self-grouping is active',
            'ends_at': self.self_grouping_end_date.isoformat() if self.self_grouping_end_date else None
        }
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Code Quest Event"
        verbose_name_plural = "Code Quest Events"
        ordering = ['-presentation_date']
    
    def __str__(self):
        return f"Code Quest {self.academic_year} - {self.semester}"


class CodeQuestParticipant(models.Model):
    """
    Students participating in Code Quest
    Categories: Regular Year 2 students and deferred students from other years
    """
    YEAR_CHOICES = [
        (2, 'Year 2'),
        (3, 'Year 3'),
        (4, 'Year 4'),
    ]
    
    ROLE_CHOICES = [
        ('Frontend', 'Frontend Developer'),
        ('Backend', 'Backend Developer'),
        ('UI/UX', 'UI/UX Designer'),
        ('Data Science', 'Data Scientist'),
        ('DevOps', 'DevOps Engineer'),
        ('QA', 'Quality Assurance'),
        ('Mobile', 'Mobile Developer'),
        ('Other', 'Other'),
    ]
    
    event = models.ForeignKey(CodeQuestEvent, on_delete=models.CASCADE, related_name='participants')
    student_id = models.CharField(max_length=50, help_text="Index number")
    student_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, blank=True)
    year = models.IntegerField(choices=YEAR_CHOICES, default=2)
    is_deferred = models.BooleanField(default=False, help_text="Is this student deferred from previous year?")
    preferred_role = models.CharField(max_length=50, choices=ROLE_CHOICES, blank=True)
    skills = models.TextField(blank=True, help_text="List of skills/technologies known")
    
    # Group assignment
    group = models.ForeignKey('CodeQuestGroup', on_delete=models.SET_NULL, null=True, blank=True, related_name='members')
    
    # Authentication
    access_key = models.CharField(max_length=20, unique=True, default=generate_access_key)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='codequest_participant_registrations',
        help_text="Linked user account (auto-assigned on registration)"
    )
    
    registration_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Code Quest Participant"
        verbose_name_plural = "Code Quest Participants"
        unique_together = [['event', 'student_id']]
        ordering = ['student_name']
    
    def __str__(self):
        return f"{self.student_name} ({self.student_id})"
    
    def save(self, *args, **kwargs):
        if not self.access_key:
            self.access_key = generate_access_key()
        super().save(*args, **kwargs)


class CodeQuestGroup(models.Model):
    """
    Groups of students working together on a project
    """
    CATEGORY_CHOICES = [
        ('regular', 'Regular Students'),
        ('deferred_mixed', 'Mixed (Regular + Deferred)'),
        ('deferred_only', 'Deferred Students Only'),
    ]
    
    event = models.ForeignKey(CodeQuestEvent, on_delete=models.CASCADE, related_name='groups')
    group_number = models.CharField(max_length=50, help_text="e.g., Group 1, Team Alpha")
    group_name = models.CharField(max_length=200, blank=True, help_text="Custom group name (optional)")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='regular')
    formation_date = models.DateTimeField(auto_now_add=True)
    
    # Leadership
    project_manager = models.ForeignKey(
        CodeQuestParticipant, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='managed_groups'
    )
    
    # Consultant assignment
    consultant = models.ForeignKey(
        'CodeQuestConsultant', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_groups'
    )
    
    is_complete = models.BooleanField(default=False, help_text="Are all roles assigned?")
    
    class Meta:
        verbose_name = "Code Quest Group"
        verbose_name_plural = "Code Quest Groups"
        unique_together = [['event', 'group_number']]
        ordering = ['group_number']
    
    def __str__(self):
        return f"{self.group_number} - {self.event.academic_year}"
    
    def member_count(self):
        return self.members.count()
    member_count.short_description = "Members"


class ProjectManagerCandidate(models.Model):
    """
    Students who nominate themselves as Project Manager candidates
    """
    participant = models.ForeignKey(CodeQuestParticipant, on_delete=models.CASCADE, related_name='pm_nominations')
    group = models.ForeignKey(CodeQuestGroup, on_delete=models.CASCADE, related_name='pm_candidates')
    nomination_statement = models.TextField(help_text="Why do you want to be Project Manager?")
    nomination_date = models.DateTimeField(auto_now_add=True)
    vote_count = models.IntegerField(default=0)
    is_winner = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Project Manager Candidate"
        verbose_name_plural = "Project Manager Candidates"
        unique_together = [['participant', 'group']]
        ordering = ['-vote_count', 'nomination_date']
    
    def __str__(self):
        return f"{self.participant.student_name} - {self.group.group_number}"


class ProjectManagerVote(models.Model):
    """
    Votes cast by group members for Project Manager candidates
    One vote per person per group
    """
    voter = models.ForeignKey(CodeQuestParticipant, on_delete=models.CASCADE, related_name='pm_votes')
    candidate = models.ForeignKey(ProjectManagerCandidate, on_delete=models.CASCADE, related_name='votes')
    group = models.ForeignKey(CodeQuestGroup, on_delete=models.CASCADE, related_name='pm_votes')
    vote_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Project Manager Vote"
        verbose_name_plural = "Project Manager Votes"
        unique_together = [['voter', 'group']]
        ordering = ['-vote_date']
    
    def __str__(self):
        return f"{self.voter.student_name} voted for {self.candidate.participant.student_name}"


class GroupMemberRole(models.Model):
    """
    Roles assigned to group members by Project Manager
    """
    ROLE_CHOICES = [
        ('Frontend', 'Frontend Developer'),
        ('Backend', 'Backend Developer'),
        ('UI/UX', 'UI/UX Designer'),
        ('Data Science', 'Data Scientist'),
        ('DevOps', 'DevOps Engineer'),
        ('QA', 'Quality Assurance'),
        ('Mobile', 'Mobile Developer'),
        ('Other', 'Other'),
    ]
    
    participant = models.ForeignKey(CodeQuestParticipant, on_delete=models.CASCADE, related_name='assigned_roles')
    group = models.ForeignKey(CodeQuestGroup, on_delete=models.CASCADE, related_name='member_roles')
    role_type = models.CharField(max_length=50, choices=ROLE_CHOICES)
    assigned_by = models.ForeignKey(
        CodeQuestParticipant, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='roles_assigned_by_me'
    )
    assigned_date = models.DateTimeField(auto_now_add=True)
    is_lead = models.BooleanField(default=False, help_text="Is this person the lead for this role?")
    
    class Meta:
        verbose_name = "Group Member Role"
        verbose_name_plural = "Group Member Roles"
        ordering = ['group', 'role_type']
    
    def __str__(self):
        lead_tag = " (Lead)" if self.is_lead else ""
        return f"{self.participant.student_name} - {self.role_type}{lead_tag}"


class CodeQuestProject(MediaUrlMixin, models.Model):
    """
    Project/App details for each group
    """
    # Media URL field mappings for auto-population
    MEDIA_URL_FIELDS = {
        'app_logo': 'app_logo_url',
    }
    
    group = models.OneToOneField(CodeQuestGroup, on_delete=models.CASCADE, related_name='project')
    app_name = models.CharField(max_length=200, help_text="Name of the app")
    app_description = models.TextField(help_text="What does the app do?")
    app_logo = models.ImageField(storage=DynamicStorage(), upload_to='codequest/logos/', blank=True, null=True)
    app_logo_url = models.URLField(
        blank=True,
        null=True,
        help_text="Alternative: Provide app logo URL instead of uploading"
    )
    inspiration_app = models.CharField(max_length=200, blank=True, help_text="Reference app (e.g., WhatsApp)")
    
    # Tech stack (stored as JSON)
    tech_stack_frontend = models.JSONField(default=list, blank=True, help_text="Frontend technologies")
    tech_stack_backend = models.JSONField(default=list, blank=True, help_text="Backend technologies")
    
    # Links
    repository_url = models.URLField(blank=True, help_text="GitHub/GitLab repository")
    demo_video_url = models.URLField(blank=True, help_text="Demo video link")
    live_demo_url = models.URLField(blank=True, help_text="Live app demo (optional)")
    documentation_url = models.URLField(blank=True, help_text="Documentation link")
    
    # Submission
    submission_date = models.DateTimeField(null=True, blank=True)
    is_approved = models.BooleanField(default=False, help_text="Admin approval")
    admin_feedback = models.TextField(blank=True, help_text="Admin comments/feedback")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Code Quest Project"
        verbose_name_plural = "Code Quest Projects"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.app_name} - {self.group.group_number}"


class CodeQuestConsultant(MediaUrlMixin, models.Model):
    """
    Upper-year student consultants (3rd/4th year) assigned to guide groups
    """
    # Media URL field mappings for auto-population
    MEDIA_URL_FIELDS = {
        'profile_image': 'profile_image_url',
    }
    
    YEAR_CHOICES = [
        ('Y3', 'Year 3 (3rd Year)'),
        ('Y4', 'Year 4 (4th Year)'),
    ]
    
    event = models.ForeignKey(CodeQuestEvent, on_delete=models.CASCADE, related_name='consultants')
    student_name = models.CharField(max_length=200)
    student_id = models.CharField(max_length=20, default='TEMP000', help_text="Student ID number")
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, blank=True)
    year = models.CharField(max_length=4, choices=YEAR_CHOICES, default='Y3', help_text="Academic year")
    expertise_areas = models.JSONField(default=list, help_text="Areas of expertise (Frontend, Backend, etc.)")
    bio = models.TextField(blank=True, help_text="Brief introduction and skills")
    profile_image = models.ImageField(storage=DynamicStorage(), upload_to='codequest/consultants/', blank=True, null=True)
    profile_image_url = models.URLField(
        blank=True,
        null=True,
        help_text="Alternative: Provide profile image URL instead of uploading"
    )
    
    # Authentication
    access_key = models.CharField(max_length=20, unique=True, default=generate_access_key)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='codequest_consultant_registrations',
        help_text="Linked user account (auto-assigned on registration)"
    )
    
    registration_date = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False, help_text="Admin approval")
    
    class Meta:
        verbose_name = "Code Quest Consultant"
        verbose_name_plural = "Code Quest Consultants"
        ordering = ['student_name']
    
    def __str__(self):
        return f"{self.student_name} ({self.student_id}) - {self.get_year_display()}"
    
    def save(self, *args, **kwargs):
        if not self.access_key:
            self.access_key = generate_access_key()
        super().save(*args, **kwargs)


class ConsultantGroupAssignment(models.Model):
    """
    Assignment of consultants to groups (many-to-many relationship with metadata)
    """
    consultant = models.ForeignKey(CodeQuestConsultant, on_delete=models.CASCADE, related_name='group_assignments')
    group = models.ForeignKey(CodeQuestGroup, on_delete=models.CASCADE, related_name='consultant_assignments')
    assigned_date = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Consultant Group Assignment"
        verbose_name_plural = "Consultant Group Assignments"
        unique_together = [['consultant', 'group']]
        ordering = ['-assigned_date']
    
    def __str__(self):
        return f"{self.consultant.name} → {self.group.group_number}"


class ScoringCriteria(models.Model):
    """
    Scoring criteria defined by admin for evaluating projects
    """
    event = models.ForeignKey(CodeQuestEvent, on_delete=models.CASCADE, related_name='scoring_criteria')
    criteria_name = models.CharField(max_length=200, help_text="e.g., UI/UX Design, Code Quality")
    criteria_description = models.TextField(blank=True)
    max_points = models.IntegerField(default=100, validators=[MinValueValidator(1)])
    percentage_weight = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=10.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage weight in final score"
    )
    order = models.IntegerField(default=0, help_text="Display order")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Scoring Criteria"
        verbose_name_plural = "Scoring Criteria"
        ordering = ['event', 'order', 'criteria_name']
    
    def __str__(self):
        return f"{self.criteria_name} ({self.percentage_weight}%)"


class CodeQuestFacilitator(models.Model):
    """
    Judges/facilitators who score projects on presentation day
    """
    event = models.ForeignKey(CodeQuestEvent, on_delete=models.CASCADE, related_name='facilitators')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=200)
    email = models.EmailField()
    role_title = models.CharField(max_length=200, blank=True, help_text="e.g., Judge, Technical Evaluator")
    access_code = models.CharField(max_length=20, unique=True, default=generate_access_key)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Code Quest Facilitator"
        verbose_name_plural = "Code Quest Facilitators"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.role_title})"
    
    def save(self, *args, **kwargs):
        if not self.access_code:
            self.access_code = generate_access_key()
        super().save(*args, **kwargs)


class ProjectScore(models.Model):
    """
    Individual scores given by facilitators for each criteria
    """
    project = models.ForeignKey(CodeQuestProject, on_delete=models.CASCADE, related_name='scores')
    facilitator = models.ForeignKey(CodeQuestFacilitator, on_delete=models.CASCADE, related_name='scores_given')
    criteria = models.ForeignKey(ScoringCriteria, on_delete=models.CASCADE, related_name='project_scores')
    score = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)])
    comments = models.TextField(blank=True, help_text="Optional feedback")
    scored_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Project Score"
        verbose_name_plural = "Project Scores"
        unique_together = [['project', 'facilitator', 'criteria']]
        ordering = ['-scored_date']
    
    def __str__(self):
        return f"{self.project.app_name} - {self.criteria.criteria_name}: {self.score}"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.score > self.criteria.max_points:
            raise ValidationError(f'Score cannot exceed {self.criteria.max_points} for this criteria')


class FinalProjectScore(models.Model):
    """
    Calculated final scores and rankings for each project
    """
    project = models.OneToOneField(CodeQuestProject, on_delete=models.CASCADE, related_name='final_score')
    total_score = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    average_score = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    rank = models.IntegerField(null=True, blank=True, help_text="Project ranking")
    is_published = models.BooleanField(default=False, help_text="Show results to participants?")
    published_date = models.DateTimeField(null=True, blank=True)
    calculation_date = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Final Project Score"
        verbose_name_plural = "Final Project Scores"
        ordering = ['-total_score', 'rank']
    
    def __str__(self):
        rank_display = f"#{self.rank}" if self.rank else "Unranked"
        return f"{self.project.app_name} - {rank_display} ({self.total_score})"


class ProjectTask(models.Model):
    """
    Tasks assigned by Project Manager to team members
    """
    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('Todo', 'To Do'),
        ('In Progress', 'In Progress'),
        ('Review', 'In Review'),
        ('Completed', 'Completed'),
    ]
    
    project = models.ForeignKey(CodeQuestProject, on_delete=models.CASCADE, related_name='tasks')
    task_title = models.CharField(max_length=200)
    task_description = models.TextField()
    assigned_to = models.ForeignKey(
        CodeQuestParticipant, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_tasks'
    )
    assigned_by = models.ForeignKey(
        CodeQuestParticipant, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='tasks_assigned_by_me'
    )
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Todo')
    due_date = models.DateTimeField(null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    completed_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Project Task"
        verbose_name_plural = "Project Tasks"
        ordering = ['-priority', 'due_date', '-created_date']
    
    def __str__(self):
        return f"{self.task_title} - {self.status}"


# ============================================================
# SELF-GROUPING MODELS
# ============================================================

class SelfGroupingTeam(models.Model):
    """
    Temporary team formed during self-grouping phase.
    When finalized, this becomes an official CodeQuestGroup.
    """
    STATUS_CHOICES = [
        ('forming', 'Forming'),
        ('ready', 'Ready to Finalize'),
        ('finalized', 'Finalized'),
        ('disbanded', 'Disbanded'),
    ]
    
    event = models.ForeignKey(CodeQuestEvent, on_delete=models.CASCADE, related_name='self_grouping_teams')
    team_name = models.CharField(max_length=200, blank=True, help_text="Optional team name")
    creator = models.ForeignKey(
        CodeQuestParticipant,
        on_delete=models.CASCADE,
        related_name='created_teams',
        help_text="Participant who created this team"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='forming')
    
    # When finalized, link to the official group
    finalized_group = models.OneToOneField(
        CodeQuestGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='source_self_grouping_team'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    finalized_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Self-Grouping Team"
        verbose_name_plural = "Self-Grouping Teams"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.team_name or f'Team by {self.creator.student_name}'} ({self.get_status_display()})"
    
    def member_count(self):
        """Count confirmed members including creator"""
        return self.memberships.filter(status='accepted').count()
    
    def can_add_members(self):
        """Check if team can accept more members"""
        max_size = self.event.max_group_size
        if not max_size:
            return True
        return self.member_count() < max_size
    
    def is_ready_to_finalize(self):
        """Check if team meets minimum size requirement"""
        min_size = self.event.min_group_size or 5
        return self.member_count() >= min_size


class SelfGroupingMembership(models.Model):
    """
    Membership in a self-grouping team.
    Tracks who is in the team and their status.
    """
    STATUS_CHOICES = [
        ('accepted', 'Accepted'),  # Creator auto-accepts, others accept invitation
        ('left', 'Left Team'),
    ]
    
    team = models.ForeignKey(SelfGroupingTeam, on_delete=models.CASCADE, related_name='memberships')
    participant = models.ForeignKey(
        CodeQuestParticipant,
        on_delete=models.CASCADE,
        related_name='team_memberships'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='accepted')
    is_creator = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Self-Grouping Membership"
        verbose_name_plural = "Self-Grouping Memberships"
        unique_together = [['team', 'participant']]
        ordering = ['is_creator', 'joined_at']
    
    def __str__(self):
        role = "Creator" if self.is_creator else "Member"
        return f"{self.participant.student_name} - {role} ({self.get_status_display()})"


class GroupInvitation(models.Model):
    """
    Invitation sent from one participant to another to join their team.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]
    
    team = models.ForeignKey(SelfGroupingTeam, on_delete=models.CASCADE, related_name='invitations')
    sender = models.ForeignKey(
        CodeQuestParticipant,
        on_delete=models.CASCADE,
        related_name='sent_invitations',
        help_text="Participant who sent the invitation"
    )
    recipient = models.ForeignKey(
        CodeQuestParticipant,
        on_delete=models.CASCADE,
        related_name='received_invitations',
        help_text="Participant who received the invitation"
    )
    message = models.TextField(blank=True, help_text="Optional message with invitation")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Group Invitation"
        verbose_name_plural = "Group Invitations"
        ordering = ['-created_at']
        # One pending invitation per sender-recipient pair per team
        constraints = [
            models.UniqueConstraint(
                fields=['team', 'recipient'],
                condition=models.Q(status='pending'),
                name='unique_pending_invitation_per_team_recipient'
            )
        ]
    
    def __str__(self):
        return f"{self.sender.student_name} → {self.recipient.student_name} ({self.get_status_display()})"
    
    def is_expired(self):
        """Check if invitation has expired (e.g., 7 days)"""
        from django.utils import timezone
        from datetime import timedelta
        if self.status != 'pending':
            return False
        return timezone.now() > self.created_at + timedelta(days=7)


class JoinRequest(models.Model):
    """
    Request from a participant to join an existing team.
    (Opposite of invitation - participant asks to join)
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('cancelled', 'Cancelled'),
    ]
    
    team = models.ForeignKey(SelfGroupingTeam, on_delete=models.CASCADE, related_name='join_requests')
    requester = models.ForeignKey(
        CodeQuestParticipant,
        on_delete=models.CASCADE,
        related_name='join_requests_sent',
        help_text="Participant who wants to join"
    )
    message = models.TextField(blank=True, help_text="Why do you want to join this team?")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Who responded to the request (team creator or any member with permission)
    responded_by = models.ForeignKey(
        CodeQuestParticipant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='join_requests_responded'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Join Request"
        verbose_name_plural = "Join Requests"
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['team', 'requester'],
                condition=models.Q(status='pending'),
                name='unique_pending_join_request_per_team'
            )
        ]
    
    def __str__(self):
        return f"{self.requester.student_name} → {self.team} ({self.get_status_display()})"
