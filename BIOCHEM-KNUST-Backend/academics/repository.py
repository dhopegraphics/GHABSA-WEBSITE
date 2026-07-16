from academics.models import (
    Course,
    AcademicSlides,
    PastQuestions,
    OnlineTutorialTips,
    InternshipOpportunities,
)
from django.utils import timezone
from django.db.models import Q, Count, Prefetch
from django.core.cache import cache


class CourseRepository:
    """
    Repository for Course model with optimized queries.
    Uses select_related, prefetch_related, and caching for performance.
    """
    model = Course.objects
    CACHE_TIMEOUT = 300  # 5 minutes cache

    @classmethod
    def _get_optimized_queryset(cls):
        """
        Returns an optimized queryset with:
        - select_related for lecturer (ForeignKey)
        - prefetch_related for prerequisites (ManyToMany)
        - annotated counts to avoid N+1 queries
        """
        return cls.model.select_related('lecturer').prefetch_related(
            'prerequisites'
        ).annotate(
            _slides_count=Count('slides', filter=Q(slides__approved=True)),
            _past_questions_count=Count('past_questions', filter=Q(past_questions__approved=True)),
            _online_tips_count=Count('online_tips', filter=Q(online_tips__approved=True)),
        )

    @classmethod
    def get_all(cls):
        """Get all courses with optimized queries and caching"""
        cache_key = 'courses_all'
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        
        queryset = cls._get_optimized_queryset().all()
        cache.set(cache_key, queryset, cls.CACHE_TIMEOUT)
        return queryset

    @classmethod
    def get_by_id(cls, course_id):
        """Get single course with optimized queries"""
        cache_key = f'course_{course_id}'
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        
        try:
            course = cls._get_optimized_queryset().get(pk=course_id)
            cache.set(cache_key, course, cls.CACHE_TIMEOUT)
            return course
        except Course.DoesNotExist:
            return None

    @classmethod
    def get_by_lecturer(cls, lecturer_id):
        """Get all courses taught by a specific lecturer"""
        cache_key = f'courses_lecturer_{lecturer_id}'
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        
        queryset = cls._get_optimized_queryset().filter(lecturer_id=lecturer_id)
        cache.set(cache_key, queryset, cls.CACHE_TIMEOUT)
        return queryset
    
    @classmethod
    def get_by_program(cls, program):
        """Get all courses for a specific program (CS or IT)"""
        cache_key = f'courses_program_{program}'
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        
        queryset = cls._get_optimized_queryset().filter(program=program)
        cache.set(cache_key, queryset, cls.CACHE_TIMEOUT)
        return queryset

    @classmethod
    def invalidate_cache(cls, course_id=None, program=None):
        """Invalidate course cache - call after updates"""
        cache.delete('courses_all')
        if course_id:
            cache.delete(f'course_{course_id}')
        if program:
            cache.delete(f'courses_program_{program}')
        # Also invalidate both program caches when no specific program given
        if not program:
            cache.delete('courses_program_CS')
            cache.delete('courses_program_IT')


class SlidesRepository:
    model = AcademicSlides.objects
    CACHE_TIMEOUT = 300

    @classmethod
    def get_slides(cls, course_id):
        """Get slides for a course with caching"""
        cache_key = f'slides_course_{course_id}'
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        
        queryset = cls.model.filter(course=course_id, approved=True).only(
            'id', 'course_id', 'title', 'file', 'file_url', 'created_at'
        )
        cache.set(cache_key, list(queryset), cls.CACHE_TIMEOUT)
        return queryset

    @classmethod
    def get_slide(cls, pk):
        try:
            return cls.model.get(pk=pk)
        except:
            return None
    
    @classmethod
    def invalidate_cache(cls, course_id):
        cache.delete(f'slides_course_{course_id}')


class PastQuestionsRepository:
    model = PastQuestions.objects
    CACHE_TIMEOUT = 300

    @classmethod
    def get_questions(cls, course_id):
        """Get past questions for a course with caching"""
        cache_key = f'past_questions_course_{course_id}'
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        
        queryset = cls.model.filter(course=course_id, approved=True).only(
            'id', 'course_id', 'title', 'file', 'file_url', 'created_at'
        )
        cache.set(cache_key, list(queryset), cls.CACHE_TIMEOUT)
        return queryset

    @classmethod
    def get_past_question(cls, pk):
        try:
            return cls.model.get(pk=pk)
        except:
            return None
    
    @classmethod
    def invalidate_cache(cls, course_id):
        cache.delete(f'past_questions_course_{course_id}')


class InternshipOpportunitiesRepository:
    model = InternshipOpportunities.objects

    @classmethod
    def get_all_internship_opportunities(cls):
        """Get all internships (including expired ones)"""
        return cls.model.all()

    @classmethod
    def get_active_internships(cls):
        """Get only active internships (deadline hasn't passed)"""
        now = timezone.now()
        # Include internships with no deadline OR deadline in the future
        return cls.model.filter(
            Q(application_deadline__isnull=True) | Q(application_deadline__gt=now)
        ).order_by('-created_at')

    @staticmethod
    def get_internship_by_id(cls, internship_id):
        return cls.model.get(id=internship_id)


class OnlineTutorialTipsRepository:
    model = OnlineTutorialTips.objects
    CACHE_TIMEOUT = 300

    @classmethod
    def get_links(cls, course_id):
        """Get online tips for a course with caching"""
        cache_key = f'online_tips_course_{course_id}'
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        
        queryset = cls.model.filter(course=course_id, approved=True).only(
            'id', 'course_id', 'title', 'link', 'type_of_resource', 'created_at'
        )
        cache.set(cache_key, list(queryset), cls.CACHE_TIMEOUT)
        return queryset

    @classmethod
    def get_online_tip(cls, pk):
        try:
            return cls.model.get(pk=pk)
        except:
            return None
    
    @classmethod
    def invalidate_cache(cls, course_id):
        cache.delete(f'online_tips_course_{course_id}')
