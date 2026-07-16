from timetable_system.models import ExaminationSchedule, ClassSchedule
from django.utils import timezone


class ExamScheduleRepository:
    model = ExaminationSchedule.objects

    @classmethod
    def get_exam_schedules(cls, year, current_semester=None):
        """
        Get all upcoming examinations (future dates only) for a specific course year and semester.
        
        Args:
            year: Course year (1, 2, 3, 4)
            current_semester: Current semester (e.g., "1" or "2"). If None, returns all semesters.
        
        Returns:
            QuerySet of ExaminationSchedule objects
        """
        # Only get exams with future dates (no past exams)
        now = timezone.now()
        
        filters = {
            'time__gt': now,
            'course__year': int(year),
        }
        
        # Filter by semester if provided
        if current_semester:
            filters['course__semester'] = str(current_semester)
        
        return cls.model.filter(**filters).order_by('time').all()

    @classmethod
    def get_past_exam_schedules(cls, year, current_semester=None):
        """
        Get all past examinations (past dates only) for a specific course year and semester.
        
        Args:
            year: Course year (1, 2, 3, 4)
            current_semester: Current semester (e.g., "1" or "2"). If None, returns all semesters.
        
        Returns:
            QuerySet of ExaminationSchedule objects ordered by most recent first
        """
        # Only get exams with past dates
        now = timezone.now()
        
        filters = {
            'time__lt': now,
            'course__year': int(year),
        }
        
        # Filter by semester if provided
        if current_semester:
            filters['course__semester'] = str(current_semester)
        
        return cls.model.filter(**filters).order_by('-time').all()


class ClassScheduleRepository:
    """Repository helper for ClassSchedule queries."""

    @staticmethod
    def model():
        return ClassSchedule.objects

    @classmethod
    def get_schedules_for_student(cls, academic_year, year, group, program, current_semester=None):
        """
        Get class schedules filtered by academic year, year, group, program, and semester.
        
        Args:
            academic_year: Academic year (e.g., "2024/2025")
            year: Academic year number (e.g., 1, 2, 3, 4)
            group: Student group (e.g., "G1", "G2", or None for IT students)
            program: Program code (e.g., "CS", "IT")
            current_semester: Current semester (e.g., "1" or "2"). If None, returns all semesters.
        
        Returns:
            QuerySet of ClassSchedule objects ordered by day and time
        """
        from timetable_system.models import ClassSchedule
        
        filters = {
            'academic_year': academic_year,
            'year': int(year),
            'program': program
        }
        
        # Only filter by group if:
        # 1. The program requires groups (currently only CS)
        # 2. A group value is provided
        if ClassSchedule.program_requires_group(program) and group:
            filters['group'] = group
        elif not ClassSchedule.program_requires_group(program):
            # For programs without groups (like IT), explicitly filter for schedules without groups
            filters['group__isnull'] = True
        
        # Filter by semester if provided
        if current_semester:
            filters['course__semester'] = str(current_semester)
        
        return cls.model().filter(**filters).order_by('day_of_week', 'start_time').all()

    @classmethod
    def get_schedules_for_course(cls, course_id):
        """
        Get all schedules for a specific course.
        
        Args:
            course_id: UUID of the course
        
        Returns:
            QuerySet of ClassSchedule objects
        """
        return cls.model().filter(course_id=course_id).all()
    
    @classmethod
    def get_schedules_for_day(cls, academic_year, year, group, program, day_of_week):
        """
        Get schedules for a specific day of the week.
        
        Args:
            academic_year: Academic year (e.g., "2024/2025")
            year: Academic year number (e.g., 1, 2, 3, 4)
            group: Student group (e.g., "G1", "G2")
            program: Program code (e.g., "CS", "IT")
            day_of_week: Day number (1=Monday, 7=Sunday)
        
        Returns:
            QuerySet of ClassSchedule objects
        """
        return cls.model().filter(
            academic_year=academic_year,
            year=int(year),
            group=group,
            program=program,
            day_of_week=day_of_week
        ).order_by('start_time').all()
