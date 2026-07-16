from rest_framework import serializers
from .models import (
    HelpDeskCategory, HelpDeskRequest, CodeSnippet, RequestImage,
    HelpDeskResponse, ResponseCodeSnippet, ResponseLink, ResponseVote,
    ResponseReply, RequestBookmark, RequestView, HelpDeskNotification, 
    ContentReport, UserReputation
)
from django.utils import timezone
from datetime import timedelta
from utils.cloudinary_utils import get_detail_image_url, get_thumbnail_url


# Nested Serializers
class CodeSnippetSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodeSnippet
        fields = ['id', 'language', 'code', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']


class RequestImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    
    class Meta:
        model = RequestImage
        fields = ['id', 'url', 'thumbnail_url', 'caption', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_url(self, obj):
        # Prioritize URL over upload, apply optimization
        url = obj.image_url if obj.image_url else (obj.image.url if obj.image else None)
        return get_detail_image_url(url, width=800)
    
    def get_thumbnail_url(self, obj):
        # Prioritize URL over upload, apply optimization
        url = obj.thumbnail_url if obj.thumbnail_url else (obj.thumbnail.url if obj.thumbnail else None)
        return get_thumbnail_url(url, size=150)


class ResponseCodeSnippetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResponseCodeSnippet
        fields = ['id', 'language', 'code', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']


class ResponseLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResponseLink
        fields = ['id', 'url', 'title', 'description', 'image_url', 'created_at']
        read_only_fields = ['id', 'created_at']


class ResponseReplySerializer(serializers.ModelSerializer):
    """Serializer for response replies with nested support"""
    author_name = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    nested_replies = serializers.SerializerMethodField()
    
    class Meta:
        model = ResponseReply
        fields = [
            'id', 'response', 'parent_reply', 'content',
            'author_name', 'is_mine', 'can_edit',
            'nested_replies', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_author_name(self, obj):
        return f"{obj.author.first_name} {obj.author.last_name}".strip() or "Anonymous User"
    
    def get_is_mine(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.author_id == request.user.id
        return False
    
    def get_can_edit(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            is_owner = obj.author_id == request.user.id
            within_time_limit = (timezone.now() - obj.created_at) < timedelta(minutes=15)
            return is_owner and within_time_limit
        return False
    
    def get_nested_replies(self, obj):
        # Get direct nested replies (not recursive to avoid deep nesting)
        nested = ResponseReply.objects.filter(
            parent_reply=obj,
            is_deleted=False
        ).order_by('created_at')
        return ResponseReplySerializer(nested, many=True, context=self.context).data


class ResponseReplyCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating replies"""
    
    class Meta:
        model = ResponseReply
        fields = ['response', 'parent_reply', 'content']
    
    def validate(self, data):
        # Ensure parent_reply belongs to the same response if provided
        if data.get('parent_reply'):
            if data['parent_reply'].response != data['response']:
                raise serializers.ValidationError(
                    "Parent reply must belong to the same response"
                )
        return data
    
    def create(self, validated_data):
        reply = ResponseReply.objects.create(**validated_data)
        
        # Update response follow_up_count
        response = reply.response
        response.follow_up_count += 1
        response.save(update_fields=['follow_up_count'])
        
        return reply
    
    def to_representation(self, instance):
        """Use the list serializer for the response after creation"""
        return ResponseReplySerializer(
            instance, 
            context=self.context
        ).data


# Category Serializer
class HelpDeskCategorySerializer(serializers.ModelSerializer):
    active_count = serializers.SerializerMethodField()
    answered_today_count = serializers.SerializerMethodField()
    total_count = serializers.SerializerMethodField()
    
    class Meta:
        model = HelpDeskCategory
        fields = [
            'id', 'name', 'emoji', 'icon', 'description',
            'display_order', 'is_active',
            'active_count', 'answered_today_count', 'total_count'
        ]
    
    def get_active_count(self, obj):
        # Count only truly active requests (not resolved)
        return obj.requests.filter(
            status='active', 
            is_deleted=False,
            is_resolved=False
        ).count()
    
    def get_answered_today_count(self, obj):
        today = timezone.now().date()
        return obj.requests.filter(
            status='active',
            is_deleted=False,
            is_resolved=False,
            response_count__gt=0,
            created_at__date=today
        ).count()
    
    def get_total_count(self, obj):
        return obj.requests.filter(is_deleted=False).count()


# Request Serializers
class HelpDeskRequestListSerializer(serializers.ModelSerializer):
    """Serializer for list view - minimal data"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_mine = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()
    has_new_responses = serializers.SerializerMethodField()
    
    class Meta:
        model = HelpDeskRequest
        fields = [
            'id', 'tracking_id', 'title', 'description',
            'category', 'category_name', 'priority', 'status',
            'tags', 'course',
            'view_count', 'response_count', 'helpful_response_count', 'bookmark_count',
            'has_new_responses', 'is_resolved', 'is_bookmarked', 'is_mine',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'tracking_id', 'view_count', 'response_count',
            'helpful_response_count', 'bookmark_count',
            'created_at', 'updated_at'
        ]
    
    def get_is_mine(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.author_id == request.user.id
        return False
    
    def get_is_bookmarked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return RequestBookmark.objects.filter(
                request=obj,
                user=request.user
            ).exists()
        return False
    
    def get_has_new_responses(self, obj):
        # Logic: check if there are responses after user's last view
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            last_view = RequestView.objects.filter(
                request=obj,
                user=request.user
            ).order_by('-viewed_at').first()
            
            if last_view:
                new_responses = obj.responses.filter(
                    created_at__gt=last_view.viewed_at,
                    is_deleted=False
                ).exists()
                return new_responses
        return False


class HelpDeskRequestDetailSerializer(serializers.ModelSerializer):
    """Serializer for detail view - complete data"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    code_snippets = CodeSnippetSerializer(many=True, read_only=True)
    images = RequestImageSerializer(many=True, read_only=True)
    is_mine = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    
    class Meta:
        model = HelpDeskRequest
        fields = [
            'id', 'tracking_id', 'title', 'description',
            'category', 'category_name', 'priority', 'status',
            'tags', 'course',
            'code_snippets', 'images',
            'view_count', 'response_count', 'helpful_response_count', 'bookmark_count',
            'is_resolved', 'is_bookmarked', 'is_mine',
            'can_edit', 'can_delete',
            'created_at', 'updated_at', 'resolved_at', 'last_response_at'
        ]
        read_only_fields = [
            'id', 'tracking_id', 'view_count', 'response_count',
            'helpful_response_count', 'bookmark_count',
            'created_at', 'updated_at', 'resolved_at', 'last_response_at'
        ]
    
    def get_is_mine(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.author_id == request.user.id
        return False
    
    def get_is_bookmarked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return RequestBookmark.objects.filter(
                request=obj,
                user=request.user
            ).exists()
        return False
    
    def get_can_edit(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Can edit if: owner, no responses yet, not resolved
            is_owner = obj.author_id == request.user.id
            has_no_responses = obj.response_count == 0
            return is_owner and has_no_responses and not obj.is_resolved
        return False
    
    def get_can_delete(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Can delete if: owner, no responses yet
            is_owner = obj.author_id == request.user.id
            has_no_responses = obj.response_count == 0
            return is_owner and has_no_responses
        return False


class HelpDeskRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating requests"""
    code_snippets = CodeSnippetSerializer(many=True, required=False)
    images = RequestImageSerializer(many=True, required=False, read_only=True)
    
    class Meta:
        model = HelpDeskRequest
        fields = [
            'title', 'description', 'category', 'priority',
            'tags', 'course', 'code_snippets', 'images'
        ]
    
    def validate_tags(self, value):
        if len(value) > 10:
            raise serializers.ValidationError("Maximum 10 tags allowed")
        for tag in value:
            if len(tag) > 30:
                raise serializers.ValidationError("Each tag must be max 30 characters")
        return value
    
    def create(self, validated_data):
        code_snippets_data = validated_data.pop('code_snippets', [])
        request_obj = HelpDeskRequest.objects.create(**validated_data)
        
        # Create code snippets
        for snippet_data in code_snippets_data:
            CodeSnippet.objects.create(request=request_obj, **snippet_data)
        
        return request_obj


class HelpDeskRequestUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating requests"""
    
    class Meta:
        model = HelpDeskRequest
        fields = ['title', 'description', 'priority', 'tags']
    
    def validate(self, data):
        # Ensure request has no responses
        if self.instance.response_count > 0:
            raise serializers.ValidationError(
                "Cannot edit request that has responses"
            )
        return data


# Response Serializers
class HelpDeskResponseListSerializer(serializers.ModelSerializer):
    """Serializer for response list"""
    code_snippets = ResponseCodeSnippetSerializer(many=True, read_only=True)
    links = ResponseLinkSerializer(many=True, read_only=True)
    is_mine = serializers.SerializerMethodField()
    user_vote = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    author_name = serializers.SerializerMethodField()
    reply_count = serializers.SerializerMethodField()
    
    class Meta:
        model = HelpDeskResponse
        fields = [
            'id', 'request', 'content',
            'code_snippets', 'links',
            'upvotes', 'downvotes', 'user_vote',
            'is_marked_helpful', 'is_mine', 'can_edit',
            'follow_up_count', 'reply_count', 'author_name',
            'created_at', 'updated_at', 'marked_helpful_at'
        ]
        read_only_fields = [
            'id', 'upvotes', 'downvotes', 'is_marked_helpful',
            'follow_up_count', 'created_at', 'updated_at', 'marked_helpful_at'
        ]
    
    def get_is_mine(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.author_id == request.user.id
        return False
    
    def get_user_vote(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            vote = ResponseVote.objects.filter(
                response=obj,
                user=request.user
            ).first()
            return vote.vote_type if vote else None
        return None
    
    def get_can_edit(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            is_owner = obj.author_id == request.user.id
            within_time_limit = (timezone.now() - obj.created_at) < timedelta(minutes=15)
            not_marked_helpful = not obj.is_marked_helpful
            return is_owner and within_time_limit and not_marked_helpful
        return False
    
    def get_author_name(self, obj):
        # Return the author's full name for responses (responses are not anonymous)
        return f"{obj.author.first_name} {obj.author.last_name}".strip() or "Anonymous User"
    
    def get_reply_count(self, obj):
        return ResponseReply.objects.filter(response=obj, is_deleted=False).count()


class HelpDeskResponseCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating responses"""
    code_snippets = ResponseCodeSnippetSerializer(many=True, required=False)
    links = serializers.ListField(
        child=serializers.URLField(),
        required=False,
        max_length=10
    )
    
    class Meta:
        model = HelpDeskResponse
        fields = ['request', 'content', 'code_snippets', 'links']
    
    def validate_links(self, value):
        if len(value) > 10:
            raise serializers.ValidationError("Maximum 10 links allowed")
        return value
    
    def create(self, validated_data):
        code_snippets_data = validated_data.pop('code_snippets', [])
        links_data = validated_data.pop('links', [])
        
        response_obj = HelpDeskResponse.objects.create(**validated_data)
        
        # Create code snippets
        for snippet_data in code_snippets_data:
            ResponseCodeSnippet.objects.create(response=response_obj, **snippet_data)
        
        # Create links
        for link_url in links_data:
            ResponseLink.objects.create(response=response_obj, url=link_url)
        
        # Update request stats
        request_obj = response_obj.request
        request_obj.response_count += 1
        request_obj.last_response_at = timezone.now()
        request_obj.save(update_fields=['response_count', 'last_response_at'])
        
        return response_obj
    
    def to_representation(self, instance):
        """Use the list serializer for the response after creation"""
        return HelpDeskResponseListSerializer(
            instance, 
            context=self.context
        ).data


# Vote Serializer
class ResponseVoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResponseVote
        fields = ['id', 'response', 'vote_type', 'created_at']
        read_only_fields = ['id', 'created_at']


# Bookmark Serializer
class RequestBookmarkSerializer(serializers.ModelSerializer):
    request_detail = HelpDeskRequestListSerializer(source='request', read_only=True)
    
    class Meta:
        model = RequestBookmark
        fields = ['id', 'request', 'request_detail', 'created_at']
        read_only_fields = ['id', 'created_at']


# Notification Serializer
class HelpDeskNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = HelpDeskNotification
        fields = [
            'id', 'notification_type', 'title', 'message',
            'request', 'response',
            'is_read', 'created_at', 'read_at'
        ]
        read_only_fields = ['id', 'created_at', 'read_at']


# Report Serializer
class ContentReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentReport
        fields = [
            'id', 'request', 'response', 'reason', 'description',
            'status', 'created_at'
        ]
        read_only_fields = ['id', 'status', 'created_at']
    
    def validate(self, data):
        # Ensure either request or response is set, not both
        if not data.get('request') and not data.get('response'):
            raise serializers.ValidationError(
                "Either request or response must be specified"
            )
        if data.get('request') and data.get('response'):
            raise serializers.ValidationError(
                "Cannot report both request and response at the same time"
            )
        return data


# User Stats Serializer
class UserReputationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserReputation
        fields = [
            'user', 'points',
            'requests_created', 'requests_resolved',
            'responses_posted', 'helpful_responses',
            'upvotes_received', 'downvotes_received',
            'updated_at'
        ]
        read_only_fields = ['updated_at']


# My Requests Serializer (for author's own requests)
class MyRequestSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    new_response_count = serializers.SerializerMethodField()
    
    class Meta:
        model = HelpDeskRequest
        fields = [
            'id', 'tracking_id', 'title',
            'category', 'category_name', 'priority', 'status',
            'response_count', 'new_response_count', 'helpful_response_count',
            'is_resolved', 'tags',
            'created_at', 'last_response_at'
        ]
    
    def get_new_response_count(self, obj):
        # Count responses created after user's last view
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            last_view = RequestView.objects.filter(
                request=obj,
                user=request.user
            ).order_by('-viewed_at').first()
            
            if last_view:
                return obj.responses.filter(
                    created_at__gt=last_view.viewed_at,
                    is_deleted=False
                ).count()
        return 0


# Helping Requests Serializer (for responses the user made)
class HelpingRequestSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    my_response = serializers.SerializerMethodField()
    
    class Meta:
        model = HelpDeskRequest
        fields = [
            'id', 'tracking_id', 'title',
            'category', 'category_name',
            'my_response',
            'created_at'
        ]
    
    def get_my_response(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            response = obj.responses.filter(
                author=request.user,
                is_deleted=False
            ).first()
            
            if response:
                return {
                    'id': str(response.id),
                    'content': response.content[:100] + '...' if len(response.content) > 100 else response.content,
                    'upvotes': response.upvotes,
                    'is_marked_helpful': response.is_marked_helpful,
                    'follow_up_count': response.follow_up_count,
                    'created_at': response.created_at
                }
        return None
