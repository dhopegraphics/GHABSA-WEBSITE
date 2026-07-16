from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from accounts.models import CustomUser, FieldRequirementConfig
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta, datetime
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.contrib import messages
import json
import logging

logger = logging.getLogger(__name__)

# Import device admin
from accounts.device_admin import *  # noqa


def get_graduated_students_queryset(include_staff=False):
    """
    Get queryset of graduated students who are still marked as active.
    
    A student is considered graduated if their graduation_year < effective_year,
    where effective_year accounts for the academic year transition in December.
    """
    now = timezone.now()
    current_year = now.year
    current_month = now.month
    
    # After November 30th, use next year as effective year
    adjustment = 1 if (current_month == 12 or (current_month == 11 and now.day > 30)) else 0
    effective_year = current_year + adjustment
    
    # Find users who have graduated but are still active
    queryset = CustomUser.objects.filter(
        graduation_year__lt=effective_year,
        is_active=True,
    )
    
    # Optionally exclude staff members
    if not include_staff:
        queryset = queryset.filter(is_staff=False)
    
    return queryset, effective_year


@staff_member_required
@require_POST
def deactivate_graduated_students_view(request):
    """
    Admin view to deactivate graduated students via AJAX.
    Requires 'deactivate_graduated_students' permission or superuser status.
    """
    # Check permission
    if not (request.user.is_superuser or request.user.has_perm('accounts.deactivate_graduated_students')):
        return JsonResponse({
            'success': False,
            'error': "You don't have permission to deactivate graduated students."
        }, status=403)
    
    try:
        include_staff = request.POST.get('include_staff', 'false').lower() == 'true'
        dry_run = request.POST.get('dry_run', 'false').lower() == 'true'
        
        graduated_students, effective_year = get_graduated_students_queryset(include_staff)
        count = graduated_students.count()
        
        if count == 0:
            return JsonResponse({
                'success': True,
                'message': 'No graduated students found that need to be deactivated.',
                'deactivated_count': 0,
                'effective_year': effective_year,
            })
        
        if dry_run:
            # Return preview data
            students_preview = [
                {
                    'id': str(s.id),
                    'name': f"{s.first_name} {s.last_name}",
                    'phone': str(s.phone),
                    'graduation_year': s.graduation_year,
                    'program': s.get_program_display_name() if hasattr(s, 'get_program_display_name') else (s.program or ''),
                }
                for s in graduated_students[:50]  # Limit preview to 50 students
            ]
            return JsonResponse({
                'success': True,
                'dry_run': True,
                'count': count,
                'effective_year': effective_year,
                'students_preview': students_preview,
                'message': f'Found {count} graduated students that would be deactivated.',
            })
        
        # Perform the actual deactivation
        updated_count = graduated_students.update(is_active=False)
        
        # Log the action
        logger.info(
            f'Admin {request.user} deactivated {updated_count} graduated students. '
            f'Effective year: {effective_year}, Include staff: {include_staff}'
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully deactivated {updated_count} graduated students.',
            'deactivated_count': updated_count,
            'effective_year': effective_year,
            'include_staff': include_staff,
            'timestamp': timezone.now().isoformat(),
        })
        
    except Exception as e:
        logger.error(f'Error deactivating graduated students: {e}')
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)


# Clearable fields configuration - fields that can be bulk cleared
CLEARABLE_FIELDS = {
    'student_id': {
        'label': 'Student ID',
        'description': 'Clear Student ID field',
        'is_sensitive': True,
    },
    'index_number': {
        'label': 'Index Number',
        'description': 'Clear Index Number field',
        'is_sensitive': True,
    },
    'personal_email': {
        'label': 'Personal Email',
        'description': 'Clear Personal Email field',
        'is_sensitive': True,
    },
    'student_email': {
        'label': 'Student Email',
        'description': 'Clear Student Email field',
        'is_sensitive': True,
    },
    'program': {
        'label': 'Program',
        'description': 'Clear Program field (CS/IT)',
        'is_sensitive': False,
    },
    'group': {
        'label': 'Group',
        'description': 'Clear Group field (G1/G2)',
        'is_sensitive': False,
    },
    'gender': {
        'label': 'Gender',
        'description': 'Clear Gender field',
        'is_sensitive': False,
    },
    'middle_name': {
        'label': 'Middle Name',
        'description': 'Clear Middle Name field',
        'is_sensitive': False,
    },
    'phone_confirm': {
        'label': 'Phone Verification Status',
        'description': 'Reset phone verification to False',
        'is_sensitive': False,
        'clear_value': False,  # Special case: set to False instead of None
    },
}


