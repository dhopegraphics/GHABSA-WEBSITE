from rest_framework import serializers
from .models import Project, ProjectMember
from .utils import convert_to_direct_image_url


class ProjectMemberWriteSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating project members"""
    class Meta:
        model = ProjectMember
        fields = [
            'name',
            'year',
            'program',
            'role',
            'student_id',
            'email',
            'phone',
            'order',
        ]


class ProjectUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating existing projects"""
    members = serializers.CharField(required=False, allow_blank=True)
    
    # Make all image fields optional for updates
    image_url = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    image2_url = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    image3_url = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    image = serializers.ImageField(required=False, allow_null=True, allow_empty_file=True)
    image2 = serializers.ImageField(required=False, allow_null=True, allow_empty_file=True)
    image3 = serializers.ImageField(required=False, allow_null=True, allow_empty_file=True)
    
    class Meta:
        model = Project
        fields = [
            'title',
            'description',
            'short_description',
            'academic_year',
            'category',
            'technologies',
            'github_url',
            'demo_url',
            'image',
            'image_url',
            'image2',
            'image2_url',
            'image3',
            'image3_url',
            'members',
        ]
    
    def validate_members(self, value):
        """Parse and validate members JSON string if provided"""
        import json
        if not value:
            return None  # No member updates
            
        try:
            if isinstance(value, str):
                members_data = json.loads(value)
            else:
                members_data = value
                
            if not isinstance(members_data, list):
                raise serializers.ValidationError("Members must be a list")
            
            if len(members_data) == 0:
                raise serializers.ValidationError("At least one team member is required.")
            
            # Validate each member has required fields
            for idx, member in enumerate(members_data):
                if not member.get('name'):
                    raise serializers.ValidationError(f"Member {idx + 1}: Name is required")
                if not member.get('year'):
                    raise serializers.ValidationError(f"Member {idx + 1}: Year is required")
                    
            return members_data
        except json.JSONDecodeError:
            raise serializers.ValidationError("Invalid JSON format for members")
    
    def update(self, instance, validated_data):
        members_data = validated_data.pop('members', None)
        
        # Convert cloud storage URLs to direct URLs if provided
        for field in ['image_url', 'image2_url', 'image3_url']:
            if field in validated_data and validated_data[field]:
                validated_data[field] = convert_to_direct_image_url(validated_data[field])
        
        # Update project fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update members if provided
        if members_data is not None:
            # Get the user who is updating
            request = self.context.get('request')
            user = request.user if request else None
            
            # Delete existing members and recreate
            instance.members.all().delete()
            
            for idx, member_data in enumerate(members_data):
                # Check if this member matches the submitting user
                is_submitter = False
                linked_user = None
                
                if user and user.is_authenticated:
                    member_email = member_data.get('email', '').lower().strip()
                    member_phone = member_data.get('phone', '').strip()
                    member_student_id = member_data.get('student_id', '').strip()
                    
                    user_phone = str(user.phone) if user.phone else ''
                    user_personal_email = (user.personal_email or '').lower().strip()
                    user_student_email = (user.student_email or '').lower().strip()
                    user_student_id = (user.student_id or '').strip()
                    
                    if (member_phone and member_phone == user_phone) or \
                       (member_email and member_email in [user_personal_email, user_student_email]) or \
                       (member_student_id and member_student_id == user_student_id):
                        is_submitter = True
                        linked_user = user
                    
                    if idx == 0 and not any(m.get('is_submitter', False) for m in members_data[:idx]):
                        is_submitter = True
                        linked_user = user
                
                ProjectMember.objects.create(
                    project=instance, 
                    user=linked_user,
                    is_submitter=is_submitter,
                    **member_data
                )
        
        return instance


