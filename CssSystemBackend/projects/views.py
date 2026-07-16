from django.shortcuts import render
from rest_framework.generics import ListAPIView, CreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.views import APIView
from rest_framework import status
from django.utils import timezone
from django.db.models import Q
from .models import Project, ProjectMember, get_year_choices
from .serializers import ProjectSerializer, ProjectSubmissionSerializer, ProjectUpdateSerializer
from .utils import convert_to_direct_image_url, is_cloud_storage_url
import requests
from PIL import Image
from io import BytesIO


class ProjectListView(ListAPIView):
    """
    API endpoint to list all approved and active student projects
    Only shows projects that have been approved by an executive
    Supports filtering by category and featured status
    """
    serializer_class = ProjectSerializer
    
    def get_queryset(self):
        # Use the approved manager to get only approved projects
        queryset = Project.approved.all()
        
        # Filter by category if provided
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
        
        # Filter by featured status if provided
        is_featured = self.request.query_params.get('featured', None)
        if is_featured is not None:
            queryset = queryset.filter(is_featured=is_featured.lower() == 'true')
        
        # Filter by year if provided
        year = self.request.query_params.get('year', None)
        if year:
            queryset = queryset.filter(academic_year=year)
        
        return queryset


class ProjectSubmissionView(CreateAPIView):
    """
    API endpoint for authenticated students to submit projects
    Projects will be in pending state until approved by an executive
    Supports both file uploads and image URLs
    """
    serializer_class = ProjectSubmissionSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def create(self, request, *args, **kwargs):
        import logging
        logger = logging.getLogger(__name__)
        
        # Log incoming request data for debugging
        logger.info(f"Project submission - Content-Type: {request.content_type}")
        logger.info(f"Project submission - FILES: {list(request.FILES.keys())}")
        logger.info(f"Project submission - Data keys: {list(request.data.keys())}")
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        project = serializer.save()
        
        # Log the saved project's image URLs
        logger.info(f"Project saved - image: {project.image}, image_url: {project.image_url}")
        
        return Response({
            'message': 'Project submitted successfully! It will be visible once approved by an executive.',
            'project_id': str(project.id),
            'title': project.title,
            'status': 'pending_approval'
        }, status=status.HTTP_201_CREATED)


class MyProjectsView(ListAPIView):
    """
    API endpoint to list all projects submitted by the authenticated user
    Shows projects of all statuses (pending, approved, rejected)
    Includes projects where user is the submitter OR a linked team member
    """
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        # Get projects where:
        # 1. User submitted the project (submitted_by)
        # 2. User is linked as a team member (members__user)
        from django.db.models import Q
        return Project.objects.filter(
            Q(submitted_by=user) | Q(members__user=user)
        ).distinct().order_by('-created_at')
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        # Count projects by status
        total = queryset.count()
        approved = queryset.filter(is_approved=True).count()
        pending = queryset.filter(is_approved=False).count()
        update_pending = queryset.filter(update_status='pending').count()
        update_in_progress = queryset.filter(update_status='in_progress').count()
        
        return Response({
            'projects': serializer.data,
            'stats': {
                'total': total,
                'approved': approved,
                'pending': pending,
                'update_pending': update_pending,
                'update_in_progress': update_in_progress,
            }
        })


@api_view(['GET'])
def get_available_years(request):
    """
    API endpoint to get dynamically generated year choices
    """
    years = [year[0] for year in get_year_choices()]
    return Response({'years': years}, status=status.HTTP_200_OK)


