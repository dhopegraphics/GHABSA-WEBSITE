from django.shortcuts import render, redirect
from django.utils import timezone
from django.template.loader import render_to_string
from rest_framework import generics
from core.serializers import ContactUsSerializer
from core.models import ContactUs, NotifyUser
from rest_framework import generics
from django.core.mail import EmailMessage
from django.conf import settings
from utils.utils import send_sms_message, personalize_message, message_has_placeholders
from core.throlling import ContactUsThrottle
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Q
from accounts.models import CustomUser
from academics.models import Course
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)


class ContactUsCreateView(generics.CreateAPIView):
    queryset = ContactUs.objects.all()
    serializer_class = ContactUsSerializer
    throttle_classes = [ContactUsThrottle]

    def perform_create(self, serializer):
        contact = serializer.save()
        logger.info(f"Contact form submitted: phone={contact.phone}, name={contact.name}")

        # Try to send SMS, but don't fail if SMS service is down
        try:
            send_sms_message(
                str(contact.phone),
                "contact_us_response.txt",
                {
                    "name": contact.name,
                    "phone": str(contact.phone),
                    "message": contact.message,
                },
            )
            logger.info(f"SMS sent successfully to {contact.phone}")
        except Exception as e:
            # Log the error but don't stop the contact form submission
            logger.error(f"SMS sending failed for {contact.phone}: {str(e)}")
            # Contact is already saved, so form submission succeeds
        

        subject = "New Society Report Message Received"
        html_content = render_to_string(
            "contact_us_alert.html",
            {
                "name": contact.name,
                "phone": str(contact.phone),
                "message": contact.message,
                "current_year": timezone.now().year,
            },
        )

        email = EmailMessage(
            subject=subject,
            body=html_content,
            from_email=settings.EMAIL_HOST_USER,
            to=["info@thecssknust.com"],
        )
        email.content_subtype = "html"
        email.send()


# =====================
# Bulk Notification Views
# =====================