@staff_member_required
@require_POST
def clear_field_data_view(request):
    """
    Admin view to clear (reset) specific field data for users filtered by graduation year.
    Requires 'change_customuser' permission or superuser status.
    """
    # Check permission
    if not (request.user.is_superuser or request.user.has_perm('accounts.change_customuser')):
        return JsonResponse({
            'success': False,
            'error': "You don't have permission to modify user data."
        }, status=403)
    
    try:
        field_name = request.POST.get('field_name', '').strip()
        graduation_year = request.POST.get('graduation_year', '').strip()
        dry_run = request.POST.get('dry_run', 'false').lower() == 'true'
        include_all_years = request.POST.get('include_all_years', 'false').lower() == 'true'
        
        # Validate field
        if not field_name:
            return JsonResponse({
                'success': False,
                'error': 'Field name is required.'
            }, status=400)
        
        if field_name not in CLEARABLE_FIELDS:
            return JsonResponse({
                'success': False,
                'error': f'Field "{field_name}" is not clearable. Valid fields: {list(CLEARABLE_FIELDS.keys())}'
            }, status=400)
        
        # Check sensitive field permission
        field_config = CLEARABLE_FIELDS[field_name]
        if field_config.get('is_sensitive', False):
            if not (request.user.is_superuser or request.user.has_perm('accounts.view_sensitive_student_data')):
                return JsonResponse({
                    'success': False,
                    'error': f"You don't have permission to modify sensitive field: {field_name}"
                }, status=403)
        
        # Build queryset
        queryset = CustomUser.objects.filter(is_staff=False)  # Exclude staff by default
        
        if not include_all_years:
            if not graduation_year:
                return JsonResponse({
                    'success': False,
                    'error': 'Graduation year is required (or select "All Years").'
                }, status=400)
            
            try:
                year_int = int(graduation_year)
                queryset = queryset.filter(graduation_year=year_int)
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid graduation year format.'
                }, status=400)
        
        # Filter to only users who have data in this field
        # For boolean fields like phone_confirm, check if it's True
        clear_value = field_config.get('clear_value', None)
        if clear_value is False:
            # For phone_confirm, we want to reset True -> False
            queryset = queryset.filter(**{field_name: True})
        elif clear_value is None:
            # For nullable fields, exclude already empty ones
            queryset = queryset.exclude(**{f"{field_name}__isnull": True}).exclude(**{field_name: ''})
        
        count = queryset.count()
        
        if count == 0:
            year_text = f"year {graduation_year}" if not include_all_years else "all years"
            return JsonResponse({
                'success': True,
                'message': f'No users found with data in "{field_config["label"]}" for {year_text}.',
                'cleared_count': 0,
            })
        
        if dry_run:
            # Return preview data
            users_preview = [
                {
                    'id': str(u.id),
                    'name': f"{u.first_name} {u.last_name}",
                    'phone': str(u.phone),
                    'graduation_year': u.graduation_year,
                    'current_value': str(getattr(u, field_name, '')),
                }
                for u in queryset[:50]  # Limit preview to 50 users
            ]
            return JsonResponse({
                'success': True,
                'dry_run': True,
                'count': count,
                'field_name': field_name,
                'field_label': field_config['label'],
                'graduation_year': graduation_year if not include_all_years else 'All',
                'users_preview': users_preview,
                'message': f'Found {count} users with data in "{field_config["label"]}" that would be cleared.',
            })
        
        # Perform the actual clear operation
        update_kwargs = {field_name: clear_value}
        updated_count = queryset.update(**update_kwargs)
        
        # Log the action
        year_text = f"year {graduation_year}" if not include_all_years else "all years"
        logger.info(
            f'Admin {request.user} cleared field "{field_name}" for {updated_count} users. '
            f'Filter: {year_text}'
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully cleared "{field_config["label"]}" for {updated_count} users.',
            'cleared_count': updated_count,
            'field_name': field_name,
            'graduation_year': graduation_year if not include_all_years else 'All',
            'timestamp': timezone.now().isoformat(),
        })
        
    except Exception as e:
        logger.error(f'Error clearing field data: {e}')
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)


