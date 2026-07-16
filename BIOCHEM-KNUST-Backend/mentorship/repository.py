"""
Mentorship System - Repository Layer

Repository classes for database operations.
Follows the repository pattern for clean separation of concerns.
"""

from django.db.models import Q, Count, Avg
from django.utils import timezone
from typing import Optional, List
from uuid import UUID
from mentorship.models import (
    MentorshipArea,
    SkillTag,
    Interviewer,
    InterviewerSchedule,
    MentorApplication,
    ApprovedMentor,
    MenteeApplication,
    MentorshipRelationship,
    MentorshipSession,
    MentorPayment,
)
from accounts.models import CustomUser


class MentorshipAreaRepository:
    """Repository for MentorshipArea operations"""
    model = MentorshipArea
    
    @classmethod
    def get_all_active(cls):
        """Get all active mentorship areas"""
        return cls.model.objects.filter(is_active=True).order_by('order', 'name')
    
    @classmethod
    def get_by_id(cls, area_id: UUID):
        """Get area by ID"""
        try:
            return cls.model.objects.get(id=area_id)
        except cls.model.DoesNotExist:
            return None
    
    @classmethod
    def get_by_slug(cls, slug: str):
        """Get area by slug"""
        try:
            return cls.model.objects.get(slug=slug, is_active=True)
        except cls.model.DoesNotExist:
            return None
    
    @classmethod
    def get_with_mentor_count(cls):
        """Get areas with mentor count annotation"""
        return cls.model.objects.filter(is_active=True).annotate(
            mentor_count=Count('approved_mentors', filter=Q(approved_mentors__is_active=True))
        ).order_by('order', 'name')
    
    @classmethod
    def search(cls, query: str):
        """Search areas by name or description"""
        return cls.model.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query),
            is_active=True
        )


class SkillTagRepository:
    """Repository for SkillTag operations"""
    model = SkillTag
    
    @classmethod
    def get_by_area(cls, area_id: UUID):
        """Get all active tags for an area"""
        return cls.model.objects.filter(area_id=area_id, is_active=True).order_by('order', 'name')
    
    @classmethod
    def get_by_id(cls, tag_id: UUID):
        """Get tag by ID"""
        try:
            return cls.model.objects.get(id=tag_id)
        except cls.model.DoesNotExist:
            return None
    
    @classmethod
    def search(cls, query: str, area_id: Optional[UUID] = None):
        """Search tags by name"""
        qs = cls.model.objects.filter(name__icontains=query, is_active=True)
        if area_id:
            qs = qs.filter(area_id=area_id)
        return qs
    
    @classmethod
    def get_popular_tags(cls, limit: int = 10):
        """Get most popular tags based on mentor usage"""
        return cls.model.objects.filter(is_active=True).annotate(
            usage_count=Count('mentor_applications') + Count('mentee_learning_goals')
        ).order_by('-usage_count')[:limit]


class InterviewerRepository:
    """Repository for Interviewer operations"""
    model = Interviewer
    
    @classmethod
    def get_all_active(cls):
        """Get all active interviewers"""
        return cls.model.objects.filter(is_active=True).select_related('user')
    
    @classmethod
    def get_by_id(cls, interviewer_id: UUID):
        """Get interviewer by ID"""
        try:
            return cls.model.objects.select_related('user').get(id=interviewer_id)
        except cls.model.DoesNotExist:
            return None
    
    @classmethod
    def get_by_user(cls, user: CustomUser):
        """Get interviewer by user"""
        try:
            return cls.model.objects.get(user=user)
        except cls.model.DoesNotExist:
            return None
    
    @classmethod
    def get_with_available_schedules(cls, area_id: Optional[UUID] = None):
        """Get interviewers with available schedules"""
        qs = cls.model.objects.filter(
            is_active=True,
            schedules__date__gte=timezone.now().date(),
            schedules__is_active=True,
            schedules__is_booked=False
        ).distinct().select_related('user')
        
        if area_id:
            qs = qs.filter(areas__id=area_id)
        
        return qs
    
    @classmethod
    def get_by_area(cls, area_id: UUID):
        """Get interviewers for a specific area"""
        return cls.model.objects.filter(
            is_active=True,
            areas__id=area_id
        ).select_related('user')