@staff_member_required
def bulk_notify_view(request):
    """
    View for bulk sending notifications to filtered users
    Allows filtering by: year, program, group, course, gender, or specific users
    """
    
    context = {
        'title': 'Bulk Notification System',
        'programs': CustomUser.PROGRAM_CHOICES,
        'groups': CustomUser.GROUP_CHOICES,
        'genders': CustomUser.GENDER_CHOICES,
        'years': [1, 2, 3, 4],  # Year 1, 2, 3, 4
        'courses': Course.objects.all().order_by('course_code'),
        'channel_choices': [
            ('sms', 'SMS'),
            ('push', 'Push Notification'),
            ('email', 'Email'),
            ('both', 'SMS & Push Notification'),
            ('sms_email', 'SMS & Email'),
            ('push_email', 'Push & Email'),
            ('all', 'SMS, Push & Email'),
        ],
    }
    
    if request.method == 'POST':
        # Get form data
        filter_type = request.POST.get('filter_type')
        notification_title = request.POST.get('notification_title', '').strip()
        notification_message = request.POST.get('notification_message', '').strip()
        channel = request.POST.get('channel', 'sms')
        is_priority = request.POST.get('is_priority') == 'on'
        action = request.POST.get('action', 'draft')
        
        # Validate required fields
        if not notification_message:
            messages.error(request, '❌ Message is required!')
            return render(request, 'admin/core/bulk_notify.html', context)
        
        # Build query based on filter type
        users_query = CustomUser.objects.filter(is_active=True)
        filter_description = ""
        
        if filter_type == 'all':
            filter_description = "All Active Users"
            
        elif filter_type == 'unverified_phone':
            users_query = users_query.filter(phone_confirm=False)
            filter_description = "Users with Unverified Phone Numbers"
            
        elif filter_type == 'year':
            year = request.POST.get('year')
            if year:
                # Calculate users in specific year
                current_year = timezone.now().year
                graduation_year = current_year + (4 - int(year))
                users_query = users_query.filter(graduation_year=graduation_year)
                filter_description = f"Year {year} Students"
            else:
                messages.error(request, '❌ Please select a year!')
                return render(request, 'admin/core/bulk_notify.html', context)
                
        elif filter_type == 'program':
            program = request.POST.get('program')
            if program:
                users_query = users_query.filter(program=program)
                program_name = dict(CustomUser.PROGRAM_CHOICES).get(program, program)
                filter_description = f"{program_name} Students"
            else:
                messages.error(request, '❌ Please select a program!')
                return render(request, 'admin/core/bulk_notify.html', context)
                
        elif filter_type == 'group':
            group = request.POST.get('group')
            if group:
                users_query = users_query.filter(group=group)
                group_name = dict(CustomUser.GROUP_CHOICES).get(group, group)
                filter_description = f"{group_name} Students"
            else:
                messages.error(request, '❌ Please select a group!')
                return render(request, 'admin/core/bulk_notify.html', context)
                
        elif filter_type == 'year_group':
            year = request.POST.get('year')
            group = request.POST.get('group')
            if year and group:
                current_year = timezone.now().year
                graduation_year = current_year + (4 - int(year))
                users_query = users_query.filter(
                    graduation_year=graduation_year,
                    group=group
                )
                group_name = dict(CustomUser.GROUP_CHOICES).get(group, group)
                filter_description = f"Year {year} - {group_name}"
            else:
                messages.error(request, '❌ Please select both year and group!')
                return render(request, 'admin/core/bulk_notify.html', context)
                
        elif filter_type == 'year_program':
            year = request.POST.get('year')
            program = request.POST.get('program')
            if year and program:
                current_year = timezone.now().year
                graduation_year = current_year + (4 - int(year))
                users_query = users_query.filter(
                    graduation_year=graduation_year,
                    program=program
                )
                program_name = dict(CustomUser.PROGRAM_CHOICES).get(program, program)
                filter_description = f"Year {year} - {program_name}"
            else:
                messages.error(request, '❌ Please select both year and program!')
                return render(request, 'admin/core/bulk_notify.html', context)
                
        elif filter_type == 'course':
            course_id = request.POST.get('course')
            if course_id:
                try:
                    course = Course.objects.get(course_id=course_id)
                    filter_description = f"Students taking {course.course_code} - {course.course_title}"
                    
                    # Filter by year and program based on course
                    messages.warning(request, 
                        '⚠️ Note: Course-based filtering shows all active students. '
                        'Consider implementing a proper enrollment system for accuracy.'
                    )
                except Course.DoesNotExist:
                    messages.error(request, '❌ Course not found!')
                    return render(request, 'admin/core/bulk_notify.html', context)
            else:
                messages.error(request, '❌ Please select a course!')
                return render(request, 'admin/core/bulk_notify.html', context)
                
        elif filter_type == 'gender':
            gender = request.POST.get('gender')
            if gender:
                users_query = users_query.filter(gender=gender)
                gender_name = dict(CustomUser.GENDER_CHOICES).get(gender, gender)
                filter_description = f"{gender_name} Students"
            else:
                messages.error(request, '❌ Please select a gender!')
                return render(request, 'admin/core/bulk_notify.html', context)
                
        elif filter_type == 'custom':
            # Custom user selection by phone numbers or IDs
            user_identifiers = request.POST.get('user_identifiers', '').strip()
            if user_identifiers:
                # Split by comma or newline
                identifiers = [x.strip() for x in user_identifiers.replace('\n', ',').split(',') if x.strip()]
                
                # Try to match by phone, student_id, or index_number
                users_query = users_query.filter(
                    Q(phone__in=identifiers) |
                    Q(student_id__in=identifiers) |
                    Q(index_number__in=identifiers)
                )
                filter_description = f"Custom Selection ({len(identifiers)} identifiers)"
            else:
                messages.error(request, '❌ Please enter user identifiers!')
                return render(request, 'admin/core/bulk_notify.html', context)
        
        # ========================================
        # Incomplete Profile Field Filters
        # ========================================
        elif filter_type == 'missing_program':
            users_query = users_query.filter(Q(program__isnull=True) | Q(program=''))
            filter_description = "Users Missing Program"
            
        elif filter_type == 'missing_gender':
            users_query = users_query.filter(Q(gender__isnull=True) | Q(gender=''))
            filter_description = "Users Missing Gender"
            
        elif filter_type == 'missing_student_id':
            users_query = users_query.filter(Q(student_id__isnull=True) | Q(student_id=''))
            filter_description = "Users Missing Student ID"
            
        elif filter_type == 'missing_index_number':
            users_query = users_query.filter(Q(index_number__isnull=True) | Q(index_number=''))
            filter_description = "Users Missing Index Number"
            
        elif filter_type == 'missing_student_email':
            users_query = users_query.filter(Q(student_email__isnull=True) | Q(student_email=''))
            filter_description = "Users Missing Student Email"
            
        elif filter_type == 'missing_personal_email':
            users_query = users_query.filter(Q(personal_email__isnull=True) | Q(personal_email=''))
            filter_description = "Users Missing Personal Email"
            
        elif filter_type == 'missing_any_field':
            # Users missing ANY of the important profile fields
            users_query = users_query.filter(
                Q(program__isnull=True) | Q(program='') |
                Q(gender__isnull=True) | Q(gender='') |
                Q(student_id__isnull=True) | Q(student_id='') |
                Q(index_number__isnull=True) | Q(index_number='') |
                Q(student_email__isnull=True) | Q(student_email='') |
                Q(personal_email__isnull=True) | Q(personal_email='')
            )
            filter_description = "Users Missing Any Profile Field"
        
        else:
            messages.error(request, '❌ Invalid filter type!')
            return render(request, 'admin/core/bulk_notify.html', context)
        
        # Get final user list
        recipients = users_query.distinct()
        recipient_count = recipients.count()
        
        if recipient_count == 0:
            messages.warning(request, f'⚠️ No users found matching filter: {filter_description}')
            return render(request, 'admin/core/bulk_notify.html', context)
        
        # Check email rate limits if sending via email
        if channel in ['email', 'sms_email', 'push_email', 'all'] and action == 'send':
            from utils.utils import get_email_rate_status, create_email_batch
            rate_status = get_email_rate_status()
            
            # For email-only channel, use the batch system
            if channel == 'email':
                # Filter only users with personal email for batch
                email_recipients = recipients.exclude(
                    Q(personal_email__isnull=True) | Q(personal_email='')
                )
                email_count = email_recipients.count()
                
                if email_count == 0:
                    messages.warning(request, 
                        f'⚠️ No users with personal email found matching filter: {filter_description}'
                    )
                    return render(request, 'admin/core/bulk_notify.html', context)
                
                # Create batch with personalized messages if needed
                batch_message = notification_message
                
                # Create the email batch
                batch = create_email_batch(
                    title=f"Bulk: {filter_description[:150]}",
                    subject=notification_title or "CSS KNUST Notification",
                    message=batch_message,
                    recipients_queryset=email_recipients,
                    created_by=request.user,
                    filter_description=filter_description,
                    channel="email",
                    start_immediately=(action == 'send')
                )
                
                action_text = "created and started" if action == 'send' else "created"
                messages.success(request, 
                    f'✅ Email batch {action_text} with {batch.total_recipients} recipients | '
                    f'Filter: {filter_description}'
                )
                
                return redirect(f'/executive-dashboard-cb/core/emailbatch/{batch.id}/change/')
            
            # For combined channels with email, show warning
            estimated_emails = recipient_count
            
            if estimated_emails > rate_status['remaining_today']:
                messages.warning(request, 
                    f'⚠️ Email limit warning: You may send ~{rate_status["remaining_today"]} more emails today. '
                    f'This batch has {recipient_count} users. '
                    f'Consider using "Email" channel only for better tracking and resume capability.'
                )
            
            if recipient_count > 50:
                messages.info(request, 
                    f'📧 Large batch: {recipient_count} recipients. For email-only sends, use the "Email" channel '
                    f'for better tracking and resume capability.'
                )
        
        # Check if this is a missing field filter that needs personalization
        is_missing_filter = filter_type and filter_type.startswith('missing_')
        
        # Check if message contains any personalization placeholders
        has_personalization = message_has_placeholders(notification_message)
        
        # Create notifications for all recipients
        notifications_created = 0
        for user in recipients:
            # Personalize message if it contains placeholders
            personalized_message = notification_message
            if is_missing_filter or has_personalization:
                # Use centralized personalization for all placeholders
                personalized_message = personalize_message(notification_message, user)
            
            NotifyUser.objects.create(
                recipient=user,
                title=notification_title if channel in ['push', 'both'] else None,
                message=personalized_message,
                channel=channel,
                action=action,
                is_priority=is_priority,
            )
            notifications_created += 1
        
        # Success message
        channel_names = {
            'sms': 'SMS', 
            'push': 'Push', 
            'email': 'Email',
            'both': 'SMS & Push', 
            'sms_email': 'SMS & Email',
            'push_email': 'Push & Email',
            'all': 'SMS, Push & Email'
        }
        channel_name = channel_names.get(channel, channel)
        action_text = "sent" if action == "send" else "saved as draft"
        priority_text = " (PRIORITY)" if is_priority else ""
        
        messages.success(request, 
            f'✅ Successfully {action_text} {notifications_created} notification(s) via {channel_name}{priority_text} | '
            f'Filter: {filter_description} | Recipients: {recipient_count} users'
        )
        
        # Redirect to notification list
        return redirect('/executive-dashboard-cb/core/notifyuser/')
    
    # GET request - show form
    return render(request, 'admin/core/bulk_notify.html', context)


