"""
Calendar Sync Views
API endpoints for calendar download and subscription
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import CalendarToken, PublicCalendarToken
from .services import CalendarService, CalendarExportService
from .serializers import (
    CalendarTokenSerializer,
    CalendarSubscriptionURLSerializer,
    CalendarTokenCreateSerializer,
    CalendarReminderPreferenceSerializer,
    ScheduledReminderSerializer
)

import logging

logger = logging.getLogger(__name__)


class CalendarTokenListView(APIView):
    """
    List and manage user's calendar tokens
    
    GET /calendar/tokens/
    POST /calendar/tokens/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """List all calendar tokens for the authenticated user"""
        tokens = CalendarToken.objects.filter(user=request.user, is_active=True)
        serializer = CalendarTokenSerializer(tokens, many=True, context={'request': request})
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def post(self, request):
        """Create a new calendar token"""
        serializer = CalendarTokenCreateSerializer(data=request.data)
        if serializer.is_valid():
            calendar_type = serializer.validated_data.get('calendar_type', 'personal')
            name = serializer.validated_data.get('name', '')
            
            # Get or create token
            token = CalendarToken.get_or_create_for_user(request.user, calendar_type)
            if name:
                token.name = name
                token.save(update_fields=['name'])
            
            return Response({
                'success': True,
                'message': 'Calendar token created',
                'data': CalendarTokenSerializer(token, context={'request': request}).data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class CalendarTokenDetailView(APIView):
    """
    Manage individual calendar token
    
    GET /calendar/tokens/<token_id>/
    DELETE /calendar/tokens/<token_id>/
    POST /calendar/tokens/<token_id>/regenerate/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, token_id):
        """Get calendar token details"""
        token = get_object_or_404(
            CalendarToken,
            id=token_id,
            user=request.user
        )
        serializer = CalendarTokenSerializer(token, context={'request': request})
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def delete(self, request, token_id):
        """Deactivate a calendar token"""
        token = get_object_or_404(
            CalendarToken,
            id=token_id,
            user=request.user
        )
        token.is_active = False
        token.save(update_fields=['is_active'])
        return Response({
            'success': True,
            'message': 'Calendar token deactivated'
        })


class CalendarTokenRegenerateView(APIView):
    """
    Regenerate calendar token (invalidates old URLs)
    
    POST /calendar/tokens/<token_id>/regenerate/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, token_id):
        """Regenerate token"""
        token = get_object_or_404(
            CalendarToken,
            id=token_id,
            user=request.user
        )
        new_token = token.regenerate_token()
        return Response({
            'success': True,
            'message': 'Token regenerated. Update your calendar subscriptions.',
            'data': CalendarTokenSerializer(token, context={'request': request}).data
        })


class CalendarSubscriptionURLsView(APIView):
    """
    Get subscription URLs for all calendar types
    
    GET /calendar/subscription-urls/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get all subscription URLs for the user"""
        calendar_types = ['classes', 'exams', 'events', 'personal', 'full']
        urls = {}
        
        base_url = request.build_absolute_uri('/calendar/subscribe/')
        webcal_base = base_url.replace('http://', 'webcal://').replace('https://', 'webcal://')
        
        for cal_type in calendar_types:
            token = CalendarToken.get_or_create_for_user(request.user, cal_type)
            urls[cal_type] = {
                'name': token.get_calendar_type_display(),
                'http_url': f"{base_url}{token.token}/",
                'webcal_url': f"{webcal_base}{token.token}/",
                'download_url': request.build_absolute_uri(f'/calendar/download/{cal_type}/'),
            }
        
        return Response({
            'success': True,
            'data': urls,
            'instructions': {
                'ios': 'Use the webcal:// URL to subscribe on iOS',
                'android': 'Use the HTTP URL in Google Calendar',
                'outlook': 'Add calendar from internet using HTTP URL',
                'download': 'Use download URLs for one-time import'
            }
        })


class CalendarDownloadView(APIView):
    """
    Download calendar as .ics file
    
    GET /calendar/download/<calendar_type>/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, calendar_type):
        """Download calendar file"""
        user = request.user
        
        try:
            if calendar_type == 'classes':
                calendar = CalendarService.generate_class_schedule_calendar(user)
                filename = f"class_timetable_{user.username}"
            elif calendar_type == 'exams':
                calendar = CalendarService.generate_exam_schedule_calendar(user)
                filename = f"exam_schedule_{user.username}"
            elif calendar_type == 'events':
                calendar = CalendarService.generate_events_calendar(include_past=False)
                filename = f"css_knust_events_{user.username}"
            elif calendar_type == 'full' or calendar_type == 'personal':
                calendar = CalendarService.generate_full_academic_calendar(user)
                filename = f"academic_calendar_{user.username}"
            else:
                return Response({
                    'success': False,
                    'error': f'Invalid calendar type: {calendar_type}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return CalendarExportService.get_download_response(calendar, filename)
            
        except Exception as e:
            logger.exception(f"Error generating calendar: {e}")
            return Response({
                'success': False,
                'error': 'Failed to generate calendar'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class CalendarSubscribeView(View):
    """
    Subscription endpoint for calendar apps
    
    GET /calendar/subscribe/<token>/
    
    Note: Uses Django View (not DRF APIView) to bypass content negotiation.
    Calendar apps like iOS Calendar send Accept: text/calendar headers
    which DRF doesn't understand, causing 406 Not Acceptable errors.
    """
    
    def get(self, request, token):
        """Serve calendar for subscription"""
        # Log the subscription request
        client_ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', 'unknown'))
        user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')
        accept_header = request.META.get('HTTP_ACCEPT', 'not set')
        logger.info(f"Calendar subscription request - Token: {token[:16]}..., IP: {client_ip}, Accept: {accept_header}, UA: {user_agent[:50]}")
        
        # Try user token first
        calendar_token = CalendarToken.objects.filter(
            token=token,
            is_active=True
        ).select_related('user').first()
        
        if calendar_token:
            logger.info(f"Token found - User: {calendar_token.user}, Type: {calendar_token.calendar_type}, Valid: {calendar_token.is_valid}")
            
            if not calendar_token.is_valid:
                logger.warning(f"Token invalid/expired - Token: {token[:16]}..., User: {calendar_token.user}")
                return HttpResponse(
                    "Calendar subscription expired or invalid",
                    status=410,
                    content_type='text/plain'
                )
            
            # Record access
            calendar_token.record_access()
            user = calendar_token.user
            
            try:
                cal_type = calendar_token.calendar_type
                logger.info(f"Generating calendar - Type: {cal_type}, User: {user.username if user else 'None'}")
                
                if cal_type == 'classes':
                    calendar = CalendarService.generate_class_schedule_calendar(user)
                elif cal_type == 'exams':
                    calendar = CalendarService.generate_exam_schedule_calendar(user)
                elif cal_type == 'events':
                    calendar = CalendarService.generate_events_calendar(include_past=False)
                elif cal_type in ('full', 'personal'):
                    calendar = CalendarService.generate_full_academic_calendar(user)
                else:
                    calendar = CalendarService.generate_full_academic_calendar(user)
                
                logger.info(f"Calendar generated successfully - Type: {cal_type}, User: {user.username if user else 'None'}")
                return CalendarExportService.get_subscription_response(calendar)
                
            except Exception as e:
                logger.exception(f"Error generating subscribed calendar - Token: {token[:16]}..., User: {user}, Type: {calendar_token.calendar_type}, Error: {str(e)}")
                return HttpResponse(
                    f"Error generating calendar: {str(e)}",
                    status=500,
                    content_type='text/plain'
                )
        
        # Try public token
        public_token = PublicCalendarToken.objects.filter(
            token=token,
            is_active=True
        ).first()
        
        if public_token:
            logger.info(f"Public token found - Type: {public_token.calendar_type}")
            public_token.record_access()
            
            try:
                if public_token.calendar_type == 'public_events':
                    calendar = CalendarService.generate_events_calendar(include_past=False)
                elif public_token.calendar_type == 'academic':
                    calendar = CalendarService.generate_exam_schedule_calendar(include_past=False)
                else:
                    calendar = CalendarService.generate_events_calendar(include_past=False)
                
                logger.info(f"Public calendar generated successfully - Type: {public_token.calendar_type}")
                return CalendarExportService.get_subscription_response(calendar)
                
            except Exception as e:
                logger.exception(f"Error generating public calendar - Type: {public_token.calendar_type}, Error: {str(e)}")
                return HttpResponse(
                    f"Error generating calendar: {str(e)}",
                    status=500,
                    content_type='text/plain'
                )
        
        # Token not found in either table
        logger.warning(f"Token not found - Token: {token}, IP: {client_ip}")
        
        # Log all existing tokens for debugging (only first 5)
        existing_tokens = CalendarToken.objects.values_list('token', flat=True)[:5]
        logger.debug(f"Sample existing tokens: {[t[:16] + '...' for t in existing_tokens]}")
        
        return HttpResponse(
            "Invalid calendar token",
            status=404,
            content_type='text/plain'
        )


class PublicEventsCalendarView(APIView):
    """
    Public events calendar (no auth required)
    
    GET /calendar/public/events/
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get public events calendar"""
        try:
            calendar = CalendarService.generate_events_calendar(include_past=False)
            
            # Check if download or subscribe
            if request.query_params.get('download'):
                return CalendarExportService.get_download_response(
                    calendar, 
                    "css_knust_events"
                )
            
            return CalendarExportService.get_subscription_response(calendar)
            
        except Exception as e:
            logger.exception(f"Error generating public events calendar: {e}")
            return Response({
                'success': False,
                'error': 'Failed to generate calendar'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AddSingleEventToCalendarView(APIView):
    """
    Generate .ics for a single event
    
    GET /calendar/event/<event_id>/
    """
    permission_classes = [AllowAny]
    
    def get(self, request, event_id):
        """Download single event as .ics"""
        from events.models import Event as EventModel
        from icalendar import Calendar, Event
        from datetime import timedelta
        import pytz
        
        TIMEZONE = pytz.timezone('Africa/Accra')
        
        try:
            evt = EventModel.objects.get(event_id=event_id)
        except EventModel.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Event not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Create calendar with single event
        cal = Calendar()
        cal.add('prodid', settings.ICAL_PRODID)
        cal.add('version', '2.0')
        cal.add('method', 'PUBLISH')
        
        event = Event()
        event.add('uid', f"{evt.event_id}@{settings.UID_DOMAIN}")
        
        summary = evt.event_name
        if evt.emoji:
            summary = f"{evt.emoji} {summary}"
        event.add('summary', summary)
        event.add('description', evt.description)
        
        # Location
        location_parts = []
        if evt.venue:
            location_parts.append(evt.venue)
        if evt.building:
            location_parts.append(evt.building)
        if location_parts:
            event.add('location', ', '.join(location_parts))
        
        # Dates
        start_dt = evt.event_date
        if start_dt.tzinfo is None:
            start_dt = TIMEZONE.localize(start_dt)
        
        if evt.event_end_date:
            end_dt = evt.event_end_date
            if end_dt.tzinfo is None:
                end_dt = TIMEZONE.localize(end_dt)
        else:
            end_dt = start_dt + timedelta(hours=2)
        
        event.add('dtstart', start_dt)
        event.add('dtend', end_dt)
        event.add('dtstamp', TIMEZONE.localize(evt.created_at.replace(tzinfo=None)) if evt.created_at.tzinfo else evt.created_at)
        
        if evt.registration_link:
            event.add('url', evt.registration_link)
        
        cal.add_component(event)
        
        # Return as downloadable file
        response = HttpResponse(
            cal.to_ical(),
            content_type='text/calendar; charset=utf-8'
        )
        safe_name = evt.event_name.replace(' ', '_')[:30]
        response['Content-Disposition'] = f'attachment; filename="{safe_name}.ics"'
        return response


class AddSingleExamToCalendarView(APIView):
    """
    Generate .ics for a single exam
    
    GET /calendar/exam/<exam_id>/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, exam_id):
        """Download single exam as .ics"""
        from timetable_system.models import ExaminationSchedule
        from icalendar import Calendar, Event, Alarm
        from datetime import timedelta
        import pytz
        
        TIMEZONE = pytz.timezone('Africa/Accra')
        
        try:
            exam = ExaminationSchedule.objects.select_related('course').get(id=exam_id)
        except ExaminationSchedule.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Exam not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if not exam.time:
            return Response({
                'success': False,
                'error': 'Exam date not set'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create calendar
        cal = Calendar()
        cal.add('prodid', settings.ICAL_PRODID)
        cal.add('version', '2.0')
        cal.add('method', 'PUBLISH')
        
        event = Event()
        event.add('uid', f"exam-{exam.id}@{settings.UID_DOMAIN}")
        
        course_code = exam.course.course_code if exam.course else "EXAM"
        course_name = exam.course.course_name if exam.course else "Examination"
        event.add('summary', f"EXAM: {course_code} - {course_name}")
        
        description = f"Course: {course_name}\nCode: {course_code}\nCollege: {exam.college}"
        if exam.room:
            description += f"\nRoom: {exam.room}"
        event.add('description', description)
        
        location = exam.college
        if exam.room:
            location += f", {exam.room}"
        event.add('location', location)
        
        start_dt = exam.time
        if start_dt.tzinfo is None:
            start_dt = TIMEZONE.localize(start_dt)
        end_dt = start_dt + timedelta(hours=3)
        
        event.add('dtstart', start_dt)
        event.add('dtend', end_dt)
        event.add('dtstamp', TIMEZONE.localize(datetime.now()))
        
        # Add reminder
        alarm = Alarm()
        alarm.add('action', 'DISPLAY')
        alarm.add('description', f"EXAM in 1 day: {course_code}")
        alarm.add('trigger', timedelta(days=-1))
        event.add_component(alarm)
        
        cal.add_component(event)
        
        response = HttpResponse(
            cal.to_ical(),
            content_type='text/calendar; charset=utf-8'
        )
        response['Content-Disposition'] = f'attachment; filename="exam_{course_code}.ics"'
        return response


class CalendarReminderPreferencesView(APIView):
    """
    Manage user's calendar reminder preferences
    
    GET /calendar/reminder-preferences/
    PUT /calendar/reminder-preferences/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get user's reminder preferences"""
        from .models import CalendarReminderPreference
        
        prefs = CalendarReminderPreference.get_for_user(request.user)
        serializer = CalendarReminderPreferenceSerializer(prefs)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'message': 'Push notifications provide the most reliable reminders. Calendar app reminders may not work for subscribed calendars.'
        })
    
    def put(self, request):
        """Update user's reminder preferences"""
        from .models import CalendarReminderPreference
        
        prefs = CalendarReminderPreference.get_for_user(request.user)
        serializer = CalendarReminderPreferenceSerializer(data=request.data, partial=True)
        
        if serializer.is_valid():
            validated = serializer.validated_data
            
            # Update preferences
            for field in [
                'class_reminders_enabled', 'class_reminder_times',
                'exam_reminders_enabled', 'exam_reminder_times',
                'event_reminders_enabled', 'event_reminder_times',
                'push_reminders_enabled'
            ]:
                if field in validated:
                    setattr(prefs, field, validated[field])
            
            prefs.save()
            
            # Trigger re-sync of reminders for this user
            from .tasks import sync_user_reminders
            sync_user_reminders.delay(str(request.user.id))
            
            return Response({
                'success': True,
                'data': CalendarReminderPreferenceSerializer(prefs).data,
                'message': 'Reminder preferences updated. Your reminders will be refreshed.'
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ScheduledRemindersView(APIView):
    """
    View user's scheduled reminders
    
    GET /calendar/scheduled-reminders/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get user's upcoming scheduled reminders"""
        from .reminder_service import CalendarReminderService
        
        reminder_type = request.query_params.get('type')  # 'class', 'exam', 'event'
        limit = int(request.query_params.get('limit', 20))
        
        reminders = CalendarReminderService.get_user_upcoming_reminders(
            user=request.user,
            reminder_type=reminder_type,
            limit=min(limit, 50)  # Cap at 50
        )
        
        serializer = ScheduledReminderSerializer(reminders, many=True)
        
        return Response({
            'success': True,
            'count': len(reminders),
            'data': serializer.data
        })


class SyncRemindersView(APIView):
    """
    Manually trigger reminder sync for the user
    
    POST /calendar/sync-reminders/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Trigger reminder sync"""
        from .tasks import sync_user_reminders
        
        # Trigger async sync
        sync_user_reminders.delay(str(request.user.id))
        
        return Response({
            'success': True,
            'message': 'Reminder sync initiated. Your reminders will be updated shortly.'
        })


# Import datetime for the exam view
from datetime import datetime
