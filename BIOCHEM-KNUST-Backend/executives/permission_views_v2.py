"""
Updated Permission Management Views
Works with Django's built-in Permission model via ManyToMany relationship
"""
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Committee, Appointee, AppointeePermission, PermissionAuditLog
from .serializers import AppointeePermissionSerializer, PermissionAuditLogSerializer
from .permissions import (
    get_user_committee_role,
    IsCommitteeHeadOrDeputy,
    IsCommitteeMember
)


def get_client_ip(request):
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_all_permissions(request):
    """
    List all available permissions in the backend.
    Grouped by app and content type for better organization.
    """
    try:
        # Get all permissions
        permissions = Permission.objects.select_related('content_type').all().order_by(
            'content_type__app_label',
            'content_type__model',
            'codename'
        )
        
        # Group permissions by app
        grouped_permissions = {}
        for perm in permissions:
            app_label = perm.content_type.app_label
            model_name = perm.content_type.model
            
            if app_label not in grouped_permissions:
                grouped_permissions[app_label] = {}
            
            if model_name not in grouped_permissions[app_label]:
                grouped_permissions[app_label][model_name] = []
            
            grouped_permissions[app_label][model_name].append({
                'id': perm.id,
                'codename': perm.codename,
                'name': perm.name,
                'content_type': f"{app_label}.{model_name}"
            })
        
        return Response({
            'success': True,
            'total_permissions': permissions.count(),
            'permissions': grouped_permissions
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCommitteeHeadOrDeputy])
def get_available_permissions(request, committee_id):
    """
    Returns permissions that the current user can grant to members.
    Heads can grant more permissions than deputies.
    """
    try:
        committee = get_object_or_404(Committee, committee_id=committee_id)
        
        # Get user's role in committee
        user_roles = get_user_committee_role(request.user)
        user_role = user_roles.get(str(committee_id))
        
        # Superusers can grant any permission
        if request.user.is_superuser:
            grantable_permissions = Permission.objects.select_related('content_type').all().order_by(
                'content_type__app_label',
                'name'
            )
        elif not user_role:
            return Response(
                {'error': 'You are not a member of this committee'},
                status=status.HTTP_403_FORBIDDEN
            )
        else:
            # Get all permissions
            all_permissions = Permission.objects.select_related('content_type').all().order_by(
                'content_type__app_label',
                'name'
            )
            
            # Heads can grant any permission, deputies have limited permissions
            if user_role == 'head':
                grantable_permissions = all_permissions
            elif user_role == 'deputy_head':
                # Deputies can grant limited permissions plus member field permissions
                limited_permissions = [
                    'view_committee_members', 'edit_committee_members', 'add_committee_members', 'assign_limited_permissions',
                    'edit_own_image', 'edit_own_portfolio', 'edit_own_bio', 'edit_own_concepts', 'edit_own_social_links', 'edit_own_contact_details'
                ]
                grantable_permissions = all_permissions.filter(codename__in=limited_permissions)
            else:
                grantable_permissions = Permission.objects.none()
        
        permissions_data = [{
            'id': perm.id,
            'codename': perm.codename,
            'name': perm.name,
            'content_type': f"{perm.content_type.app_label}.{perm.content_type.model}",
            'app_label': perm.content_type.app_label
        } for perm in grantable_permissions]
        
        return Response({
            'success': True,
            'user_role': user_role,
            'committee_name': committee.name,
            'total_permissions': len(permissions_data),
            'permissions': permissions_data
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsCommitteeHeadOrDeputy])
def grant_permissions(request, committee_id):
    """
    Grant multiple permissions to a committee member.
    
    Expected payload:
    {
        "member_id": 123,
        "permission_ids": [1, 2, 3, 4],
        "notes": "Optional notes",
        "expires_at": "2024-12-31T23:59:59Z"  // optional
    }
    """
    try:
        committee = get_object_or_404(Committee, committee_id=committee_id)
        
        member_id = request.data.get('member_id')
        permission_ids = request.data.get('permission_ids', [])
        notes = request.data.get('notes', '')
        expires_at = request.data.get('expires_at')
        
        if not member_id or not permission_ids:
            return Response(
                {'error': 'member_id and permission_ids are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get the target appointee
        appointee = get_object_or_404(
            Appointee,
            appointee_id=member_id,
            committee=committee,
            role='member'
        )
        
        # Get the permissions
        permissions_to_grant = Permission.objects.filter(id__in=permission_ids)
        
        if not permissions_to_grant.exists():
            return Response(
                {'error': 'No valid permissions found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            # Get or create AppointeePermission
            appointee_perm, created = AppointeePermission.objects.get_or_create(
                appointee=appointee,
                defaults={
                    'granted_by': request.user,
                    'notes': notes,
                    'expires_at': expires_at,
                    'is_active': True
                }
            )
            
            # Add the permissions
            appointee_perm.permissions.add(*permissions_to_grant)
            
            if not created:
                # Update existing record
                appointee_perm.granted_by = request.user
                appointee_perm.notes = notes
                if expires_at:
                    appointee_perm.expires_at = expires_at
                appointee_perm.save()
            
            # Create audit log
            audit_log = PermissionAuditLog.objects.create(
                action='grant' if created else 'modify',
                target_user=appointee.user,
                target_committee=committee,
                performed_by=request.user,
                details=f"Granted {permissions_to_grant.count()} permissions. Notes: {notes}",
                ip_address=get_client_ip(request)
            )
            audit_log.permissions.add(*permissions_to_grant)
        
        serializer = AppointeePermissionSerializer(appointee_perm)
        
        return Response({
            'success': True,
            'message': f'Successfully granted {permissions_to_grant.count()} permissions to {appointee.user.first_name} {appointee.user.last_name}',
            'permission_grant': serializer.data
        })
        
    except Appointee.DoesNotExist:
        return Response(
            {'error': 'Member not found or not a committee member'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsCommitteeHeadOrDeputy])
def revoke_permissions(request, committee_id):
    """
    Revoke specific permissions from a committee member.
    
    Expected payload:
    {
        "member_id": 123,
        "permission_ids": [1, 2, 3]
    }
    """
    try:
        committee = get_object_or_404(Committee, committee_id=committee_id)
        
        member_id = request.data.get('member_id')
        permission_ids = request.data.get('permission_ids', [])
        
        if not member_id or not permission_ids:
            return Response(
                {'error': 'member_id and permission_ids are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get the appointee permission record
        appointee = get_object_or_404(
            Appointee,
            appointee_id=member_id,
            committee=committee
        )
        
        try:
            appointee_perm = AppointeePermission.objects.get(appointee=appointee)
        except AppointeePermission.DoesNotExist:
            return Response(
                {'error': 'No permissions found for this member'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        permissions_to_revoke = Permission.objects.filter(id__in=permission_ids)
        
        with transaction.atomic():
            # Remove the permissions
            appointee_perm.permissions.remove(*permissions_to_revoke)
            
            # Create audit log
            audit_log = PermissionAuditLog.objects.create(
                action='revoke',
                target_user=appointee.user,
                target_committee=committee,
                performed_by=request.user,
                details=f"Revoked {permissions_to_revoke.count()} permissions",
                ip_address=get_client_ip(request)
            )
            audit_log.permissions.add(*permissions_to_revoke)
            
            # If no permissions left, optionally deactivate
            if appointee_perm.permissions.count() == 0:
                appointee_perm.is_active = False
                appointee_perm.save()
        
        return Response({
            'success': True,
            'message': f'Successfully revoked {permissions_to_revoke.count()} permissions from {appointee.user.first_name} {appointee.user.last_name}'
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCommitteeMember])
def list_member_permissions(request, committee_id, member_id):
    """
    List all permissions for a specific committee member.
    """
    try:
        committee = get_object_or_404(Committee, committee_id=committee_id)
        appointee = get_object_or_404(
            Appointee,
            appointee_id=member_id,
            committee=committee
        )
        
        try:
            appointee_perm = AppointeePermission.objects.get(appointee=appointee)
            serializer = AppointeePermissionSerializer(appointee_perm)
            
            return Response({
                'success': True,
                'member_name': f"{appointee.user.first_name} {appointee.user.last_name}",
                'role': appointee.role,
                'committee': committee.name,
                'permission_grant': serializer.data,
                'total_permissions': appointee_perm.permissions.count()
            })
        except AppointeePermission.DoesNotExist:
            return Response({
                'success': True,
                'member_name': f"{appointee.user.first_name} {appointee.user.last_name}",
                'role': appointee.role,
                'committee': committee.name,
                'permission_grant': None,
                'total_permissions': 0,
                'message': 'No additional permissions granted'
            })
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCommitteeMember])
def my_permissions(request, committee_id):
    """
    Returns current user's permissions in the committee.
    """
    try:
        committee = get_object_or_404(Committee, committee_id=committee_id)
        
        appointee = get_object_or_404(
            Appointee,
            user=request.user,
            committee=committee
        )
        
        try:
            appointee_perm = AppointeePermission.objects.get(appointee=appointee)
            serializer = AppointeePermissionSerializer(appointee_perm)
            
            return Response({
                'success': True,
                'user_name': f"{request.user.first_name} {request.user.last_name}",
                'role': appointee.role,
                'committee': committee.name,
                'permission_grant': serializer.data,
                'total_permissions': appointee_perm.permissions.count()
            })
        except AppointeePermission.DoesNotExist:
            return Response({
                'success': True,
                'user_name': f"{request.user.first_name} {request.user.last_name}",
                'role': appointee.role,
                'committee': committee.name,
                'permission_grant': None,
                'total_permissions': 0,
                'message': 'No additional permissions granted'
            })
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCommitteeHeadOrDeputy])
def permission_audit_log(request, committee_id):
    """
    Returns audit trail of permission changes in the committee.
    """
    try:
        committee = get_object_or_404(Committee, committee_id=committee_id)
        
        # Get last 100 logs for this committee
        logs = PermissionAuditLog.objects.filter(
            target_committee=committee
        ).select_related(
            'target_user',
            'performed_by'
        ).prefetch_related(
            'permissions'
        ).order_by('-timestamp')[:100]
        
        serializer = PermissionAuditLogSerializer(logs, many=True)
        
        return Response({
            'success': True,
            'committee': committee.name,
            'total_logs': logs.count(),
            'logs': serializer.data
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