class InterviewerScheduleRepository:
    """Repository for InterviewerSchedule operations"""
    model = InterviewerSchedule
    
    @classmethod
    def get_by_interviewer(cls, interviewer_id: UUID, future_only: bool = True):
        """Get schedules for an interviewer"""
        qs = cls.model.objects.filter(interviewer_id=interviewer_id)
        if future_only:
            qs = qs.filter(date__gte=timezone.now().date())
        return qs.order_by('date', 'start_time')
    
    @classmethod
    def get_available_schedules(cls, interviewer_id: Optional[UUID] = None):
        """Get available (unbooked) schedules"""
        qs = cls.model.objects.filter(
            date__gte=timezone.now().date(),
            is_active=True,
            is_booked=False
        )
        if interviewer_id:
            qs = qs.filter(interviewer_id=interviewer_id)
        return qs.order_by('date', 'start_time')
    
    @classmethod
    def get_by_id(cls, schedule_id: UUID):
        """Get schedule by ID"""
        try:
            return cls.model.objects.select_related('interviewer', 'interviewer__user').get(id=schedule_id)
        except cls.model.DoesNotExist:
            return None
    
    @classmethod
    def book_schedule(cls, schedule_id: UUID):
        """Mark a schedule as booked"""
        try:
            schedule = cls.model.objects.get(id=schedule_id)
            if not schedule.is_available:
                return None
            schedule.is_booked = True
            schedule.save()
            return schedule
        except cls.model.DoesNotExist:
            return None


class MentorApplicationRepository:
    """Repository for MentorApplication operations"""
    model = MentorApplication
    
    @classmethod
    def create(cls, applicant: CustomUser, **kwargs):
        """Create a new mentor application"""
        return cls.model.objects.create(applicant=applicant, **kwargs)
    
    @classmethod
    def get_by_id(cls, application_id: UUID):
        """Get application by ID"""
        try:
            return cls.model.objects.select_related(
                'applicant', 'assigned_interviewer', 'interview_schedule'
            ).prefetch_related('areas', 'skills').get(id=application_id)
        except cls.model.DoesNotExist:
            return None
    
    @classmethod
    def get_by_user(cls, user: CustomUser):
        """Get all applications by a user"""
        return cls.model.objects.filter(applicant=user).order_by('-created_at')
    
    @classmethod
    def get_latest_by_user(cls, user: CustomUser):
        """Get the latest application by a user"""
        return cls.model.objects.filter(applicant=user).order_by('-created_at').first()
    
    @classmethod
    def has_pending_application(cls, user: CustomUser) -> bool:
        """Check if user has a pending application"""
        return cls.model.objects.filter(
            applicant=user,
            status__in=['draft', 'submitted', 'interview_scheduled', 'interview_completed']
        ).exists()
    
    @classmethod
    def get_by_status(cls, status: str):
        """Get applications by status"""
        return cls.model.objects.filter(status=status).select_related('applicant').order_by('-created_at')
    
    @classmethod
    def get_by_interviewer(cls, interviewer: Interviewer, status: Optional[str] = None):
        """Get applications assigned to an interviewer"""
        qs = cls.model.objects.filter(assigned_interviewer=interviewer)
        if status:
            qs = qs.filter(status=status)
        return qs.select_related('applicant').order_by('-created_at')
    
    @classmethod
    def get_pending_interviews(cls):
        """Get applications with scheduled but not completed interviews"""
        return cls.model.objects.filter(
            status='interview_scheduled',
            interview_schedule__date__gte=timezone.now().date()
        ).select_related('applicant', 'assigned_interviewer', 'interview_schedule')
    
    @classmethod
    def get_stats(cls):
        """Get application statistics"""
        return {
            'total': cls.model.objects.count(),
            'pending': cls.model.objects.filter(status__in=['submitted', 'interview_scheduled']).count(),
            'approved': cls.model.objects.filter(status='approved').count(),
            'rejected': cls.model.objects.filter(status='rejected').count(),
        }