@staff_member_required
def get_clearable_fields_info(request):
    """
    Return information about clearable fields including counts per graduation year.
    """
    if not (request.user.is_superuser or request.user.has_perm('accounts.change_customuser')):
        return JsonResponse({
            'success': False,
            'error': "Permission denied"
        }, status=403)
    
    has_sensitive_perm = (
        request.user.is_superuser or 
        request.user.has_perm('accounts.view_sensitive_student_data')
    )
    
    # Filter fields based on permissions
    available_fields = {}
    for key, config in CLEARABLE_FIELDS.items():
        if config.get('is_sensitive', False) and not has_sensitive_perm:
            continue
        available_fields[key] = {
            'label': config['label'],
            'description': config['description'],
        }
    
    # Get graduation years with user counts
    now = timezone.now()
    current_year = now.year
    adjustment = 1 if (now.month == 12 or (now.month == 11 and now.day > 30)) else 0
    effective_year = current_year + adjustment
    
    # Get years from effective_year to effective_year + 3 (Year 4 to Year 1)
    graduation_years = []
    for year in range(effective_year, effective_year + 4):
        count = CustomUser.objects.filter(graduation_year=year, is_staff=False).count()
        academic_year = effective_year + 3 - year + 1  # Calculate year 1-4
        graduation_years.append({
            'year': year,
            'count': count,
            'academic_year': f'Year {academic_year}'
        })
    
    return JsonResponse({
        'success': True,
        'clearable_fields': available_fields,
        'graduation_years': graduation_years,
        'effective_year': effective_year,
    })