@staff_member_required
def preview_recipients(request):
    """
    AJAX endpoint to preview recipients based on current filter selection
    Returns count and sample of users who will receive the notification
    """
    
    filter_type = request.GET.get('filter_type')
    
    users_query = CustomUser.objects.filter(is_active=True)
    
    if filter_type == 'unverified_phone':
        users_query = users_query.filter(phone_confirm=False)
    
    elif filter_type == 'year':
        year = request.GET.get('year')
        if year:
            current_year = timezone.now().year
            graduation_year = current_year + (4 - int(year))
            users_query = users_query.filter(graduation_year=graduation_year)
            
    elif filter_type == 'program':
        program = request.GET.get('program')
        if program:
            users_query = users_query.filter(program=program)
            
    elif filter_type == 'group':
        group = request.GET.get('group')
        if group:
            users_query = users_query.filter(group=group)
            
    elif filter_type == 'year_group':
        year = request.GET.get('year')
        group = request.GET.get('group')
        if year and group:
            current_year = timezone.now().year
            graduation_year = current_year + (4 - int(year))
            users_query = users_query.filter(
                graduation_year=graduation_year,
                group=group
            )
            
    elif filter_type == 'year_program':
        year = request.GET.get('year')
        program = request.GET.get('program')
        if year and program:
            current_year = timezone.now().year
            graduation_year = current_year + (4 - int(year))
            users_query = users_query.filter(
                graduation_year=graduation_year,
                program=program
            )
            
    elif filter_type == 'gender':
        gender = request.GET.get('gender')
        if gender:
            users_query = users_query.filter(gender=gender)
    
    # ========================================
    # Incomplete Profile Field Filters (Preview)
    # ========================================
    elif filter_type == 'missing_program':
        users_query = users_query.filter(Q(program__isnull=True) | Q(program=''))
        
    elif filter_type == 'missing_gender':
        users_query = users_query.filter(Q(gender__isnull=True) | Q(gender=''))
        
    elif filter_type == 'missing_student_id':
        users_query = users_query.filter(Q(student_id__isnull=True) | Q(student_id=''))
        
    elif filter_type == 'missing_index_number':
        users_query = users_query.filter(Q(index_number__isnull=True) | Q(index_number=''))
        
    elif filter_type == 'missing_student_email':
        users_query = users_query.filter(Q(student_email__isnull=True) | Q(student_email=''))
        
    elif filter_type == 'missing_personal_email':
        users_query = users_query.filter(Q(personal_email__isnull=True) | Q(personal_email=''))
        
    elif filter_type == 'missing_any_field':
        users_query = users_query.filter(
            Q(program__isnull=True) | Q(program='') |
            Q(gender__isnull=True) | Q(gender='') |
            Q(student_id__isnull=True) | Q(student_id='') |
            Q(index_number__isnull=True) | Q(index_number='') |
            Q(student_email__isnull=True) | Q(student_email='') |
            Q(personal_email__isnull=True) | Q(personal_email='')
        )
    
    recipients = users_query.distinct()
    count = recipients.count()
    
    # Get sample of recipients (first 5)
    sample = []
    for user in recipients[:5]:
        user_data = {
            'name': f"{user.first_name} {user.last_name}",
            'phone': str(user.phone),
            'year': user.get_year(),
            'program': user.get_program_display_name() if user.program else 'N/A',
            'group': user.get_group_display_name() if user.group else 'N/A',
        }
        
        # Add missing fields info for incomplete profile filters
        if filter_type and filter_type.startswith('missing_'):
            missing_fields = []
            if not user.program:
                missing_fields.append('Program')
            if not user.gender:
                missing_fields.append('Gender')
            if not user.student_id:
                missing_fields.append('Student ID')
            if not user.index_number:
                missing_fields.append('Index Number')
            if not user.student_email:
                missing_fields.append('Student Email')
            if not user.personal_email:
                missing_fields.append('Personal Email')
            user_data['missing_fields'] = missing_fields
        
        sample.append(user_data)
    
    return JsonResponse({
        'count': count,
        'sample': sample,
        'is_missing_filter': filter_type.startswith('missing_') if filter_type else False,
    })


