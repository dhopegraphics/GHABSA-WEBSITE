"""
Calendar Sync Services
Generates iCalendar (.ics) data from existing schedule models
"""
from icalendar import Calendar, Event, vRecur, vText
from datetime import datetime, timedelta, date
from django.utils import timezone
from django.conf import settings
import pytz
import hashlib
import logging

from timetable_system.models import ClassSchedule, ExaminationSchedule, DayOfWeek
from events.models import Event as EventModel
from events.repositories import EventRepo

logger = logging.getLogger(__name__)

# Timezone for Ghana (UTC+0)
TIMEZONE = pytz.timezone('Africa/Accra')
PRODID = '-//CSS KNUST//Calendar Sync//EN'


class CalendarService:
    """
    Service class for generating iCalendar data from various schedule sources.
    """
    
    @staticmethod
    def _create_base_calendar(name: str, description: str = "") -> Calendar:
        """Create a base iCalendar object with standard properties"""
        cal = Calendar()
        cal.add('prodid', PRODID)
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')
        cal.add('method', 'PUBLISH')
        cal.add('x-wr-calname', name)
        if description:
            cal.add('x-wr-caldesc', description)
        cal.add('x-wr-timezone', 'Africa/Accra')
        return cal
    
    @staticmethod
    def _generate_uid(prefix: str, identifier: str) -> str:
        """Generate a unique identifier for calendar events"""
        hash_input = f"{prefix}-{identifier}"
        return f"{hashlib.md5(hash_input.encode()).hexdigest()}@cssknust.edu.gh"
    
    @staticmethod
    def _get_semester_dates(academic_year: str, semester: str = None) -> tuple:
        """
        Get semester start and end dates based on academic year.
        Academic year format: "2024/2025"
        
        Returns: (start_date, end_date)
        """
        try:
            start_year = int(academic_year.split('/')[0])
        except (ValueError, IndexError):
            start_year = timezone.now().year
        
        current_month = timezone.now().month
        
        # Determine current semester if not provided
        if not semester:
            # First semester: September - January
            # Second semester: February - June
            semester = "1" if current_month >= 9 or current_month <= 1 else "2"
        
        if semester == "1":
            # First semester: September to January
            start_date = date(start_year, 9, 1)
            end_date = date(start_year + 1, 1, 31)
        else:
            # Second semester: February to June
            start_date = date(start_year + 1, 2, 1)
            end_date = date(start_year + 1, 6, 30)
        
        return start_date, end_date
    
    @staticmethod
    def _day_of_week_to_rrule(day: int) -> str:
        """Convert DayOfWeek integer to iCalendar RRULE day"""
        mapping = {
            1: 'MO',  # Monday
            2: 'TU',  # Tuesday
            3: 'WE',  # Wednesday
            4: 'TH',  # Thursday
            5: 'FR',  # Friday
            6: 'SA',  # Saturday
            7: 'SU',  # Sunday
        }
        return mapping.get(day, 'MO')

    @classmethod
    def generate_class_schedule_calendar(
        cls,
        user,
        academic_year: str = None,
        program: str = None,
        year: int = None,
        group: str = None,
        semester: str = None
    ) -> Calendar:
        """
        Generate iCalendar for class schedules.
        Uses user's profile for personalization if parameters not provided.
        Note: Group is optional for programs like IT that don't have group separation.
        """
        logger.info(f"Generating class schedule calendar for user: {user.username if user else 'None'}")
        
        # Get user parameters
        academic_year = academic_year or user.get_current_academic_year()
        program = program or user.program
        year = year or user.get_year()
        group = group or user.group
        semester = semester or user.calculate_current_semester()
        
        logger.info(f"Class calendar params - AY: {academic_year}, Program: {program}, Year: {year}, Group: {group}, Semester: {semester}")
        
        # Get semester date range
        semester_start, semester_end = cls._get_semester_dates(academic_year, semester)
        
        # Create calendar name (omit group if not applicable)
        group_part = f" {group}" if group else ""
        cal_name = f"Class Timetable - {program} Year {year}{group_part}"
        cal = cls._create_base_calendar(
            name=cal_name,
            description=f"Class schedule for {academic_year}, Semester {semester}"
        )
        
        # Query class schedules
        # Build filters based on whether group is required
        filters = {
            'academic_year': academic_year,
            'program': program,
            'year': year,
            'course__semester': semester
        }
        
        # Only filter by group if the program requires groups (e.g., CS)
        from timetable_system.models import ClassSchedule
        if ClassSchedule.program_requires_group(program) and group:
            filters['group'] = group
        elif not ClassSchedule.program_requires_group(program):
            # For programs without groups (like IT), explicitly get schedules without groups
            filters['group__isnull'] = True
        
        schedules = ClassSchedule.objects.filter(**filters).select_related('course').order_by('day_of_week', 'start_time')
        
        for schedule in schedules:
            event = Event()
            
            # Generate unique ID
            uid = cls._generate_uid('class', str(schedule.id))
            event.add('uid', uid)
            
            # Event summary (title)
            course_code = schedule.course.course_code if schedule.course else "Class"
            course_name = schedule.course.course_name if schedule.course else "Unknown"
            event.add('summary', f"{course_code}: {course_name}")
            
            # Description (handle optional group)
            description_parts = [
                f"Course: {course_name}",
                f"Code: {course_code}",
                f"Program: {schedule.get_program_display()}",
                f"Year: {schedule.year}",
            ]
            if schedule.group:
                description_parts.append(f"Group: {schedule.get_group_display()}")
            if schedule.notes:
                description_parts.append(f"Notes: {schedule.notes}")
            event.add('description', '\n'.join(description_parts))
            
            # Location
            location_parts = []
            if schedule.room:
                location_parts.append(schedule.room)
            if schedule.address:
                location_parts.append(str(schedule.address))
            if location_parts:
                event.add('location', ', '.join(location_parts))
            
            # Calculate first occurrence date
            # Find the first date that matches the day of week after semester start
            days_ahead = schedule.day_of_week - semester_start.isoweekday()
            if days_ahead < 0:
                days_ahead += 7
            first_date = semester_start + timedelta(days=days_ahead)
            
            # Start and end times
            start_dt = TIMEZONE.localize(datetime.combine(first_date, schedule.start_time))
            end_dt = TIMEZONE.localize(datetime.combine(first_date, schedule.end_time))
            
            event.add('dtstart', start_dt)
            event.add('dtend', end_dt)
            
            # Recurrence rule (weekly until semester end)
            rrule = vRecur({
                'freq': 'weekly',
                'until': datetime.combine(semester_end, datetime.max.time()).replace(tzinfo=TIMEZONE),
                'byday': cls._day_of_week_to_rrule(schedule.day_of_week)
            })
            event.add('rrule', rrule)
            
            # Timestamps
            event.add('dtstamp', timezone.now())
            event.add('created', schedule.created_at)
            event.add('last-modified', schedule.updated_at)
            
            # Categories
            event.add('categories', ['CLASS', 'LECTURE', program])
            
            # Alarms (multiple reminders based on user preferences or defaults)
            from icalendar import Alarm
            from .models import CalendarReminderPreference
            
            # Get user's reminder preferences or use defaults
            try:
                prefs = CalendarReminderPreference.get_for_user(user)
                alarm_times = prefs.get_reminder_times('class') if prefs.class_reminders_enabled else []
            except:
                alarm_times = [15, 30]  # Default: 15 and 30 minutes before
            
            for minutes in alarm_times:
                alarm = Alarm()
                alarm.add('action', 'DISPLAY')
                if minutes >= 60:
                    hours = minutes // 60
                    alarm.add('description', f"Class in {hours} hour{'s' if hours > 1 else ''}: {course_code}")
                else:
                    alarm.add('description', f"Class in {minutes} minutes: {course_code}")
                alarm.add('trigger', timedelta(minutes=-minutes))
                event.add_component(alarm)
            
            cal.add_component(event)
        
        logger.info(f"Class calendar generated with {schedules.count()} schedules")
        return cal

    @classmethod
    def generate_exam_schedule_calendar(
        cls,
        user=None,
        year: int = None,
        semester: str = None,
        include_past: bool = False
    ) -> Calendar:
        """
        Generate iCalendar for exam schedules.
        """
        logger.info(f"Generating exam schedule calendar - User: {user.username if user else 'None'}, Year: {year}, Semester: {semester}")
        
        # Get parameters
        if user:
            year = year or user.get_year()
            semester = semester or user.calculate_current_semester()
        
        logger.info(f"Exam calendar params - Year: {year}, Semester: {semester}, Include past: {include_past}")
        
        # Create calendar
        cal_name = "Exam Schedule" + (f" - Year {year}" if year else "")
        cal = cls._create_base_calendar(
            name=cal_name,
            description="Examination schedule"
        )
        
        # Query exams
        now = timezone.now()
        filters = {}
        
        if year:
            filters['course__year'] = year
        if semester:
            filters['course__semester'] = semester
        if not include_past:
            filters['time__gte'] = now
        
        exams = ExaminationSchedule.objects.filter(
            **filters
        ).select_related('course').order_by('time')
        
        for exam in exams:
            if not exam.time:
                continue
                
            event = Event()
            
            # Generate unique ID
            uid = cls._generate_uid('exam', str(exam.id))
            event.add('uid', uid)
            
            # Event summary
            course_code = exam.course.course_code if exam.course else "Exam"
            course_name = exam.course.course_name if exam.course else "Unknown"
            event.add('summary', f"EXAM: {course_code} - {course_name}")
            
            # Description
            description_parts = [
                f"Course: {course_name}",
                f"Code: {course_code}",
                f"College: {exam.college}",
            ]
            if exam.room:
                description_parts.append(f"Room: {exam.room}")
            if exam.index_number_start and exam.index_number_end:
                description_parts.append(f"Index Range: {exam.index_number_start} - {exam.index_number_end}")
            event.add('description', '\n'.join(description_parts))
            
            # Location
            location_parts = [exam.college]
            if exam.room:
                location_parts.append(exam.room)
            if exam.address:
                location_parts.append(str(exam.address))
            event.add('location', ', '.join(location_parts))
            
            # Start time (assume 2-3 hour exam duration)
            start_dt = exam.time
            if timezone.is_naive(start_dt):
                start_dt = TIMEZONE.localize(start_dt)
            end_dt = start_dt + timedelta(hours=3)
            
            event.add('dtstart', start_dt)
            event.add('dtend', end_dt)
            event.add('dtstamp', timezone.now())
            
            # Categories
            event.add('categories', ['EXAM', 'ACADEMIC'])
            
            # Priority (high for exams)
            event.add('priority', 1)
            
            # Alarms (multiple reminders based on user preferences or defaults)
            from icalendar import Alarm
            from .models import CalendarReminderPreference
            
            # Get user's reminder preferences or use defaults
            try:
                if user:
                    prefs = CalendarReminderPreference.get_for_user(user)
                    alarm_times = prefs.get_reminder_times('exam') if prefs.exam_reminders_enabled else []
                else:
                    alarm_times = [1440, 120, 30]  # Defaults: 1 day, 2 hours, 30 minutes
            except:
                alarm_times = [1440, 120, 30]
            
            for minutes in alarm_times:
                alarm = Alarm()
                alarm.add('action', 'DISPLAY')
                
                # Create descriptive alarm messages based on time
                if minutes >= 1440:
                    days = minutes // 1440
                    alarm.add('description', f"EXAM in {days} day{'s' if days > 1 else ''}: {course_code}")
                elif minutes >= 60:
                    hours = minutes // 60
                    alarm.add('description', f"EXAM in {hours} hour{'s' if hours > 1 else ''}: {course_code}")
                else:
                    alarm.add('description', f"EXAM in {minutes} minutes: {course_code}")
                
                alarm.add('trigger', timedelta(minutes=-minutes))
                event.add_component(alarm)
            
            cal.add_component(event)
        
        logger.info(f"Exam calendar generated with {exams.count()} exams")
        return cal

    @classmethod
    def generate_events_calendar(
        cls,
        user=None,
        include_past: bool = False,
        user_rsvp_only: bool = False
    ) -> Calendar:
        """
        Generate iCalendar for events.
        """
        logger.info(f"Generating events calendar - User: {user.username if user else 'None'}, Include past: {include_past}, RSVP only: {user_rsvp_only}")
        
        try:
            # Create calendar
            cal_name = "CSS KNUST Events"
            
            cal = cls._create_base_calendar(
                name=cal_name,
                description="Computer Science Society KNUST Events"
            )
            
            # Query events - always get all events (upcoming + ongoing)
            if user and user_rsvp_only:
                events = EventRepo.get_user_rsvp_events(user)
                logger.info(f"Fetching RSVP events for user: {user.username}")
            elif include_past:
                events = EventRepo.get_all_events()
                logger.info("Fetching all events (including past)")
            else:
                # Get upcoming and ongoing events
                upcoming = EventRepo.get_upcoming_events()
                ongoing = EventRepo.get_ongoing_events()
                events = list(upcoming) + list(ongoing)
                logger.info(f"Fetching upcoming ({len(list(upcoming))} events) + ongoing events")
            
            event_count = 0
            for evt in events:
                if not evt.event_date:
                    logger.debug(f"Skipping event {evt.event_id} - no event_date")
                    continue
                
                event_count += 1
                event = Event()
                
                # Generate unique ID
                uid = cls._generate_uid('event', str(evt.event_id))
                event.add('uid', uid)
                
                # Event summary
                summary = evt.event_name
                if evt.emoji:
                    summary = f"{evt.emoji} {summary}"
                event.add('summary', summary)
                
                # Description
                description_parts = [evt.description]
                description_parts.append(f"\nOrganized by: {evt.organised_by}")
                if evt.event_type:
                    description_parts.append(f"Type: {evt.get_event_type_display()}")
                if evt.registration_link:
                    description_parts.append(f"\nRegistration: {evt.registration_link}")
                if evt.media_link:
                    description_parts.append(f"Media: {evt.media_link}")
                event.add('description', '\n'.join(description_parts))
                
                # Location
                location_parts = []
                if evt.venue:
                    location_parts.append(evt.venue)
                if evt.building:
                    location_parts.append(evt.building)
                if evt.virtual_link and evt.location_type in ('virtual', 'hybrid'):
                    location_parts.append(f"Online: {evt.virtual_link}")
                if location_parts:
                    event.add('location', ', '.join(location_parts))
                
                # Date/time
                start_dt = evt.event_date
                if timezone.is_naive(start_dt):
                    start_dt = TIMEZONE.localize(start_dt)
                
                if evt.event_end_date:
                    end_dt = evt.event_end_date
                    if timezone.is_naive(end_dt):
                        end_dt = TIMEZONE.localize(end_dt)
                else:
                    # Default to 2-hour event
                    end_dt = start_dt + timedelta(hours=2)
                
                event.add('dtstart', start_dt)
                event.add('dtend', end_dt)
                event.add('dtstamp', timezone.now())
                event.add('created', evt.created_at)
                event.add('last-modified', evt.last_updated)
                
                # Categories
                categories = ['EVENT', 'CSS_KNUST']
                if evt.event_type:
                    categories.append(evt.event_type.upper())
                event.add('categories', categories)
                
                # URL (if registration link exists)
                if evt.registration_link:
                    event.add('url', evt.registration_link)
                
                # Alarms (multiple reminders for events)
                from icalendar import Alarm
                from .models import CalendarReminderPreference
                
                # Get user's reminder preferences or use defaults
                try:
                    if user:
                        prefs = CalendarReminderPreference.get_for_user(user)
                        alarm_times = prefs.get_reminder_times('event') if prefs.event_reminders_enabled else []
                    else:
                        alarm_times = [60, 1440]  # Defaults: 1 hour and 1 day before
                except:
                    alarm_times = [60, 1440]
                
                for minutes in alarm_times:
                    alarm = Alarm()
                    alarm.add('action', 'DISPLAY')
                    
                    if minutes >= 1440:
                        days = minutes // 1440
                        alarm.add('description', f"Event in {days} day{'s' if days > 1 else ''}: {evt.event_name}")
                    elif minutes >= 60:
                        hours = minutes // 60
                        alarm.add('description', f"Event in {hours} hour{'s' if hours > 1 else ''}: {evt.event_name}")
                    else:
                        alarm.add('description', f"Event in {minutes} minutes: {evt.event_name}")
                    
                    alarm.add('trigger', timedelta(minutes=-minutes))
                    event.add_component(alarm)
                
                cal.add_component(event)
            
            logger.info(f"Events calendar generated with {event_count} events")
            return cal
            
        except Exception as e:
            logger.exception(f"Error generating events calendar: {str(e)}")
            raise

    @classmethod
    def generate_full_academic_calendar(cls, user) -> Calendar:
        """
        Generate a combined calendar with classes, exams, and events.
        """
        logger.info(f"Generating full academic calendar for user: {user.username if user else 'None'}")
        
        cal_name = f"Academic Calendar - {user.first_name}"
        cal = cls._create_base_calendar(
            name=cal_name,
            description="Complete academic calendar including classes, exams, and events"
        )
        
        # Get individual calendars
        logger.info("Generating class schedule component...")
        class_cal = cls.generate_class_schedule_calendar(user)
        
        logger.info("Generating exam schedule component...")
        exam_cal = cls.generate_exam_schedule_calendar(user)
        
        logger.info("Generating events component...")
        events_cal = cls.generate_events_calendar(include_past=False)
        
        # Merge all events into single calendar
        class_count = 0
        for component in class_cal.walk():
            if component.name == 'VEVENT':
                cal.add_component(component)
                class_count += 1
        
        exam_count = 0
        for component in exam_cal.walk():
            if component.name == 'VEVENT':
                cal.add_component(component)
                exam_count += 1
        
        event_count = 0
        for component in events_cal.walk():
            if component.name == 'VEVENT':
                cal.add_component(component)
                event_count += 1
        
        logger.info(f"Full calendar generated - Classes: {class_count}, Exams: {exam_count}, Events: {event_count}")
        return cal

    @staticmethod
    def calendar_to_ics(calendar: Calendar) -> bytes:
        """Convert calendar to .ics file content"""
        return calendar.to_ical()


class CalendarExportService:
    """
    Service for exporting calendars via various methods
    """
    
    @staticmethod
    def get_download_response(calendar: Calendar, filename: str):
        """Create HTTP response for calendar download"""
        from django.http import HttpResponse
        
        response = HttpResponse(
            calendar.to_ical(),
            content_type='text/calendar; charset=utf-8'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}.ics"'
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response
    
    @staticmethod
    def get_subscription_response(calendar: Calendar):
        """Create HTTP response for calendar subscription"""
        from django.http import HttpResponse
        
        response = HttpResponse(
            calendar.to_ical(),
            content_type='text/calendar; charset=utf-8'
        )
        # Allow caching for subscription (5 minutes)
        response['Cache-Control'] = 'public, max-age=300'
        return response