@api_view(['POST'])
def validate_image_url(request):
    """
    Validate if an image URL is accessible and returns a valid image
    Handles Google Drive and Dropbox share links automatically
    """
    image_url = request.data.get('url', '')
    
    if not image_url:
        return Response({
            'valid': False,
            'error': 'No URL provided'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Convert cloud storage share links to direct URLs
    original_url = image_url
    if is_cloud_storage_url(image_url):
        image_url = convert_to_direct_image_url(image_url)
        
    try:
        # Set timeout and headers to mimic browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Try to fetch the image
        response = requests.get(image_url, timeout=15, headers=headers, stream=True, allow_redirects=True)
        
        # Check if request was successful
        if response.status_code != 200:
            return Response({
                'valid': False,
                'error': f'Unable to access image. Server returned status code {response.status_code}. Please ensure the link is publicly accessible.',
                'converted_url': image_url if image_url != original_url else None
            }, status=status.HTTP_200_OK)
        
        # Check content type
        content_type = response.headers.get('Content-Type', '')
        if not content_type.startswith('image/'):
            # For cloud storage, sometimes content-type might not be set correctly
            # Try to validate by loading the image
            if not is_cloud_storage_url(original_url):
                return Response({
                    'valid': False,
                    'error': 'The URL does not point to an image. Please provide a direct image link.',
                    'content_type': content_type
                }, status=status.HTTP_200_OK)
        
        # Try to load the image to verify it's valid
        try:
            img = Image.open(BytesIO(response.content))
            img.verify()  # Verify it's a valid image
            
            # Re-open image to get dimensions (verify() closes the file)
            img = Image.open(BytesIO(response.content))
            
            return Response({
                'valid': True,
                'message': 'Image is accessible and valid',
                'width': img.width,
                'height': img.height,
                'format': img.format,
                'converted_url': image_url if image_url != original_url else None,
                'direct_url': image_url  # Return the direct URL to use
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'valid': False,
                'error': 'The file exists but is not a valid image format.',
                'details': str(e)
            }, status=status.HTTP_200_OK)
    
    except requests.exceptions.Timeout:
        return Response({
            'valid': False,
            'error': 'Request timed out. The image may be too large or the server is slow. Try uploading the image directly instead.'
        }, status=status.HTTP_200_OK)
    
    except requests.exceptions.RequestException as e:
        return Response({
            'valid': False,
            'error': 'Unable to access the image. Please check if the link is publicly accessible and not behind a login or permission wall. Consider uploading the image directly instead.',
            'details': str(e)
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'valid': False,
            'error': f'An unexpected error occurred: {str(e)}'
        }, status=status.HTTP_200_OK)


class ProjectDetailView(APIView):
    """
    API endpoint to retrieve, update, or delete a project
    - GET: Retrieve project details (owner only)
    - PUT/PATCH: Update project (only if not approved OR update_in_progress)
    - DELETE: Delete project (only if not approved)
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_project(self, pk, user):
        """Get project if user owns it"""
        try:
            project = Project.objects.filter(
                Q(submitted_by=user) | Q(members__user=user)
            ).distinct().get(pk=pk)
            return project
        except Project.DoesNotExist:
            return None
    
    def get(self, request, pk):
        """Get project details"""
        project = self.get_project(pk, request.user)
        if not project:
            return Response({
                'error': 'Project not found or you do not have permission to view it.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ProjectSerializer(project)
        return Response(serializer.data)
    
    def put(self, request, pk):
        """Update project (full update)"""
        return self._update_project(request, pk, partial=False)
    
    def patch(self, request, pk):
        """Update project (partial update)"""
        return self._update_project(request, pk, partial=True)
    
    def _update_project(self, request, pk, partial=False):
        """Handle project update logic"""
        project = self.get_project(pk, request.user)
        if not project:
            return Response({
                'error': 'Project not found or you do not have permission to edit it.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if editing is allowed
        can_edit = (
            not project.is_approved or  # Not approved yet - can edit
            project.update_status == 'in_progress'  # Update approved by admin - can edit
        )
        
        if not can_edit:
            return Response({
                'error': 'Cannot edit an approved project. Please request an update first.',
                'requires_update_request': True
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ProjectUpdateSerializer(
            project, 
            data=request.data, 
            partial=partial,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Project updated successfully!',
                'project': ProjectSerializer(project).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        """Delete project (only if not approved)"""
        project = self.get_project(pk, request.user)
        if not project:
            return Response({
                'error': 'Project not found or you do not have permission to delete it.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Cannot delete approved projects
        if project.is_approved:
            return Response({
                'error': 'Cannot delete an approved project. Please contact an administrator.',
            }, status=status.HTTP_403_FORBIDDEN)
        
        title = project.title
        project.delete()
        
        return Response({
            'message': f'Project "{title}" has been deleted successfully.'
        }, status=status.HTTP_200_OK)


class RequestUpdateView(APIView):
    """
    API endpoint to request an update for an approved project
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        """Request update for an approved project"""
        try:
            project = Project.objects.filter(
                Q(submitted_by=request.user) | Q(members__user=request.user)
            ).distinct().get(pk=pk)
        except Project.DoesNotExist:
            return Response({
                'error': 'Project not found or you do not have permission.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if project is approved
        if not project.is_approved:
            return Response({
                'error': 'Project is not approved yet. You can edit it directly.',
                'can_edit_directly': True
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if update is already requested or in progress
        if project.update_status in ['pending', 'approved', 'in_progress']:
            return Response({
                'error': f'An update request is already {project.update_status}.',
                'update_status': project.update_status
            }, status=status.HTTP_400_BAD_REQUEST)
        
        reason = request.data.get('reason', '').strip()
        if not reason:
            return Response({
                'error': 'Please provide a reason for the update request.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create update request
        project.update_status = 'pending'
        project.update_request_reason = reason
        project.update_requested_at = timezone.now()
        project.save()
        
        return Response({
            'message': 'Update request submitted successfully! An executive will review your request.',
            'update_status': 'pending',
            'project_id': str(project.id)
        })


class CancelUpdateRequestView(APIView):
    """
    API endpoint to cancel an update request
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        """Cancel update request"""
        try:
            project = Project.objects.filter(
                Q(submitted_by=request.user) | Q(members__user=request.user)
            ).distinct().get(pk=pk)
        except Project.DoesNotExist:
            return Response({
                'error': 'Project not found or you do not have permission.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if project.update_status != 'pending':
            return Response({
                'error': 'No pending update request to cancel.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        project.update_status = 'none'
        project.update_request_reason = ''
        project.update_requested_at = None
        project.save()
        
        return Response({
            'message': 'Update request cancelled.',
            'update_status': 'none'
        })


class CompleteUpdateView(APIView):
    """
    API endpoint to mark an update as complete
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        """Mark update as complete and re-submit for approval"""
        try:
            project = Project.objects.filter(
                Q(submitted_by=request.user) | Q(members__user=request.user)
            ).distinct().get(pk=pk)
        except Project.DoesNotExist:
            return Response({
                'error': 'Project not found or you do not have permission.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if project.update_status != 'in_progress':
            return Response({
                'error': 'No update in progress to complete.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Reset update status and set back to pending approval
        project.update_status = 'none'
        project.update_request_reason = ''
        project.update_requested_at = None
        project.update_approved_by = None
        project.update_approved_at = None
        project.is_approved = False  # Set back to pending approval
        project.approved_by = None
        project.approved_at = None
        project.save()
        
        return Response({
            'message': 'Update completed! Your project is now pending re-approval.',
            'update_status': 'none',
            'is_approved': False
        })