class ProjectSubmissionSerializer(serializers.ModelSerializer):
    """Serializer for students to submit projects"""
    members = serializers.CharField(write_only=True)  # Will receive JSON string
    
    # Make image_url not required since users can upload files instead
    image_url = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    image2_url = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    image3_url = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    
    # Add image file fields
    image = serializers.ImageField(required=False, allow_null=True, allow_empty_file=True)
    image2 = serializers.ImageField(required=False, allow_null=True, allow_empty_file=True)
    image3 = serializers.ImageField(required=False, allow_null=True, allow_empty_file=True)
    
    class Meta:
        model = Project
        fields = [
            'title',
            'description',
            'short_description',
            'academic_year',
            'category',
            'technologies',
            'github_url',
            'demo_url',
            'image',
            'image_url',
            'image2',
            'image2_url',
            'image3',
            'image3_url',
            'members',
        ]
    
    def validate_members(self, value):
        """Parse and validate members JSON string"""
        import json
        try:
            if isinstance(value, str):
                members_data = json.loads(value)
            else:
                members_data = value
                
            if not isinstance(members_data, list):
                raise serializers.ValidationError("Members must be a list")
            
            if len(members_data) == 0:
                raise serializers.ValidationError("At least one team member is required.")
            
            # Validate each member has required fields
            for idx, member in enumerate(members_data):
                if not member.get('name'):
                    raise serializers.ValidationError(f"Member {idx + 1}: Name is required")
                if not member.get('year'):
                    raise serializers.ValidationError(f"Member {idx + 1}: Year is required")
                    
            return members_data
        except json.JSONDecodeError:
            raise serializers.ValidationError("Invalid JSON format for members")
    
    def validate(self, data):
        """Ensure at least one main image is provided (either file or URL)"""
        has_image_file = data.get('image') is not None
        image_url = data.get('image_url', '') or ''
        has_image_url = bool(image_url.strip()) if isinstance(image_url, str) else bool(image_url)
        
        if not has_image_file and not has_image_url:
            raise serializers.ValidationError({
                'image': 'At least one main project image is required. Provide either a file upload or an image URL.'
            })
        
        return data
    
    def create(self, validated_data):
        import logging
        logger = logging.getLogger(__name__)
        
        members_data = validated_data.pop('members')
        
        # Convert cloud storage URLs to direct URLs if provided
        for field in ['image_url', 'image2_url', 'image3_url']:
            if field in validated_data and validated_data[field]:
                validated_data[field] = convert_to_direct_image_url(validated_data[field])
        
        # Get the user who is submitting (from the request context)
        request = self.context.get('request')
        user = request.user if request else None
        
        # Set the submitted_by field
        if user and user.is_authenticated:
            validated_data['submitted_by'] = user
        
        # Log the image fields being submitted
        logger.info(f"Creating project with image fields: image={validated_data.get('image')}, image_url={validated_data.get('image_url')}")
        
        # Create project (defaults to unapproved)
        project = Project.objects.create(**validated_data)
        
        # Refresh from DB to get updated URL fields (populated by MediaUrlMixin)
        project.refresh_from_db()
        
        logger.info(f"Project created with image={project.image}, image_url={project.image_url}")
        
        # Create team members
        for idx, member_data in enumerate(members_data):
            # Check if this member matches the submitting user (by phone, email, or student_id)
            is_submitter = False
            linked_user = None
            
            if user and user.is_authenticated:
                member_email = member_data.get('email', '').lower().strip()
                member_phone = member_data.get('phone', '').strip()
                member_student_id = member_data.get('student_id', '').strip()
                
                # Check if this member is the submitter
                user_phone = str(user.phone) if user.phone else ''
                user_personal_email = (user.personal_email or '').lower().strip()
                user_student_email = (user.student_email or '').lower().strip()
                user_student_id = (user.student_id or '').strip()
                
                # Match by various identifiers
                if (member_phone and member_phone == user_phone) or \
                   (member_email and member_email in [user_personal_email, user_student_email]) or \
                   (member_student_id and member_student_id == user_student_id):
                    is_submitter = True
                    linked_user = user
                
                # If first member and no specific match, assume they are the submitter
                if idx == 0 and not any(m.get('is_submitter', False) for m in members_data[:idx]):
                    is_submitter = True
                    linked_user = user
            
            ProjectMember.objects.create(
                project=project, 
                user=linked_user,
                is_submitter=is_submitter,
                **member_data
            )
        
        return project


