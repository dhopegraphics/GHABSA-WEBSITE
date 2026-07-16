from django.shortcuts import render
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from executives.repositories import ExecutiveRepo
from executives.serializers import (
    ExecutiveSerializer, CommitteeSerializer, CommitteeDetailSerializer,
    AppointeeSerializer, AppointeeSocialLinksSerializer
)
from executives.models import Committee, Appointee, AppointeeSocialLinks, AppointeePermission
from rest_framework.permissions import IsAuthenticated
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.http import http_date
from django.contrib.auth import get_user_model

User = get_user_model()
from django.contrib.auth import get_user_model
from executives.permissions import get_user_permissions_in_committee
import re

# Create your views here.

exec_repo = ExecutiveRepo


class ExecutiveListView(ListAPIView):
    """Get all active/current executives"""
    queryset = exec_repo.get_all_active()
    serializer_class = ExecutiveSerializer


def _is_mobile_request(request):
    """Heuristic to detect mobile clients. Frontend can also set `X-Client-Platform: mobile` header
    or add `?platform=mobile` query param. This helper looks for those hints or the User-Agent.
    """
    # explicit query param or header overrides
    platform = request.query_params.get('platform') or request.META.get('HTTP_X_CLIENT_PLATFORM')
    if platform and str(platform).lower() == 'mobile':
        return True

    user_agent = request.META.get('HTTP_USER_AGENT', '')
    # common mobile UA fragments
    mobile_regex = re.compile(r"Mobile|Android|iPhone|iPad|iPod|BlackBerry|Opera Mini|IEMobile", re.I)
    return bool(mobile_regex.search(user_agent))


class PastExecutiveListView(ListAPIView):
    """Get all past executives"""
    queryset = exec_repo.get_all_past()
    serializer_class = ExecutiveSerializer