class ApprovedMentorRepository:
    """Repository for ApprovedMentor operations"""
    model = ApprovedMentor
    
    @classmethod
    def get_all_active(cls):
        """Get all active approved mentors"""
        return cls.model.objects.filter(
            is_active=True
        ).select_related('user', 'application').prefetch_related('areas', 'skills')
    
    @classmethod
    def get_accepting_mentees(cls):
        """Get mentors who are accepting mentees"""
        return cls.model.objects.filter(
            is_active=True,
            is_accepting_mentees=True
        ).select_related('user', 'application').prefetch_related('areas', 'skills')
    
    @classmethod
    def get_by_id(cls, mentor_id: UUID):
        """Get mentor by ID"""
        try:
            return cls.model.objects.select_related(
                'user', 'application'
            ).prefetch_related('areas', 'skills').get(id=mentor_id)
        except cls.model.DoesNotExist:
            return None
    
    @classmethod
    def get_by_user(cls, user: CustomUser):
        """Get mentor by user"""
        try:
            return cls.model.objects.select_related('application').get(user=user)
        except cls.model.DoesNotExist:
            return None
    
    @classmethod
    def get_by_area(cls, area_id: UUID):
        """Get mentors by area"""
        return cls.model.objects.filter(
            areas__id=area_id,
            is_active=True,
            is_accepting_mentees=True
        ).select_related('user', 'application').prefetch_related('areas', 'skills')
    
    @classmethod
    def search(cls, query: str, area_id: Optional[UUID] = None):
        """Search mentors by name or skills"""
        qs = cls.model.objects.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(skills__name__icontains=query),
            is_active=True
        ).distinct()
        
        if area_id:
            qs = qs.filter(areas__id=area_id)
        
        return qs.select_related('user', 'application').prefetch_related('areas', 'skills')
    
    @classmethod
    def create_from_application(cls, application: MentorApplication):
        """Create an approved mentor from an application"""
        mentor, created = cls.model.objects.get_or_create(
            user=application.applicant,
            defaults={'application': application}
        )
        if created:
            mentor.areas.set(application.areas.all())
            mentor.skills.set(application.skills.all())
        return mentor


class MenteeApplicationRepository:
    """Repository for MenteeApplication operations"""
    model = MenteeApplication
    
    @classmethod
    def create(cls, applicant: CustomUser, mentor: ApprovedMentor, area: MentorshipArea, **kwargs):
        """Create a new mentee application"""
        return cls.model.objects.create(applicant=applicant, mentor=mentor, area=area, **kwargs)
    
    @classmethod
    def get_by_id(cls, application_id: UUID):
        """Get application by ID"""
        try:
            return cls.model.objects.select_related(
                'applicant', 'mentor', 'mentor__user', 'area'
            ).prefetch_related('current_skills', 'skills_to_learn').get(id=application_id)
        except cls.model.DoesNotExist:
            return None
    
    @classmethod
    def get_by_applicant(cls, user: CustomUser):
        """Get all applications by a user"""
        return cls.model.objects.filter(applicant=user).select_related(
            'mentor', 'mentor__user', 'area'
        ).order_by('-created_at')
    
    @classmethod
    def get_by_mentor(cls, mentor: ApprovedMentor, status: Optional[str] = None):
        """Get applications to a mentor"""
        qs = cls.model.objects.filter(mentor=mentor).select_related('applicant', 'area')
        if status:
            qs = qs.filter(status=status)
        return qs.order_by('-created_at')
    
    @classmethod
    def get_pending_by_mentor(cls, mentor: ApprovedMentor):
        """Get pending applications for a mentor"""
        return cls.get_by_mentor(mentor, status='pending')
    
    @classmethod
    def has_applied(cls, user: CustomUser, mentor: ApprovedMentor, area: MentorshipArea) -> bool:
        """Check if user has already applied to this mentor for this area"""
        return cls.model.objects.filter(
            applicant=user,
            mentor=mentor,
            area=area,
            status__in=['pending', 'accepted']
        ).exists()