# =====================
# BATCH EMAIL VIEWS
# =====================

@staff_member_required
def create_email_batch_view(request):
    """
    View for creating email batches with recipient filtering.
    Similar to bulk_notify_view but creates a tracked batch instead.
    """
    from utils.utils import create_email_batch, get_email_rate_status
    from academics.models import Course
    
    context = {
        'title': 'Create Email Batch',
        'programs': CustomUser.PROGRAM_CHOICES,
        'groups': CustomUser.GROUP_CHOICES,
        'genders': CustomUser.GENDER_CHOICES,
        'years': [1, 2, 3, 4],  # Year 1, 2, 3, 4
        'courses': Course.objects.all().order_by('course_code'),
        'rate_status': get_email_rate_status(),
    }
    
    if request.method == 'POST':
        # Get form data
        filter_type = request.POST.get('filter_type')
        batch_title = request.POST.get('batch_title', '').strip()
        email_subject = request.POST.get('email_subject', '').strip()
        email_message = request.POST.get('email_message', '').strip()
        start_immediately = request.POST.get('start_immediately') == 'on'
        
        # Validate required fields
        if not batch_title:
            messages.error(request, '❌ Batch title is required!')
            return render(request, 'admin/core/create_email_batch.html', context)
        
        if not email_subject:
            messages.error(request, '❌ Email subject is required!')
            return render(request, 'admin/core/create_email_batch.html', context)
        
        if not email_message:
            messages.error(request, '❌ Email message is required!')
            return render(request, 'admin/core/create_email_batch.html', context)
        
        # Build query based on filter type (same logic as bulk_notify_view)
        users_query = CustomUser.objects.filter(is_active=True)
        filter_description = ""
        
        # Filter only users with personal email
        users_query = users_query.exclude(
            Q(personal_email__isnull=True) | Q(personal_email='')
        )
        
        if filter_type == 'all':
            filter_description = "All Active Users with Personal Email"
            
        elif filter_type == 'year':
            year = request.POST.get('year')
            if year:
                current_year = timezone.now().year
                graduation_year = current_year + (4 - int(year))
                users_query = users_query.filter(graduation_year=graduation_year)
                filter_description = f"Year {year} Students"
            else:
                messages.error(request, '❌ Please select a year!')
                return render(request, 'admin/core/create_email_batch.html', context)
                
        elif filter_type == 'program':
            program = request.POST.get('program')
            if program:
                users_query = users_query.filter(program=program)
                program_name = dict(CustomUser.PROGRAM_CHOICES).get(program, program)
                filter_description = f"{program_name} Students"
            else:
                messages.error(request, '❌ Please select a program!')
                return render(request, 'admin/core/create_email_batch.html', context)
                
        elif filter_type == 'group':
            group = request.POST.get('group')
            if group:
                users_query = users_query.filter(group=group)
                group_name = dict(CustomUser.GROUP_CHOICES).get(group, group)
                filter_description = f"{group_name} Students"
            else:
                messages.error(request, '❌ Please select a group!')
                return render(request, 'admin/core/create_email_batch.html', context)
                
        elif filter_type == 'year_group':
            year = request.POST.get('year')
            group = request.POST.get('group')
            if year and group:
                current_year = timezone.now().year
                graduation_year = current_year + (4 - int(year))
                users_query = users_query.filter(graduation_year=graduation_year, group=group)
                group_name = dict(CustomUser.GROUP_CHOICES).get(group, group)
                filter_description = f"Year {year} - {group_name}"
            else:
                messages.error(request, '❌ Please select both year and group!')
                return render(request, 'admin/core/create_email_batch.html', context)
                
        elif filter_type == 'year_program':
            year = request.POST.get('year')
            program = request.POST.get('program')
            if year and program:
                current_year = timezone.now().year
                graduation_year = current_year + (4 - int(year))
                users_query = users_query.filter(graduation_year=graduation_year, program=program)
                program_name = dict(CustomUser.PROGRAM_CHOICES).get(program, program)
                filter_description = f"Year {year} - {program_name}"
            else:
                messages.error(request, '❌ Please select both year and program!')
                return render(request, 'admin/core/create_email_batch.html', context)
                
        elif filter_type == 'gender':
            gender = request.POST.get('gender')
            if gender:
                users_query = users_query.filter(gender=gender)
                gender_name = dict(CustomUser.GENDER_CHOICES).get(gender, gender)
                filter_description = f"{gender_name} Students"
            else:
                messages.error(request, '❌ Please select a gender!')
                return render(request, 'admin/core/create_email_batch.html', context)
                
        elif filter_type == 'custom':
            user_identifiers = request.POST.get('user_identifiers', '').strip()
            if user_identifiers:
                identifiers = [x.strip() for x in user_identifiers.replace('\n', ',').split(',') if x.strip()]
                users_query = users_query.filter(
                    Q(phone__in=identifiers) |
                    Q(student_id__in=identifiers) |
                    Q(index_number__in=identifiers)
                )
                filter_description = f"Custom Selection ({len(identifiers)} identifiers)"
            else:
                messages.error(request, '❌ Please enter user identifiers!')
                return render(request, 'admin/core/create_email_batch.html', context)
        
        else:
            messages.error(request, '❌ Invalid filter type!')
            return render(request, 'admin/core/create_email_batch.html', context)
        
        # Get final user list
        recipients = users_query.distinct()
        recipient_count = recipients.count()
        
        if recipient_count == 0:
            messages.warning(request, f'⚠️ No users found matching filter: {filter_description}')
            return render(request, 'admin/core/create_email_batch.html', context)
        
        # Create the batch
        batch = create_email_batch(
            title=batch_title,
            subject=email_subject,
            message=email_message,
            recipients_queryset=recipients,
            created_by=request.user,
            filter_description=filter_description,
            channel="email",
            start_immediately=start_immediately
        )
        
        action_text = "created and started" if start_immediately else "created"
        messages.success(request, 
            f'✅ Email batch "{batch_title}" {action_text} with {batch.total_recipients} recipients | '
            f'Filter: {filter_description}'
        )
        
        return redirect(f'/executive-dashboard-cb/core/emailbatch/{batch.id}/change/')
    
    # GET request - show form
    return render(request, 'admin/core/create_email_batch.html', context)


@staff_member_required
def email_batch_status_api(request, batch_id):
    """
    API endpoint to get batch status for AJAX polling.
    """
    from utils.utils import get_batch_status
    return JsonResponse(get_batch_status(batch_id))