class ExecutiveByYearView(APIView):
    """Get executives by specific year"""
    
    def get(self, request, year=None):
        if year:
            executives = exec_repo.get_by_year(year)
            serializer = ExecutiveSerializer(executives, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(
            {"error": "Year parameter is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )


class AvailableYearsView(APIView):
    """Get all available office years"""
    
    def get(self, request):
        years = list(exec_repo.get_available_years())
        return Response({"years": years}, status=status.HTTP_200_OK)


# Committee Views
class CommitteeListView(ListAPIView):
    """Get all active committees"""
    queryset = Committee.objects.filter(is_active=True).order_by('name')
    serializer_class = CommitteeSerializer
    # This is a public page - no mobile restrictions needed


class CommitteeDetailView(APIView):
    """Get committee details with all members organized by role"""
    
    def get(self, request, committee_id):
        try:
            committee = Committee.objects.get(committee_id=committee_id, is_active=True)
            serializer = CommitteeDetailSerializer(committee)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Committee.DoesNotExist:
            return Response(
                {"error": "Committee not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )


class CurrentAdministrationView(APIView):
    """Get current executives and all active committees with their members"""
    
    def get(self, request):
        # This is a public page - no mobile restrictions needed
        # Get current executives
        executives = exec_repo.get_all_active()
        executives_data = ExecutiveSerializer(executives, many=True).data
        
        # Get all active committees with their members
        committees = Committee.objects.filter(is_active=True).order_by('name')
        committees_data = CommitteeDetailSerializer(committees, many=True).data
        
        return Response({
            "executives": executives_data,
            "committees": committees_data
        }, status=status.HTTP_200_OK)


class AppointeeListView(APIView):
    """List all appointees or create a new committee member"""
    # GET is public for viewing past/current appointees, POST requires authentication
    def get_permissions(self):
        if self.request.method == 'GET':
            return []
        return [IsAuthenticated()]
    
    def get(self, request):
        """Get all active appointees with optional filtering"""
        # Allow filtering by office year and optionally include inactive (past) appointees
        qs = Appointee.objects.select_related('user', 'committee', 'contact_details').prefetch_related('social_media_links')
        year = request.query_params.get('year')
        include_inactive = request.query_params.get('include_inactive')

        if year:
            qs = qs.filter(office_year=year)

        # By default only return active appointees unless explicitly asked
        if include_inactive and include_inactive.lower() in ["1", "true", "yes"]:
            # include both active and inactive
            pass
        else:
            qs = qs.filter(is_active=True)

        appointees = qs.order_by('committee', 'role')
        
        # Prevent mobile access to the appointees list unless permitted
        if _is_mobile_request(request):
            user = request.user
            if not (user and user.is_authenticated and (user.is_superuser or user.has_perm('executives.can_access_mobile_dashboard'))):
                return Response({"detail": "Mobile access to this endpoint is restricted."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = AppointeeSerializer(appointees, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        """
        Create a new committee member.
        
        Required permissions:
        - add_committee_members: Can add members to their own committee
        - add_appointee: Can add members to any committee (staff/superuser level)
        
        Expected payload:
        {
            "user_phone": "+233XXXXXXXXX",  # Phone of existing user
            "committee_id": "uuid",          # Optional if user is head/deputy
            "portfolio": "Description of role",
            "bio": "Bio text",
            "skills": "Skills",
            "appointed_from": "2024-01-01",
            "appointed_to": "2024-12-31",
            "office_year": "2024/2025"
        }
        """
        user = request.user
        
        # Check permissions - prioritize explicit permissions over staff status
        has_add_appointee = user.has_perm('executives.add_appointee')
        has_add_committee_members = user.has_perm('executives.add_committee_members')
        is_superuser = user.is_superuser
        
        if not (has_add_appointee or has_add_committee_members or is_superuser):
            return Response({
                "detail": "Permission denied. Required permission: add_committee_members or add_appointee"
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get user phone from request
        user_phone = request.data.get('user_phone')
        if not user_phone:
            return Response({
                "error": "user_phone is required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Find the user
        try:
            target_user = User.objects.get(phone=user_phone)
        except User.DoesNotExist:
            return Response({
                "error": f"No user found with phone: {user_phone}"
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user is already an appointee
        if Appointee.objects.filter(user=target_user, is_active=True).exists():
            return Response({
                "error": f"User {target_user.first_name} {target_user.last_name} is already an active appointee"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Determine committee based on permissions
        committee_id = request.data.get('committee_id')
        committee = None
        
        # Priority 1: Heads/deputies with add_committee_members (most common case)
        if has_add_committee_members and not (has_add_appointee or is_superuser):
            # Heads/deputies can only add to their own committee
            try:
                creator_appointee = Appointee.objects.get(
                    user=user,
                    role__in=['head', 'deputy_head'],
                    is_active=True
                )
                committee = creator_appointee.committee
                
                # If they provided a different committee_id, reject
                if committee_id and str(committee.committee_id) != str(committee_id):
                    return Response({
                        "error": f"You can only add members to your own committee: {committee.name}"
                    }, status=status.HTTP_403_FORBIDDEN)
                    
            except Appointee.DoesNotExist:
                return Response({
                    "error": "You must be a head or deputy to add committee members"
                }, status=status.HTTP_403_FORBIDDEN)
        
        # Priority 2: Staff/users with add_appointee can add to any committee
        elif has_add_appointee or is_superuser:
            if not committee_id:
                return Response({
                    "error": "committee_id is required for staff users"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                committee = Committee.objects.get(committee_id=committee_id)
            except Committee.DoesNotExist:
                return Response({
                    "error": "Committee not found"
                }, status=status.HTTP_404_NOT_FOUND)
        
        else:
            # Should not reach here due to permission check at start
            return Response({
                "error": "Permission denied"
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Create the appointee
        try:
            with transaction.atomic():
                from django.utils import timezone
                
                appointee_data = {
                    'user': target_user,
                    'committee': committee,
                    'role': 'member',  # Only members can be created via API
                    'portfolio': request.data.get('portfolio', ''),
                    'bio': request.data.get('bio', ''),
                    'skills': request.data.get('skills', ''),
                    'appointed_from': request.data.get('appointed_from') or timezone.now(),  # Default to now
                    'appointed_to': request.data.get('appointed_to'),  # Can be None
                    'office_year': request.data.get('office_year', ''),
                    'is_active': True
                }
                
                appointee = Appointee.objects.create(**appointee_data)
                
                # Track who created this member (for deletion permissions)
                # Only create tracking for heads/deputies, not for staff/superusers
                if has_add_committee_members and not (has_add_appointee or is_superuser):
                    AppointeePermission.objects.create(
                        appointee=appointee,
                        granted_by=user,
                        is_active=True,
                        notes=f'Auto-created when {user.first_name} {user.last_name} added this member'
                    )
                
                serializer = AppointeeSerializer(appointee)
                return Response({
                    "success": True,
                    "message": f"Successfully added {target_user.first_name} {target_user.last_name} to {committee.name}",
                    "appointee": serializer.data
                }, status=status.HTTP_201_CREATED)
                
        except IntegrityError as e:
            return Response({
                "error": f"Database error: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "error": f"Error creating appointee: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AppointeeByCommitteeView(APIView):
    """Get all appointees in a specific committee"""
    
    def get(self, request, committee_id):
        appointees = Appointee.objects.filter(
            committee_id=committee_id,
            is_active=True
        ).select_related('user', 'committee', 'contact_details').prefetch_related('social_media_links')
        serializer = AppointeeSerializer(appointees, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AppointeeDetailView(APIView):
    """Retrieve or update a single appointee. Appointee users can update their own record; staff or users with change permission can update any."""
    permission_classes = [IsAuthenticated]

    def get_object(self, appointee_id):
        try:
            return Appointee.objects.select_related('user', 'committee', 'contact_details').prefetch_related('social_media_links').get(appointee_id=appointee_id)
        except Appointee.DoesNotExist:
            return None

    def get(self, request, appointee_id):
        obj = self.get_object(appointee_id)
        if not obj:
            return Response({"error": "Appointee not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Permission-based access: view_appointee for any, own record for self
        user = request.user
        can_view_any = user.has_perm('executives.view_appointee') or user.is_staff
        can_view_own = user == obj.user
        
        if not (can_view_own or can_view_any):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = AppointeeSerializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, appointee_id):
        obj = self.get_object(appointee_id)
        if not obj:
            return Response({"error": "Appointee not found"}, status=status.HTTP_404_NOT_FOUND)

        user = request.user

        # Permission-based access control
        # Rule 1: If user has 'change_appointee' permission, they have FULL ACCESS to edit ANY appointee
        has_change_permission = user.has_perm('executives.change_appointee')
        
        # Rule 2: If editing own record, check granular 'edit_own_*' permissions
        can_edit_own = user == obj.user

        if not (can_edit_own or has_change_permission or user.is_staff):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        # Determine filtered data based on permissions
        if has_change_permission or user.is_staff:
            # Full access: can update ALL fields including sensitive ones (role, committee, user, etc.)
            filtered_data = request.data
        elif can_edit_own:
            # Editing own record: restrict to fields based on granular 'edit_own_*' permissions
            field_permissions = {
                'executives.edit_own_image': ['image', 'image_url'],
                'executives.edit_own_portfolio': ['portfolio', 'skills'],
                'executives.edit_own_bio': ['bio'],
                'executives.edit_own_concepts': ['achievements'],
                'executives.edit_own_social_links': ['social_media_links'],  # For nested updates
                'executives.edit_own_contact_details': ['contact_details'],  # For nested updates
            }
            
            allowed_fields = set()
            for perm, fields in field_permissions.items():
                if user.has_perm(perm):
                    allowed_fields.update(fields)
            
            if not allowed_fields:
                return Response({
                    "detail": "You do not have permission to edit any fields. Required permissions: edit_own_image, edit_own_bio, edit_own_portfolio, etc."
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Filter request data to only allowed fields
            filtered_data = {k: v for k, v in request.data.items() if k in allowed_fields}
            
            if not filtered_data:
                return Response({
                    "detail": f"None of the provided fields are editable. You can only edit: {', '.join(allowed_fields)}"
                }, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        serializer = AppointeeSerializer(obj, data=filtered_data, partial=True)
        if serializer.is_valid():
            try:
                serializer.save()
            except IntegrityError:
                return Response({
                    "detail": "Duplicate active appointee exists for this user and office year."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(serializer.data, status=status.HTTP_200_OK)
        # If serializer.is_valid() is False the code will return errors below.
        # However, catch model ValidationError (raised by model.full_clean) and return readable response.
        try:
            serializer.is_valid(raise_exception=True)
        except DjangoValidationError as e:
            return Response({"detail": e.message_dict}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AppointeeSocialLinksView(APIView):
    """Manage social links for appointees"""
    permission_classes = [IsAuthenticated]

    def get(self, request, appointee_id):
        """Get all social links for an appointee"""
        try:
            appointee = Appointee.objects.get(appointee_id=appointee_id)
            
            # Permission-based access: view_appointee for any, own record for self
            can_view_any = request.user.has_perm('executives.view_appointee') or request.user.is_staff
            can_view_own = request.user == appointee.user
            
            if not (can_view_own or can_view_any):
                return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
            
            links = AppointeeSocialLinks.objects.filter(appointee=appointee)
            serializer = AppointeeSocialLinksSerializer(links, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Appointee.DoesNotExist:
            return Response({"error": "Appointee not found"}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, appointee_id):
        """Add a social link for an appointee"""
        try:
            appointee = Appointee.objects.get(appointee_id=appointee_id)
            user = request.user
            
            # Permission-based access control
            # Rule 1: If user has 'change_appointee' permission, they can edit ANY appointee's social links
            has_change_permission = user.has_perm('executives.change_appointee')
            
            # Rule 2: If editing own record, check 'edit_own_social_links' permission
            can_edit_own = user == appointee.user
            
            if has_change_permission or user.is_staff:
                # Full access: can add social links for any appointee
                pass
            elif can_edit_own:
                # Editing own record: require 'edit_own_social_links' permission
                if not user.has_perm('executives.edit_own_social_links'):
                    return Response({"detail": "Permission denied. Required permission: edit_own_social_links"}, status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
            
            data = request.data.copy()
            data['appointee'] = appointee.appointee_id
            
            serializer = AppointeeSocialLinksSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Appointee.DoesNotExist:
            return Response({"error": "Appointee not found"}, status=status.HTTP_404_NOT_FOUND)


class AppointeeSocialLinkDetailView(APIView):
    """Manage individual social link"""
    permission_classes = [IsAuthenticated]

    def get_object(self, link_id):
        try:
            return AppointeeSocialLinks.objects.select_related('appointee').get(id=link_id)
        except AppointeeSocialLinks.DoesNotExist:
            return None

    def patch(self, request, appointee_id, link_id):
        """Update a social link"""
        link = self.get_object(link_id)
        if not link:
            return Response({"error": "Social link not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if str(link.appointee.appointee_id) != appointee_id:
            return Response({"error": "Link does not belong to this appointee"}, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        appointee = link.appointee
        
        # Permission-based access control
        has_change_permission = user.has_perm('executives.change_appointee')
        can_edit_own = user == appointee.user
        
        if has_change_permission or user.is_staff:
            # Full access: can update any appointee's social links
            pass
        elif can_edit_own:
            # Editing own record: require 'edit_own_social_links' permission
            if not user.has_perm('executives.edit_own_social_links'):
                return Response({"detail": "Permission denied. Required permission: edit_own_social_links"}, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = AppointeeSocialLinksSerializer(link, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, appointee_id, link_id):
        """Delete a social link"""
        link = self.get_object(link_id)
        if not link:
            return Response({"error": "Social link not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if str(link.appointee.appointee_id) != appointee_id:
            return Response({"error": "Link does not belong to this appointee"}, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        appointee = link.appointee
        
        # Permission-based access control
        has_change_permission = user.has_perm('executives.change_appointee')
        can_edit_own = user == appointee.user
        
        if has_change_permission or user.is_staff:
            # Full access: can delete any appointee's social links
            pass
        elif can_edit_own:
            # Editing own record: require 'edit_own_social_links' permission
            if not user.has_perm('executives.edit_own_social_links'):
                return Response({"detail": "Permission denied. Required permission: edit_own_social_links"}, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        
        link.delete()
        return Response({"message": "Social link deleted"}, status=status.HTTP_204_NO_CONTENT)