class MentorshipRelationshipRepository:
    """Repository for MentorshipRelationship operations"""
    model = MentorshipRelationship
    
    @classmethod
    def create(cls, mentor: ApprovedMentor, mentee: CustomUser, area: MentorshipArea, **kwargs):
        """Create a new mentorship relationship"""
        return cls.model.objects.create(mentor=mentor, mentee=mentee, area=area, **kwargs)
    
    @classmethod
    def get_by_id(cls, relationship_id: UUID):
        """Get relationship by ID"""
        try:
            return cls.model.objects.select_related(
                'mentor', 'mentor__user', 'mentee', 'area'
            ).get(id=relationship_id)
        except cls.model.DoesNotExist:
            return None
    
    @classmethod
    def get_by_mentor(cls, mentor: ApprovedMentor, status: Optional[str] = None):
        """Get relationships for a mentor"""
        qs = cls.model.objects.filter(mentor=mentor).select_related('mentee', 'area')
        if status:
            qs = qs.filter(status=status)
        return qs.order_by('-started_at')
    
    @classmethod
    def get_active_by_mentor(cls, mentor: ApprovedMentor):
        """Get active relationships for a mentor"""
        return cls.get_by_mentor(mentor, status='active')
    
    @classmethod
    def get_by_mentee(cls, mentee: CustomUser, status: Optional[str] = None):
        """Get relationships for a mentee"""
        qs = cls.model.objects.filter(mentee=mentee).select_related(
            'mentor', 'mentor__user', 'area'
        )
        if status:
            qs = qs.filter(status=status)
        return qs.order_by('-started_at')
    
    @classmethod
    def get_active_by_mentee(cls, mentee: CustomUser):
        """Get active relationships for a mentee"""
        return cls.get_by_mentee(mentee, status='active')


class MentorshipSessionRepository:
    """Repository for MentorshipSession operations"""
    model = MentorshipSession
    
    @classmethod
    def create(cls, relationship: MentorshipRelationship, **kwargs):
        """Create a new session"""
        return cls.model.objects.create(relationship=relationship, **kwargs)
    
    @classmethod
    def get_by_id(cls, session_id: UUID):
        """Get session by ID"""
        try:
            return cls.model.objects.select_related(
                'relationship', 'relationship__mentor', 'relationship__mentee'
            ).get(id=session_id)
        except cls.model.DoesNotExist:
            return None
    
    @classmethod
    def get_by_relationship(cls, relationship_id: UUID):
        """Get sessions for a relationship"""
        return cls.model.objects.filter(relationship_id=relationship_id).order_by('-date')
    
    @classmethod
    def get_upcoming(cls, user: CustomUser, as_mentor: bool = False):
        """Get upcoming sessions for a user"""
        if as_mentor:
            return cls.model.objects.filter(
                relationship__mentor__user=user,
                date__gte=timezone.now().date(),
                status='scheduled'
            ).order_by('date', 'start_time')
        else:
            return cls.model.objects.filter(
                relationship__mentee=user,
                date__gte=timezone.now().date(),
                status='scheduled'
            ).order_by('date', 'start_time')
    
    @classmethod
    def get_by_mentee(cls, user: CustomUser):
        """Get all sessions where user is the mentee"""
        return cls.model.objects.filter(
            relationship__mentee=user
        ).select_related(
            'relationship', 'relationship__mentor', 'relationship__area'
        ).order_by('-date', '-start_time')
    
    @classmethod
    def get_by_mentor(cls, mentor):
        """Get all sessions where user is the mentor"""
        return cls.model.objects.filter(
            relationship__mentor=mentor
        ).select_related(
            'relationship', 'relationship__mentee', 'relationship__area'
        ).order_by('-date', '-start_time')


class MentorPaymentRepository:
    """Repository for MentorPayment operations"""
    model = MentorPayment
    
    @classmethod
    def create(cls, mentor: ApprovedMentor, **kwargs):
        """Create a new payment record"""
        return cls.model.objects.create(mentor=mentor, **kwargs)
    
    @classmethod
    def get_by_mentor(cls, mentor: ApprovedMentor):
        """Get payments for a mentor"""
        return cls.model.objects.filter(mentor=mentor).order_by('-created_at')
    
    @classmethod
    def get_total_earnings(cls, mentor: ApprovedMentor):
        """Get total earnings for a mentor"""
        from django.db.models import Sum
        result = cls.model.objects.filter(
            mentor=mentor,
            status='completed'
        ).aggregate(total=Sum('amount'))
        return result['total'] or 0
