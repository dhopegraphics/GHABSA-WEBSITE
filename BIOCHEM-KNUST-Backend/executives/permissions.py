"""
Custom permissions system for Committee Heads, Deputy Heads, and Members.
This module defines granular permissions for executive dashboard access.
"""

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework import permissions
from .models import Appointee, Committee

# Define all available permissions for committee roles
COMMITTEE_PERMISSIONS = {
    # Committee Head permissions (full access)
    'head': {
        'view_committee_members': 'Can view all committee members',
        'edit_committee_members': 'Can edit committee member details',
        'add_committee_members': 'Can add new committee members',
        'remove_committee_members': 'Can remove committee members',
        'assign_member_permissions': 'Can assign permissions to members',
        'manage_deputy_permissions': 'Can manage deputy head permissions',
    },
    
    # Deputy Head permissions (limited management)
    'deputy_head': {
        'view_committee_members': 'Can view all committee members',
        'edit_committee_members': 'Can edit committee member details',
        'add_committee_members': 'Can add new committee members',
        'assign_limited_permissions': 'Can assign limited permissions to members',
    },
    
    # Member permissions (view only, unless granted more)
    'member': {
        'view_own_details': 'Can view own member details',
    }
}

# Fine-grained permissions for editing own profile fields (available to all appointee roles)
MEMBER_FIELD_PERMISSIONS = {
    'edit_own_image': 'Can update own profile image',
    'edit_own_portfolio': 'Can update own portfolio/links',
    'edit_own_bio': 'Can update own biography',
    'edit_own_concepts': 'Can add or update own concepts/ideas',
    'edit_own_social_links': 'Can add or update social links',
    'edit_own_contact_details': 'Can update own contact information',
}

# Add field permissions to all roles so heads/deputies can edit their own data
for role in COMMITTEE_PERMISSIONS:
    COMMITTEE_PERMISSIONS[role].update(MEMBER_FIELD_PERMISSIONS)


def get_user_committee_role(user):
    """
    Get the user's role in their committee(s).
    Returns a dict: {'committee_id': 'role', ...}
    """
    try:
        appointees = Appointee.objects.filter(user=user, is_active=True)
        return {str(appointee.committee.committee_id): appointee.role 
                for appointee in appointees}
    except Appointee.DoesNotExist:
        return {}


def get_user_permissions_in_committee(user, committee_id):
    """
    Get all permissions a user has in a specific committee.
    Returns a list of permission codenames.
    """
    try:
        appointee = Appointee.objects.get(
            user=user, 
            committee__committee_id=committee_id, 
            is_active=True
        )
        
        # Get base permissions based on role
        role = appointee.role
        base_permissions = list(COMMITTEE_PERMISSIONS.get(role, {}).keys())
        
        # Get additional granted permissions from AppointeePermission model
        granted_permissions = list(
            appointee.granted_permissions.filter(is_active=True)
            .values_list('permission_codename', flat=True)
        )
        
        return list(set(base_permissions + granted_permissions))
    except Appointee.DoesNotExist:
        return []


def can_user_grant_permission(granter, permission_codename, committee_id):
    """
    Check if a user (head/deputy) can grant a specific permission to a member.
    Rule: Can only grant permissions they already have.
    """
    granter_permissions = get_user_permissions_in_committee(granter, committee_id)
    return permission_codename in granter_permissions


class IsCommitteeHead(permissions.BasePermission):
    """
    Permission class to check if user is a committee head.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        committee_id = view.kwargs.get('committee_id') or request.data.get('committee_id')
        if not committee_id:
            return False
        
        try:
            appointee = Appointee.objects.get(
                user=request.user,
                committee__committee_id=committee_id,
                role='head',
                is_active=True
            )
            return True
        except Appointee.DoesNotExist:
            return False


class IsCommitteeHeadOrDeputy(permissions.BasePermission):
    """
    Permission class to check if user is a committee head or deputy head.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        committee_id = view.kwargs.get('committee_id') or request.data.get('committee_id')
        if not committee_id:
            return False
        
        try:
            appointee = Appointee.objects.get(
                user=request.user,
                committee__committee_id=committee_id,
                role__in=['head', 'deputy_head'],
                is_active=True
            )
            return True
        except Appointee.DoesNotExist:
            return False