class ProjectMemberSerializer(serializers.ModelSerializer):
    year_display = serializers.CharField(source='get_year_display', read_only=True)
    program_display = serializers.CharField(source='get_program_display', read_only=True)
    is_linked = serializers.SerializerMethodField()
    
    class Meta:
        model = ProjectMember
        fields = [
            'id',
            'name',
            'year',
            'year_display',
            'program',
            'program_display',
            'role',
            'student_id',
            'email',
            'phone',
            'order',
            'is_submitter',
            'is_linked',
        ]
    
    def get_is_linked(self, obj):
        """Check if member is linked to a user account"""
        return obj.user is not None


class SubmittedBySerializer(serializers.ModelSerializer):
    """Serializer for the user who submitted the project"""
    full_name = serializers.SerializerMethodField()
    year = serializers.SerializerMethodField()
    program_display = serializers.SerializerMethodField()
    
    class Meta:
        from accounts.models import CustomUser
        model = CustomUser
        fields = [
            'id',
            'full_name',
            'phone',
            'student_id',
            'index_number',
            'personal_email',
            'student_email',
            'year',
            'program',
            'program_display',
        ]
    
    def get_full_name(self, obj):
        parts = [obj.first_name]
        if obj.middle_name:
            parts.append(obj.middle_name)
        parts.append(obj.last_name)
        return ' '.join(parts)
    
    def get_year(self, obj):
        """Calculate current year from graduation year"""
        from django.utils import timezone
        current_year = timezone.now().year
        years_left = obj.graduation_year - current_year
        year = 4 - years_left
        if year < 1:
            return 'Year 1'
        elif year > 4:
            return 'Alumni'
        return f'Year {year}'
    
    def get_program_display(self, obj):
        return obj.get_program_display() if obj.program else None


class ProjectSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    technology_list = serializers.SerializerMethodField()
    members = ProjectMemberSerializer(many=True, read_only=True)
    submitted_by = SubmittedBySerializer(read_only=True)
    team_size = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    image2 = serializers.SerializerMethodField()
    image3 = serializers.SerializerMethodField()
    update_status_display = serializers.CharField(source='get_update_status_display', read_only=True)
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id',
            'title',
            'description',
            'short_description',
            'academic_year',
            'category',
            'category_display',
            'technologies',
            'technology_list',
            'github_url',
            'demo_url',
            'image',
            'image2',
            'image3',
            'is_featured',
            'is_approved',
            'order',
            'created_at',
            'submitted_by',
            'members',
            'team_size',
            'update_status',
            'update_status_display',
            'update_request_reason',
            'update_requested_at',
            'can_edit',
            'can_delete',
        ]
    
    def get_technology_list(self, obj):
        return obj.get_technology_list()
    
    def get_team_size(self, obj):
        return obj.members.count()
    
    def get_can_edit(self, obj):
        """Check if the project can be edited"""
        return not obj.is_approved or obj.update_status == 'in_progress'
    
    def get_can_delete(self, obj):
        """Check if the project can be deleted"""
        return not obj.is_approved
    
    def get_image(self, obj):
        # Prioritize uploaded file over URL (file has the correct sanitized path)
        if obj.image:
            try:
                url = obj.image.url
                if url:
                    return url
            except (ValueError, AttributeError):
                pass
        if obj.image_url:
            return obj.image_url
        return None
    
    def get_image2(self, obj):
        # Prioritize uploaded file over URL
        if obj.image2:
            try:
                url = obj.image2.url
                if url:
                    return url
            except (ValueError, AttributeError):
                pass
        if obj.image2_url:
            return obj.image2_url
        return None
    
    def get_image3(self, obj):
        # Prioritize uploaded file over URL
        if obj.image3:
            try:
                url = obj.image3.url
                if url:
                    return url
            except (ValueError, AttributeError):
                pass
        if obj.image3_url:
            return obj.image3_url
        return None