@staff_member_required
def accounts_analytics(request):
    """
    Analytics dashboard for user accounts.
    Requires 'view_accounts_analytics' permission.
    """
    # Check permission
    if not (request.user.is_superuser or request.user.has_perm('accounts.view_accounts_analytics')):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("You don't have permission to view analytics.")
    
    # Get graduated students count for the dashboard
    graduated_active, effective_year = get_graduated_students_queryset(include_staff=False)
    graduated_active_count = graduated_active.count()
    
    # Total users
    total_users = CustomUser.objects.count()
    
    # Active vs Inactive users
    active_users = CustomUser.objects.filter(is_active=True).count()
    inactive_users = total_users - active_users
    
    # Phone verification status
    phone_confirmed = CustomUser.objects.filter(phone_confirm=True).count()
    phone_unconfirmed = total_users - phone_confirmed
    phone_confirmation_rate = (phone_confirmed / total_users * 100) if total_users > 0 else 0
    
    # Staff users
    staff_users = CustomUser.objects.filter(is_staff=True).count()
    non_staff_users = total_users - staff_users
    
    # Gender distribution
    gender_stats = CustomUser.objects.values('gender').annotate(count=Count('id'))
    male_count = next((item['count'] for item in gender_stats if item['gender'] == 'M'), 0)
    female_count = next((item['count'] for item in gender_stats if item['gender'] == 'F'), 0)
    other_gender_count = next((item['count'] for item in gender_stats if item['gender'] == 'O'), 0)
    unspecified_gender = total_users - (male_count + female_count + other_gender_count)
    
    # Program distribution
    program_stats = CustomUser.objects.values('program').annotate(count=Count('id'))
    cs_count = next((item['count'] for item in program_stats if item['program'] == 'CS'), 0)
    it_count = next((item['count'] for item in program_stats if item['program'] == 'IT'), 0)
    unspecified_program = total_users - (cs_count + it_count)
    
    # Missing Profile Fields Statistics
    from django.db.models import Q
    missing_program = CustomUser.objects.filter(Q(program__isnull=True) | Q(program='')).count()
    missing_gender = CustomUser.objects.filter(Q(gender__isnull=True) | Q(gender='')).count()
    missing_student_id = CustomUser.objects.filter(Q(student_id__isnull=True) | Q(student_id='')).count()
    missing_index_number = CustomUser.objects.filter(Q(index_number__isnull=True) | Q(index_number='')).count()
    missing_student_email = CustomUser.objects.filter(Q(student_email__isnull=True) | Q(student_email='')).count()
    missing_personal_email = CustomUser.objects.filter(Q(personal_email__isnull=True) | Q(personal_email='')).count()
    missing_any_field = CustomUser.objects.filter(
        Q(program__isnull=True) | Q(program='') |
        Q(gender__isnull=True) | Q(gender='') |
        Q(student_id__isnull=True) | Q(student_id='') |
        Q(index_number__isnull=True) | Q(index_number='') |
        Q(student_email__isnull=True) | Q(student_email='') |
        Q(personal_email__isnull=True) | Q(personal_email='')
    ).count()
    
    # Calculate profile completion rate
    complete_profiles = total_users - missing_any_field
    profile_completion_rate = (complete_profiles / total_users * 100) if total_users > 0 else 0
    
    # Graduation year distribution
    graduation_years = CustomUser.objects.values('graduation_year').annotate(
        count=Count('id')
    ).order_by('graduation_year')
    
    # Recent registrations (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_registrations = CustomUser.objects.filter(date_joined__gte=thirty_days_ago).count()
    
    # Last 7 days
    seven_days_ago = timezone.now() - timedelta(days=7)
    last_week_registrations = CustomUser.objects.filter(date_joined__gte=seven_days_ago).count()
    
    # Year distribution (by computed year, using the model helper)
    year_counts = {1: 0, 2: 0, 3: 0, 4: 0}
    for u in CustomUser.objects.all():
        try:
            yr = u.get_year()
            yr_int = int(yr) if yr else 0
            if yr_int in year_counts:
                year_counts[yr_int] += 1
        except Exception:
            # skip users with unavailable/invalid year
            continue

    year_1 = year_counts[1]
    year_2 = year_counts[2]
    year_3 = year_counts[3]
    year_4 = year_counts[4]

    # Program completion status: use the instance helper to determine completion
    completed_program = 0
    for u in CustomUser.objects.all():
        try:
            if u.has_completed_program():
                completed_program += 1
        except Exception:
            continue

    in_progress = total_users - completed_program

    # Monthly registration trend (last 6 months) — use month boundaries for accuracy
    monthly_data = []
    now = timezone.now()
    tz = now.tzinfo
    for i in range(5, -1, -1):
        # compute year and month for the month i months ago
        month = now.month - i
        year = now.year
        while month <= 0:
            month += 12
            year -= 1

        month_start = timezone.make_aware(datetime(year, month, 1), timezone.get_current_timezone())
        # compute start of next month
        if month == 12:
            next_month_start = timezone.make_aware(datetime(year + 1, 1, 1), timezone.get_current_timezone())
        else:
            next_month_start = timezone.make_aware(datetime(year, month + 1, 1), timezone.get_current_timezone())

        # For the most recent month, cap the end at 'now' to get partial-month counts
        month_end = min(next_month_start, now)

        month_count = CustomUser.objects.filter(
            date_joined__gte=month_start,
            date_joined__lt=month_end
        ).count()

        monthly_data.append({
            'month': month_start.strftime('%b %Y'),
            'count': month_count
        })
    
    # Users by program AND gender (cross-analysis)
    cs_male = CustomUser.objects.filter(program='CS', gender='M').count()
    cs_female = CustomUser.objects.filter(program='CS', gender='F').count()
    it_male = CustomUser.objects.filter(program='IT', gender='M').count()
    it_female = CustomUser.objects.filter(program='IT', gender='F').count()
    
    context = {
        'title': 'Accounts Analytics Dashboard',
        # Summary stats
        'total_users': total_users,
        'active_users': active_users,
        'inactive_users': inactive_users,
        'active_percentage': (active_users / total_users * 100) if total_users > 0 else 0,
        
        # Phone verification
        'phone_confirmed': phone_confirmed,
        'phone_unconfirmed': phone_unconfirmed,
        'phone_confirmation_rate': phone_confirmation_rate,
        
        # Staff
        'staff_users': staff_users,
        'non_staff_users': non_staff_users,
        
        # Gender
        'male_count': male_count,
        'female_count': female_count,
        'other_gender_count': other_gender_count,
        'unspecified_gender': unspecified_gender,
        
        # Program
        'cs_count': cs_count,
        'it_count': it_count,
        'unspecified_program': unspecified_program,
        
        # Graduation years
        'graduation_years': graduation_years,
        
        # Recent activity
        'recent_registrations': recent_registrations,
        'last_week_registrations': last_week_registrations,
        
        # Year distribution
        'year_1': year_1,
        'year_2': year_2,
        'year_3': year_3,
        'year_4': year_4,
        
        # Completion
        'completed_program': completed_program,
        'in_progress': in_progress,
        
        # Monthly trend
        'monthly_data': monthly_data,
        
        # Cross-analysis
        'cs_male': cs_male,
        'cs_female': cs_female,
        'it_male': it_male,
        'it_female': it_female,
        
        # Missing Profile Fields
        'missing_program': missing_program,
        'missing_gender': missing_gender,
        'missing_student_id': missing_student_id,
        'missing_index_number': missing_index_number,
        'missing_student_email': missing_student_email,
        'missing_personal_email': missing_personal_email,
        'missing_any_field': missing_any_field,
        'complete_profiles': complete_profiles,
        'profile_completion_rate': profile_completion_rate,
        
        # Graduated students management
        'graduated_active_count': graduated_active_count,
        'effective_year': effective_year,
        'can_deactivate_graduates': (
            request.user.is_superuser or 
            request.user.has_perm('accounts.deactivate_graduated_students')
        ),
    }
    # Build detail payloads for interactive cards (limited to first 200 items each)
    def _user_dict(u):
        return {
            'id': str(u.id),
            'name': f"{u.first_name} {u.last_name}",
            'phone': str(u.phone) if u.phone else None,
            'program': u.get_program_display_name() if hasattr(u, 'get_program_display_name') else (u.program or ''),
            'graduation_year': u.graduation_year,
            'date_joined': u.date_joined.isoformat() if hasattr(u, 'date_joined') and u.date_joined else None,
        }

    # Collect lists (kept small to avoid huge payloads)
    recent_users = list(CustomUser.objects.order_by('-date_joined')[:200])
    recent_users_list = [_user_dict(u) for u in recent_users]

    active_users_list = [_user_dict(u) for u in CustomUser.objects.filter(is_active=True).order_by('-date_joined')[:200]]
    phone_verified_list = [_user_dict(u) for u in CustomUser.objects.filter(phone_confirm=True).order_by('-date_joined')[:200]]
    staff_users_list = [_user_dict(u) for u in CustomUser.objects.filter(is_staff=True).order_by('-date_joined')[:200]]

    completed_list = []
    for u in CustomUser.objects.order_by('-date_joined'):
        try:
            if u.has_completed_program():
                completed_list.append(_user_dict(u))
        except Exception:
            continue
        if len(completed_list) >= 200:
            break

    in_progress_list = []
    for u in CustomUser.objects.order_by('-date_joined'):
        try:
            if not u.has_completed_program():
                in_progress_list.append(_user_dict(u))
        except Exception:
            continue
        if len(in_progress_list) >= 200:
            break

    # Missing fields lists
    missing_program_list = [_user_dict(u) for u in CustomUser.objects.filter(Q(program__isnull=True) | Q(program='')).order_by('-date_joined')[:200]]
    missing_gender_list = [_user_dict(u) for u in CustomUser.objects.filter(Q(gender__isnull=True) | Q(gender='')).order_by('-date_joined')[:200]]
    missing_student_id_list = [_user_dict(u) for u in CustomUser.objects.filter(Q(student_id__isnull=True) | Q(student_id='')).order_by('-date_joined')[:200]]
    missing_index_number_list = [_user_dict(u) for u in CustomUser.objects.filter(Q(index_number__isnull=True) | Q(index_number='')).order_by('-date_joined')[:200]]
    missing_student_email_list = [_user_dict(u) for u in CustomUser.objects.filter(Q(student_email__isnull=True) | Q(student_email='')).order_by('-date_joined')[:200]]
    missing_personal_email_list = [_user_dict(u) for u in CustomUser.objects.filter(Q(personal_email__isnull=True) | Q(personal_email='')).order_by('-date_joined')[:200]]

    details_payload = {
        'total_users': recent_users_list,
        'active_users': active_users_list,
        'phone_verified': phone_verified_list,
        'staff_members': staff_users_list,
        'completed_program': completed_list,
        'in_progress': in_progress_list,
        # Missing fields
        'missing_program': missing_program_list,
        'missing_gender': missing_gender_list,
        'missing_student_id': missing_student_id_list,
        'missing_index_number': missing_index_number_list,
        'missing_student_email': missing_student_email_list,
        'missing_personal_email': missing_personal_email_list,
    }

    context['details_payload'] = details_payload
    # Provide a JSON string for templates without relying on the json_script tag
    context['details_payload_json'] = json.dumps(details_payload, default=str)

    return render(request, 'admin/accounts/analytics.html', context)


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = [
        "first_name",
        "middle_name",
        "last_name",
        "phone",
        "student_id_display",
        "index_number_display",
        "program",
        "group",
        "gender",
        "current_semester",
        "completed_semesters_display",
        "is_active",
        "phone_confirm",
        "is_staff",
        "last_login",
    ]
    ordering = ["-last_login"]
    
    list_filter = [
        "is_active",
        "is_staff",
        "phone_confirm",
        "program",
        "group",
        "gender",
        "graduation_year",
    ]

    search_fields = [
        "first_name",
        "last_name",
        "phone",
        "student_id",
        "index_number",
        "student_email",
        "personal_email",
    ]

    readonly_fields = ["current_semester", "completed_semesters_display", "program_completion_status"]
    
    change_list_template = "admin/accounts/customuser/change_list.html"
    
    actions = ['verify_phone_numbers', 'unverify_phone_numbers', 'deactivate_selected_graduates']
    
    @admin.action(description='✅ Verify phone numbers for selected users')
    def verify_phone_numbers(self, request, queryset):
        """Bulk action to verify phone numbers for selected users"""
        updated = queryset.update(phone_confirm=True)
        self.message_user(
            request,
            f'Successfully verified phone numbers for {updated} user(s).',
            level='success'
        )
    
    @admin.action(description='❌ Unverify phone numbers for selected users')
    def unverify_phone_numbers(self, request, queryset):
        """Bulk action to unverify phone numbers for selected users"""
        updated = queryset.update(phone_confirm=False)
        self.message_user(
            request,
            f'Successfully unverified phone numbers for {updated} user(s).',
            level='warning'
        )
    
    @admin.action(description='🎓 Deactivate selected graduated students')
    def deactivate_selected_graduates(self, request, queryset):
        """Bulk action to deactivate selected students who have graduated"""
        # Check permission
        if not (request.user.is_superuser or request.user.has_perm('accounts.deactivate_graduated_students')):
            self.message_user(
                request,
                "You don't have permission to deactivate graduated students.",
                level='error'
            )
            return
        
        # Filter to only graduated students in the selection
        graduated_in_selection = []
        for user in queryset:
            try:
                if user.has_completed_program() and user.is_active:
                    graduated_in_selection.append(user.pk)
            except Exception:
                continue
        
        if not graduated_in_selection:
            self.message_user(
                request,
                'No active graduated students found in selection.',
                level='warning'
            )
            return
        
        # Deactivate them
        updated = CustomUser.objects.filter(pk__in=graduated_in_selection).update(is_active=False)
        self.message_user(
            request,
            f'Successfully deactivated {updated} graduated student(s).',
            level='success'
        )
        logger.info(f'Admin {request.user} deactivated {updated} selected graduated students.')
    
    def get_urls(self):
        """Add custom URLs for analytics and graduated student management"""
        urls = super().get_urls()
        custom_urls = [
            path('analytics/', self.admin_site.admin_view(accounts_analytics), name='accounts_analytics'),
            path('deactivate-graduates/', self.admin_site.admin_view(deactivate_graduated_students_view), name='deactivate_graduated_students'),
            path('clear-field-data/', self.admin_site.admin_view(clear_field_data_view), name='clear_field_data'),
            path('clearable-fields-info/', self.admin_site.admin_view(get_clearable_fields_info), name='clearable_fields_info'),
        ]
        return custom_urls + urls
    
    def get_fieldsets(self, request, obj=None):
        """Dynamically modify fieldsets based on user permissions"""
        base_fieldsets = [
            (
                "Identity",
                {
                    "fields": (
                        "phone",
                        "graduation_year",
                    )
                },
            ),
            (
                _("Personal info"),
                {
                    "fields": (
                        "first_name",
                        "middle_name",
                        "last_name",
                    )
                },
            ),
        ]
        
        # Only show sensitive student information if user has permission or is superuser
        if request.user.is_superuser or request.user.has_perm('accounts.view_sensitive_student_data'):
            base_fieldsets.extend([
                (
                    "Student Information",
                    {
                        "fields": (
                            "student_id",
                            "index_number",
                            "program",
                            "group",
                            "gender",
                            "current_semester",
                            "completed_semesters_display",
                            "program_completion_status",
                        )
                    },
                ),
                (
                    "Contact Information",
                    {
                        "fields": (
                            "personal_email",
                            "student_email",
                        )
                    },
                ),
            ])
        else:
            # Limited view for users without permission
            base_fieldsets.append(
                (
                    "Basic Student Information",
                    {
                        "fields": (
                            "program",
                            "group",
                            "current_semester",
                        )
                    },
                )
            )
        
        base_fieldsets.extend([
            (
                _("Permissions"),
                {
                    "fields": (
                        "groups",
                        "phone_confirm",
                        "user_permissions",
                        "is_active",
                        "is_staff",
                    ),
                },
            ),
            (_("Important dates"), {"fields": ("last_login", "date_joined")}),
        ])
        
        return base_fieldsets
    
    def get_list_display(self, request):
        """
        Dynamically modify list_display based on user permissions.
        CRITICAL: Always check permissions before returning columns.
        """
        # Check if user has permission to view sensitive data
        has_sensitive_perm = (
            request.user.is_superuser or 
            request.user.has_perm('accounts.view_sensitive_student_data')
        )
        
        # Get session-stored column selection
        session_key = 'customuser_list_display'
        stored = request.session.get(session_key)
        
        if stored and isinstance(stored, (list, tuple)):
            # CRITICAL FIX: Filter stored columns based on permissions
            allowed = set(self.get_available_columns(request))
            filtered = [c for c in stored if c in allowed]
            if filtered:
                return filtered
        
        # Fallback to defaults based on permissions
        if has_sensitive_perm:
            return [
                "first_name",
                "last_name",
                "phone",
                "phone_confirm",
                "student_id_display",
                "index_number_display",
                "student_email_display",
                "personal_email_display",
                "program",
                "group",
                "gender",
                "current_semester",
                "completed_semesters_display",
                "is_active",
                "is_staff",
                "last_login",
            ]
        else:
            return [
                "first_name",
                "last_name",
                "program",
                "group",
                "is_active",
            ]

    def get_available_columns(self, request):
        """
        CRITICAL FIX: Return only columns the user has permission to see.
        This ensures the column picker only shows allowed columns.
        """
        # Check if user has permission to view sensitive data
        has_sensitive_perm = (
            request.user.is_superuser or 
            request.user.has_perm('accounts.view_sensitive_student_data')
        )
        
        # Basic columns available to everyone (non-sensitive)
        basic_columns = [
            "first_name",
            "middle_name",
            "last_name",
            "program",
            "group",
            "is_active",
        ]
        
        # Sensitive columns only for authorized users
        sensitive_columns = [
            "phone",
            "phone_confirm",
            "student_id_display",
            "index_number_display",
            "student_email_display",
            "personal_email_display",
            "gender",
            "current_semester",
            "completed_semesters_display",
            "is_staff",
            "last_login",
        ]
        
        if has_sensitive_perm:
            return basic_columns + sensitive_columns
        else:
            return basic_columns

    def changelist_view(self, request, extra_context=None):
        """
        Inject column-picker context and handle updates to selected columns.
        CRITICAL FIX: Validate permissions before saving column selections.
        """
        session_key = 'customuser_list_display'

        # Handle reset to defaults
        if request.GET.get('reset_columns'):
            if session_key in request.session:
                del request.session[session_key]
            return redirect(request.path)

        # Handle POST with selected columns
        if request.method == 'POST' and 'selected_columns' in request.POST:
            # Get selected columns from POST
            selected = request.POST.getlist('selected_columns')
            
            # CRITICAL FIX: Validate against allowed columns for this user
            allowed = set(self.get_available_columns(request))
            selected_valid = [c for c in selected if c in allowed]
            
            # Only save valid selections
            if selected_valid:
                request.session[session_key] = selected_valid
            else:
                # Clear session if no valid columns
                if session_key in request.session:
                    del request.session[session_key]
            
            return redirect(request.path)

        # Build extra context for template
        selected = request.session.get(session_key)
        if not selected:
            # Use default for current user
            selected = self.get_list_display(request)
        
        # Get clearable fields info for the template
        has_sensitive_perm = (
            request.user.is_superuser or 
            request.user.has_perm('accounts.view_sensitive_student_data')
        )
        has_change_perm = (
            request.user.is_superuser or 
            request.user.has_perm('accounts.change_customuser')
        )
        
        # Filter clearable fields based on permissions
        available_clearable_fields = {}
        if has_change_perm:
            for key, config in CLEARABLE_FIELDS.items():
                if config.get('is_sensitive', False) and not has_sensitive_perm:
                    continue
                available_clearable_fields[key] = {
                    'label': config['label'],
                    'description': config['description'],
                }
        
        # Get graduation years for dropdown
        now = timezone.now()
        current_year = now.year
        adjustment = 1 if (now.month == 12 or (now.month == 11 and now.day > 30)) else 0
        effective_year = current_year + adjustment
        
        graduation_years_choices = []
        for year in range(effective_year, effective_year + 4):
            count = CustomUser.objects.filter(graduation_year=year, is_staff=False).count()
            academic_year = effective_year + 3 - year + 1
            graduation_years_choices.append({
                'year': year,
                'count': count,
                'academic_year': f'Year {academic_year}'
            })
        
        ctx = extra_context or {}
        ctx.update({
            'available_columns': self.get_available_columns(request),
            'selected_columns': selected,
            # CRITICAL FIX: Add permission info to template context
            'has_sensitive_perm': has_sensitive_perm,
            'has_analytics_perm': (
                request.user.is_superuser or 
                request.user.has_perm('accounts.view_accounts_analytics')
            ),
            # Clear field data context
            'has_change_perm': has_change_perm,
            'clearable_fields': available_clearable_fields,
            'graduation_years_choices': graduation_years_choices,
        })
        return super().changelist_view(request, extra_context=ctx)
    
    def student_id_display(self, obj):
        """Display student ID with permission check"""
        return obj.student_id or "-"
    student_id_display.short_description = "Student ID"
    
    def index_number_display(self, obj):
        """Display index number with permission check"""
        return obj.index_number or "-"
    index_number_display.short_description = "Index Number"
    
    def student_email_display(self, obj):
        """Display student email with permission check"""
        return obj.student_email or "-"
    student_email_display.short_description = "Student Email"
    
    def personal_email_display(self, obj):
        """Display personal email with permission check"""
        return obj.personal_email or "-"
    personal_email_display.short_description = "Personal Email"
    
    def completed_semesters_display(self, obj):
        """Display completed semesters with visual indicator"""
        completed = obj.get_completed_semesters()
        if completed >= 8:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ {} / 8 (COMPLETED)</span>',
                completed
            )
        else:
            return format_html(
                '<span>{} / 8</span>',
                completed
            )
    completed_semesters_display.short_description = "Completed Semesters"
    
    def program_completion_status(self, obj):
        """Display program completion status"""
        if obj.has_completed_program():
            return format_html(
                '<span style="color: green; font-weight: bold; font-size: 14px;">✓ PROGRAM COMPLETED</span>'
            )
        else:
            completed = obj.get_completed_semesters()
            remaining = 8 - completed
            return format_html(
                '<span style="color: orange; font-size: 14px;">{} semesters remaining</span>',
                remaining
            )
    program_completion_status.short_description = "Program Status"
    
    def has_delete_permission(self, request, obj=None):
        """
        Allow superusers and staff with delete permission to delete accounts.
        This ensures audit logs and related objects don't block deletion.
        """
        if request.user.is_superuser:
            return True
        return request.user.has_perm('accounts.delete_customuser')


@admin.register(FieldRequirementConfig)
class FieldRequirementConfigAdmin(admin.ModelAdmin):
    list_display = [
        "field_name",
        "is_required",
        "required_from_year",
        "description",
        "created_at",
        "updated_at",
    ]
    list_filter = ["is_required", "required_from_year", "field_name"]
    search_fields = ["field_name", "description"]
    ordering = ["required_from_year", "field_name"]
    
    fieldsets = (
        (
            "Field Configuration",
            {
                "fields": (
                    "field_name",
                    "is_required",
                    "required_from_year",
                )
            },
        ),
        (
            "Details",
            {
                "fields": ("description",)
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )
    
    readonly_fields = ["created_at", "updated_at"]