class HasCommitteePermission(permissions.BasePermission):
    """
    Permission class to check if user has a specific permission in a committee.
    Usage: Add required_permission attribute to view.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        committee_id = view.kwargs.get('committee_id') or request.data.get('committee_id')
        required_permission = getattr(view, 'required_permission', None)
        
        if not committee_id or not required_permission:
            return False
        
        user_permissions = get_user_permissions_in_committee(request.user, committee_id)
        return required_permission in user_permissions


class IsCommitteeMember(permissions.BasePermission):
    """
    Permission class to check if user is any member of a committee.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        committee_id = view.kwargs.get('committee_id') or request.data.get('committee_id')
        if not committee_id:
            return False
        
        try:
            appointee = Appointee.objects.get(
                user=request.user,
                committee__committee_id=committee_id,
                is_active=True
            )
            return True
        except Appointee.DoesNotExist:
            return False


def create_committee_permissions():
    """
    Create all custom permissions in the database.
    Should be run after migrations.
    """
    from django.contrib.contenttypes.models import ContentType
    from django.contrib.auth.models import Permission
    
    # Get content types
    committee_content_type = ContentType.objects.get_for_model(Committee)
    appointee_content_type = ContentType.objects.get_for_model(Appointee)
    
    created_count = 0
    
    # Create committee permissions
    committee_permissions = {}
    for role, perms in COMMITTEE_PERMISSIONS.items():
        if role != 'member':
            committee_permissions.update(perms)
        else:
            # For member role, separate committee permissions from field permissions
            for codename, name in perms.items():
                if codename in MEMBER_FIELD_PERMISSIONS:
                    # Member field permissions use Appointee content_type
                    permission, created = Permission.objects.get_or_create(
                        codename=codename,
                        content_type=appointee_content_type,
                        defaults={'name': name}
                    )
                    if created:
                        created_count += 1
                else:
                    committee_permissions[codename] = name
    
    # Create committee permissions
    for codename, name in committee_permissions.items():
        permission, created = Permission.objects.get_or_create(
            codename=codename,
            content_type=committee_content_type,
            defaults={'name': name}
        )
        if created:
            created_count += 1
    
    return created_count


# Decorator for function-based views
def require_committee_permission(permission_codename):
    """
    Decorator to check if user has specific permission in a committee.
    Usage: @require_committee_permission('view_committee_members')
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                from django.http import JsonResponse
                return JsonResponse({'error': 'Authentication required'}, status=401)
            
            committee_id = kwargs.get('committee_id') or request.POST.get('committee_id')
            if not committee_id:
                from django.http import JsonResponse
                return JsonResponse({'error': 'Committee ID required'}, status=400)
            
            user_permissions = get_user_permissions_in_committee(request.user, committee_id)
            if permission_codename not in user_permissions:
                from django.http import JsonResponse
                return JsonResponse({'error': 'Permission denied'}, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def create_committee_permissions():
    """
    Create all custom permissions in the database.
    Should be run after migrations.
    """
    from django.contrib.contenttypes.models import ContentType
    from django.contrib.auth.models import Permission
    
    # Get content types
    committee_content_type = ContentType.objects.get_for_model(Committee)
    appointee_content_type = ContentType.objects.get_for_model(Appointee)
    
    created_count = 0
    
    # Create committee permissions (excluding field permissions)
    committee_permissions = {}
    for role, perms in COMMITTEE_PERMISSIONS.items():
        for codename, name in perms.items():
            if codename not in MEMBER_FIELD_PERMISSIONS:
                committee_permissions[codename] = name
    
    # Create committee permissions
    for codename, name in committee_permissions.items():
        permission, created = Permission.objects.get_or_create(
            codename=codename,
            content_type=committee_content_type,
            defaults={'name': name}
        )
        if created:
            created_count += 1
    
    # Create field permissions for appointee
    for codename, name in MEMBER_FIELD_PERMISSIONS.items():
        permission, created = Permission.objects.get_or_create(
            codename=codename,
            content_type=appointee_content_type,
            defaults={'name': name}
        )
        if created:
            created_count += 1
    
    return created_count
