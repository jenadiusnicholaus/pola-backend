"""
Hub Serializers - Legal Education Hub & Social Hubs
"""
from rest_framework import serializers
from django.db.models import Avg
from .models import (
    LegalEdTopic, LegalEdSubTopic, HubComment, ContentLike, 
    ContentBookmark, HubCommentLike, HubMessage
)
from documents.models import (
    LearningMaterial, LearningMaterialPurchase, LecturerFollow, 
    MaterialQuestion, MaterialRating
)
from authentication.models import PolaUser
from decimal import Decimal
from utils.base64_fields import Base64AnyFileField


class LearningMaterialMinimalSerializer(serializers.ModelSerializer):
    """Minimal learning material info for subtopic listing"""
    uploader_name = serializers.SerializerMethodField()
    file = serializers.SerializerMethodField()
    
    class Meta:
        model = LearningMaterial
        fields = [
            'id', 'title', 'description', 'content_type', 'price',
            'file', 'file_size', 'downloads_count', 'uploader_name',
            'is_approved', 'is_active', 'created_at'
        ]
    
    def get_uploader_name(self, obj):
        return f"{obj.uploader.first_name} {obj.uploader.last_name}"
    
    def get_file(self, obj):
        """Get file URL if available"""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
        return None


class SubtopicMinimalSerializer(serializers.ModelSerializer):
    """Minimal subtopic info for topic listing"""
    materials_count = serializers.SerializerMethodField()
    
    class Meta:
        model = LegalEdSubTopic
        fields = [
            'id', 'name', 'name_sw', 'slug', 'description',
            'description_sw', 'display_order', 'materials_count',
            'is_active'
        ]
    
    def get_materials_count(self, obj):
        return obj.get_materials_count()


class TopicListSerializer(serializers.ModelSerializer):
    """Simple serializer for topic listing"""
    subtopics_count = serializers.SerializerMethodField()
    materials_count = serializers.SerializerMethodField()
    
    class Meta:
        model = LegalEdTopic
        fields = [
            'id', 'name', 'name_sw', 'slug', 'description', 'description_sw',
            'icon', 'display_order', 'is_active', 'subtopics_count',
            'materials_count', 'created_at', 'last_updated'
        ]
    
    def get_subtopics_count(self, obj):
        return obj.get_subtopics_count()
    
    def get_materials_count(self, obj):
        return obj.get_materials_count()


class TopicDetailSerializer(serializers.ModelSerializer):
    """Detailed topic serializer with subtopics"""
    subtopics = SubtopicMinimalSerializer(many=True, read_only=True)
    subtopics_count = serializers.SerializerMethodField()
    materials_count = serializers.SerializerMethodField()
    
    class Meta:
        model = LegalEdTopic
        fields = [
            'id', 'name', 'name_sw', 'slug', 'description', 'description_sw',
            'icon', 'display_order', 'is_active', 'subtopics',
            'subtopics_count', 'materials_count', 'created_at', 'last_updated'
        ]
    
    def get_subtopics_count(self, obj):
        return obj.get_subtopics_count()
    
    def get_materials_count(self, obj):
        return obj.get_materials_count()


class SubtopicListSerializer(serializers.ModelSerializer):
    """Serializer for subtopic listing"""
    topic_name = serializers.CharField(source='topic.name', read_only=True)
    topic_name_sw = serializers.CharField(source='topic.name_sw', read_only=True)
    materials_count = serializers.SerializerMethodField()
    
    class Meta:
        model = LegalEdSubTopic
        fields = [
            'id', 'topic', 'topic_name', 'topic_name_sw', 'name', 'name_sw',
            'slug', 'description', 'description_sw', 'display_order',
            'is_active', 'materials_count', 'created_at', 'last_updated'
        ]
    
    def get_materials_count(self, obj):
        return obj.get_materials_count()


class SubtopicDetailSerializer(serializers.ModelSerializer):
    """Detailed subtopic serializer with materials"""
    topic_name = serializers.CharField(source='topic.name', read_only=True)
    topic_name_sw = serializers.CharField(source='topic.name_sw', read_only=True)
    materials = LearningMaterialMinimalSerializer(many=True, read_only=True)
    materials_count = serializers.SerializerMethodField()
    
    class Meta:
        model = LegalEdSubTopic
        fields = [
            'id', 'topic', 'topic_name', 'topic_name_sw', 'name', 'name_sw',
            'slug', 'description', 'description_sw', 'display_order',
            'is_active', 'materials', 'materials_count', 'created_at', 'last_updated'
        ]


# ============================================================================
# UNIFIED HUB SERIALIZERS - Works for all hubs (Advocates, Students, Forum)
# ============================================================================

from .models import HubComment, ContentLike, ContentBookmark, HubCommentLike, HubMessage
from documents.models import LearningMaterialPurchase, LecturerFollow, MaterialQuestion, MaterialRating
from authentication.models import PolaUser
from django.db.models import Avg


class UserMinimalSerializer(serializers.ModelSerializer):
    """Minimal user info for content authors"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    is_verified = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    
    class Meta:
        model = PolaUser
        fields = ['id', 'email', 'full_name', 'user_role', 'is_verified', 'avatar_url']
        read_only_fields = fields
    
    def get_is_verified(self, obj):
        """Check if user has verified account"""
        return hasattr(obj, 'verification') and obj.verification.status == 'verified'
    
    def get_avatar_url(self, obj):
        """Get avatar URL"""
        if obj.profile_picture:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_picture.url)
        return None


class HubContentSerializer(serializers.ModelSerializer):
    """
    Unified serializer for ALL hub content (posts + documents)
    Works across: Advocates Hub, Students Hub, Community Forum, Legal Education
    """
    uploader_info = UserMinimalSerializer(source='uploader', read_only=True)
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    bookmarks_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()
    has_purchased = serializers.SerializerMethodField()
    can_download = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    ratings_count = serializers.SerializerMethodField()
    file = serializers.SerializerMethodField()
    
    class Meta:
        model = LearningMaterial
        fields = [
            'id', 'hub_type', 'content_type', 'uploader_info', 'uploader_type',
            'title', 'description', 'content', 'file', 'file_size',
            'video_url', 'language', 'price', 'is_downloadable',
            'is_lecture_material', 'is_verified_quality', 'is_pinned',
            'views_count', 'downloads_count', 
            'likes_count', 'comments_count', 'bookmarks_count',
            'average_rating', 'ratings_count',
            'is_liked', 'is_bookmarked', 'has_purchased', 'can_download',
            'is_approved', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'uploader_info', 'downloads_count', 'views_count',
            'likes_count', 'comments_count', 'bookmarks_count',
            'is_liked', 'is_bookmarked', 'has_purchased', 'can_download',
            'average_rating', 'ratings_count', 'file', 'created_at', 'updated_at'
        ]
    
    def get_likes_count(self, obj):
        return obj.get_likes_count()
    
    def get_comments_count(self, obj):
        return obj.get_comments_count()
    
    def get_bookmarks_count(self, obj):
        return obj.get_bookmarks_count()
    
    def get_is_liked(self, obj):
        """Check if current user liked this content"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ContentLike.objects.filter(user=request.user, content=obj).exists()
        return False
    
    def get_is_bookmarked(self, obj):
        """Check if current user bookmarked this content"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ContentBookmark.objects.filter(user=request.user, content=obj).exists()
        return False
    
    def get_has_purchased(self, obj):
        """Check if user has purchased/can access this material"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        # Django admin users (staff/superuser) have access to all content
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Free content is always accessible
        if obj.price == 0:
            return True
        
        # Check if purchased
        return LearningMaterialPurchase.objects.filter(
            buyer=request.user, 
            material=obj
        ).exists()
    
    def get_can_download(self, obj):
        """Check if user can download this content"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        # Django admin users (staff/superuser) can download all content if it's downloadable
        if (request.user.is_staff or request.user.is_superuser) and obj.is_downloadable:
            return True
        
        # Must be downloadable
        if not obj.is_downloadable:
            return False
        
        # Check if purchased or free
        return self.get_has_purchased(obj)
    
    def get_average_rating(self, obj):
        """Calculate average rating"""
        result = obj.ratings.aggregate(avg_rating=Avg('rating'))
        avg = result['avg_rating']
        return round(avg, 1) if avg else None
    
    def get_ratings_count(self, obj):
        """Get total number of ratings"""
        return obj.ratings.count()
    
    def get_file(self, obj):
        """Get file URL if user has access - UNIFIED logic for all hubs"""
        if not obj.file:
            return None
        
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        # UNIFIED LOGIC: Show files for all hubs if user has access
        # This covers both free content (images, attachments) and paid downloadable content
        if self.get_has_purchased(obj):
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        
        return None
    
    def validate(self, data):
        """Validate hub-specific rules"""
        hub_type = data.get('hub_type')
        uploader_type = data.get('uploader_type')
        request = self.context.get('request')
        
        # Advocates Hub - only advocates and admins can post
        if hub_type == 'advocates':
            if uploader_type not in ['advocate', 'admin']:
                raise serializers.ValidationError({
                    'uploader_type': 'Only advocates and admins can post in Advocates Hub'
                })
            if request and request.user.user_role not in ['advocate', 'admin']:
                raise serializers.ValidationError({
                    'hub_type': 'You must be an advocate to post here'
                })
        
        # Students Hub - students, lecturers, admins can post
        elif hub_type == 'students':
            if uploader_type not in ['student', 'lecturer', 'admin']:
                raise serializers.ValidationError({
                    'uploader_type': 'Only students, lecturers, and admins can post in Students Hub'
                })
        
        return data


class HubContentCreateSerializer(serializers.ModelSerializer):
    """
    Content creation serializer with Base64 file upload support
    Used for creating content/posts/materials across all hubs
    """
    file = Base64AnyFileField(
        required=False, 
        allow_null=True,
        max_file_size=50 * 1024 * 1024,  # 50MB limit
        allowed_types=['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'ppt', 'pptx', 'xls', 'xlsx'],
        document_type=None  # Will be set based on content_type if needed
    )
    
    class Meta:
        model = LearningMaterial
        fields = [
            'hub_type', 'content_type', 'title', 'description', 'content',
            'file', 'video_url', 'language', 'price', 'is_downloadable',
            'is_lecture_material', 'is_pinned', 'topic', 'subtopic'
        ]
        
    def validate(self, data):
        """Validate content creation with hub-specific rules"""
        hub_type = data.get('hub_type')
        content_type = data.get('content_type')
        request = self.context.get('request')
        user = request.user if request else None
        
        # Validate user permissions for each hub
        if hub_type == 'advocates':
            # Only verified advocates and admins
            if not user or not user.is_authenticated:
                raise serializers.ValidationError({'detail': 'Authentication required'})
            
            user_role = getattr(user, 'user_role', None)
            role_name = user_role.role_name if user_role else None
            
            if role_name not in ['advocate', 'lawyer'] and not user.is_staff:
                raise serializers.ValidationError({
                    'hub_type': 'Only advocates, lawyers, and admins can post in Advocates Hub'
                })
            
            # Check verification for advocates
            if role_name in ['advocate', 'lawyer'] and not getattr(user, 'is_verified', False):
                raise serializers.ValidationError({
                    'detail': 'Only verified advocates can post in Advocates Hub'
                })
            
            data['uploader_type'] = 'advocate' if role_name in ['advocate', 'lawyer'] else 'admin'
            
        elif hub_type == 'students':
            # Students, lecturers, admins
            if not user or not user.is_authenticated:
                raise serializers.ValidationError({'detail': 'Authentication required'})
            
            user_role = getattr(user, 'user_role', None) 
            role_name = user_role.role_name if user_role else None
            
            if role_name not in ['student', 'lecturer'] and not user.is_staff:
                raise serializers.ValidationError({
                    'hub_type': 'Only students, lecturers, and admins can post in Students Hub'
                })
            
            data['uploader_type'] = role_name if role_name in ['student', 'lecturer'] else 'admin'
            
        elif hub_type == 'forum':
            # Everyone can post in forum
            if not user or not user.is_authenticated:
                raise serializers.ValidationError({'detail': 'Authentication required'})
            
            user_role = getattr(user, 'user_role', None)
            role_name = user_role.role_name if user_role else 'citizen'
            data['uploader_type'] = 'admin' if user.is_staff else role_name
            
        elif hub_type == 'legal_ed':
            # Only admins can post in legal education
            if not user or not user.is_staff:
                raise serializers.ValidationError({
                    'detail': 'Only admins can create legal education content'
                })
            data['uploader_type'] = 'admin'
        
        # Validate content type for hub
        valid_content_types = {
            'advocates': ['discussion', 'article', 'news', 'case_study', 'legal_update'],
            'students': ['notes', 'past_papers', 'assignment', 'discussion', 'question', 'tutorial'],
            'forum': ['discussion', 'question', 'news', 'general'],
            'legal_ed': ['lecture', 'article', 'tutorial', 'case_study', 'legal_update']
        }
        
        if content_type not in valid_content_types.get(hub_type, []):
            raise serializers.ValidationError({
                'content_type': f'Invalid content type for {hub_type} hub. Allowed: {", ".join(valid_content_types.get(hub_type, []))}'
            })
        
        # Set pricing rules
        if content_type in ['news', 'discussion', 'announcement', 'question', 'article', 'general']:
            # These content types should be free
            data['price'] = Decimal('0.00')
            data['is_downloadable'] = False
        else:
            # Set default price if not provided
            if 'price' not in data:
                data['price'] = Decimal('0.00')
        
        # Legal education content should link to topics (subtopics are deprecated)
        if hub_type == 'legal_ed':
            if not data.get('topic') and not data.get('subtopic'):
                raise serializers.ValidationError({
                    'topic': 'Legal education content must be linked to a topic'
                })
        
        return data
    
    def create(self, validated_data):
        """Create content with current user as uploader"""
        request = self.context.get('request')
        validated_data['uploader'] = request.user
        
        # Auto-approve admin content
        if request.user.is_staff:
            validated_data['is_approved'] = True
        
        # Set default values
        validated_data['is_active'] = True
        
        return super().create(validated_data)


class HubCommentSerializer(serializers.ModelSerializer):
    """Unified comment serializer for all hubs"""
    author_info = UserMinimalSerializer(source='author', read_only=True)
    likes_count = serializers.SerializerMethodField()
    replies_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = HubComment
        fields = [
            'id', 'hub_type', 'content', 'author_info', 'parent_comment',
            'comment_text', 'likes_count', 'replies_count', 'is_liked',
            'replies', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'author_info', 'likes_count', 'replies_count',
            'is_liked', 'replies', 'created_at', 'updated_at'
        ]
    
    def get_likes_count(self, obj):
        return obj.get_likes_count()
    
    def get_replies_count(self, obj):
        return obj.get_replies_count()
    
    def get_is_liked(self, obj):
        """Check if current user liked this comment"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return HubCommentLike.objects.filter(user=request.user, comment=obj).exists()
        return False
    
    def get_replies(self, obj):
        """Get nested replies (only for top-level comments)"""
        if obj.parent_comment is None:
            replies = obj.replies.filter(is_active=True).order_by('created_at')[:10]
            return HubCommentSerializer(replies, many=True, context=self.context).data
        return []


class ContentLikeSerializer(serializers.ModelSerializer):
    """Serializer for content likes"""
    user_info = UserMinimalSerializer(source='user', read_only=True)
    
    class Meta:
        model = ContentLike
        fields = ['id', 'user_info', 'content', 'created_at']
        read_only_fields = ['id', 'user_info', 'created_at']


class ContentBookmarkSerializer(serializers.ModelSerializer):
    """Serializer for content bookmarks"""
    content_info = HubContentSerializer(source='content', read_only=True)
    
    class Meta:
        model = ContentBookmark
        fields = ['id', 'content_info', 'created_at']
        read_only_fields = ['id', 'content_info', 'created_at']


class LecturerFollowSerializer(serializers.ModelSerializer):
    """Serializer for following lecturers (Students Hub)"""
    lecturer_info = UserMinimalSerializer(source='lecturer', read_only=True)
    materials_count = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()
    
    class Meta:
        model = LecturerFollow
        fields = [
            'id', 'lecturer_info', 'is_active', 'notifications_enabled',
            'materials_count', 'followers_count', 'followed_at'
        ]
        read_only_fields = ['id', 'lecturer_info', 'materials_count', 'followers_count', 'followed_at']
    
    def get_materials_count(self, obj):
        """Count of materials by this lecturer"""
        return LearningMaterial.objects.filter(
            uploader=obj.lecturer,
            uploader_type='lecturer',
            hub_type='students',
            is_active=True,
            is_approved=True
        ).count()
    
    def get_followers_count(self, obj):
        """Total followers of this lecturer"""
        return LecturerFollow.objects.filter(
            lecturer=obj.lecturer,
            is_active=True
        ).count()


class MaterialQuestionSerializer(serializers.ModelSerializer):
    """Serializer for general legal questions (material optional)"""
    asker_info = UserMinimalSerializer(source='asker', read_only=True)
    answerer_info = UserMinimalSerializer(source='answered_by', read_only=True)
    material_title = serializers.CharField(source='material.title', read_only=True, allow_null=True)
    
    class Meta:
        model = MaterialQuestion
        fields = [
            'id', 'material', 'material_title', 'asker_info', 'question_text',
            'answer_text', 'answerer_info', 'answered_at',
            'status', 'is_answered_by_uploader', 'helpful_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'material_title', 'asker_info', 'answerer_info', 'answered_at',
            'is_answered_by_uploader', 'helpful_count', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'material': {'required': False, 'allow_null': True}
        }


class MaterialRatingSerializer(serializers.ModelSerializer):
    """Serializer for material ratings"""
    rater_info = UserMinimalSerializer(source='rater', read_only=True)
    material_title = serializers.CharField(source='material.title', read_only=True)
    
    class Meta:
        model = MaterialRating
        fields = [
            'id', 'material', 'material_title', 'rater_info', 
            'rating', 'review', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'material_title', 'rater_info', 'created_at', 'updated_at']
    
    def validate_rating(self, value):
        """Validate rating is between 1-5"""
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value


class HubMessageSerializer(serializers.ModelSerializer):
    """Serializer for private messages"""
    sender_info = UserMinimalSerializer(source='sender', read_only=True)
    recipient_info = UserMinimalSerializer(source='recipient', read_only=True)
    
    class Meta:
        model = HubMessage
        fields = [
            'id', 'hub_type', 'sender_info', 'recipient_info',
            'subject', 'message', 'is_read', 'read_at', 'created_at'
        ]
        read_only_fields = [
            'id', 'sender_info', 'recipient_info', 'is_read', 'read_at', 'created_at'
        ]


# ============================================================================
# ADMIN CRUD SERIALIZERS
# ============================================================================

class AdminContentCreateSerializer(serializers.ModelSerializer):
    """
    Admin serializer for CREATING content (news, discussions, posts)
    
    Simplified creation with smart defaults:
    - Auto-fills admin user as uploader
    - Auto-approves content
    - Sets sensible defaults for price, active status
    - Supports topic creation if not exists
    """
    file = Base64AnyFileField(
        required=False, 
        allow_null=True,
        max_file_size=50 * 1024 * 1024,  # 50MB limit
        allowed_types=['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'ppt', 'pptx', 'xls', 'xlsx'],
        document_type=None
    )
    
    # Allow creating new topic by name if it doesn't exist
    topic_name = serializers.CharField(
        required=False, 
        allow_blank=True,
        help_text="Create new topic by name if topic ID not provided"
    )
    
    class Meta:
        model = LearningMaterial
        fields = [
            'hub_type', 'content_type', 'title', 'description', 'content',
            'file', 'video_url', 'language', 'price', 'is_downloadable',
            'is_pinned', 'is_active', 'is_approved', 'topic', 'topic_name'
        ]
    
    def validate(self, data):
        """Validate and set defaults"""
        # Default price to 0 for non-downloadable content
        if not data.get('is_downloadable', False):
            data['price'] = Decimal('0.00')
        
        # Ensure price is set
        if 'price' not in data:
            data['price'] = Decimal('0.00')
        
        # News, discussions, announcements should always be free
        if data.get('content_type') in ['news', 'discussion', 'announcement', 'question', 'article']:
            data['price'] = Decimal('0.00')
            data['is_downloadable'] = False
        
        # Handle topic creation for legal_ed hub
        if data.get('hub_type') == 'legal_ed':
            topic_name = data.pop('topic_name', None)
            topic = data.get('topic')
            
            if not topic and topic_name:
                # Create new topic if it doesn't exist
                from .models import LegalEdTopic
                from django.utils.text import slugify
                
                # Check if topic already exists
                existing_topic = LegalEdTopic.objects.filter(name__iexact=topic_name).first()
                if existing_topic:
                    data['topic'] = existing_topic
                else:
                    # Create new topic
                    new_topic = LegalEdTopic.objects.create(
                        name=topic_name,
                        slug=slugify(topic_name),
                        description=f"Auto-created topic: {topic_name}",
                        display_order=LegalEdTopic.objects.count() + 1,
                        is_active=True
                    )
                    data['topic'] = new_topic
            
            elif not topic and not topic_name:
                raise serializers.ValidationError({
                    'topic': 'Legal education content must have a topic. Provide topic ID or topic_name to create new topic.'
                })
        
        return data
    
    def create(self, validated_data):
        """Create content with admin as uploader"""
        request = self.context.get('request')
        
        # Set uploader to current admin user
        validated_data['uploader'] = request.user
        validated_data['uploader_type'] = 'admin'
        
        # Auto-approve admin content
        validated_data['is_approved'] = validated_data.get('is_approved', True)
        validated_data['is_active'] = validated_data.get('is_active', True)
        
        return super().create(validated_data)


class AdminContentUpdateSerializer(serializers.ModelSerializer):
    """
    Admin serializer for UPDATING content
    
    Allows updating all fields including moderation status
    """
    file = Base64AnyFileField(
        required=False, 
        allow_null=True,
        max_file_size=50 * 1024 * 1024,  # 50MB limit
        allowed_types=['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'ppt', 'pptx', 'xls', 'xlsx'],
        document_type=None
    )
    
    class Meta:
        model = LearningMaterial
        fields = [
            'hub_type', 'content_type', 'title', 'description', 'content',
            'file', 'video_url', 'language', 'price', 'is_downloadable',
            'is_pinned', 'is_active', 'is_approved', 'is_lecture_material',
            'is_verified_quality', 'subtopic', 'views_count', 'downloads_count'
        ]
    
    def validate(self, data):
        """Validate updates"""
        # News/discussions should remain free
        if data.get('content_type') in ['news', 'discussion', 'announcement', 'question', 'article']:
            if 'price' in data and data['price'] > 0:
                data['price'] = Decimal('0.00')
            if 'is_downloadable' in data:
                data['is_downloadable'] = False
        
        return data


class AdminContentDetailSerializer(serializers.ModelSerializer):
    """
    Admin serializer for READING content with full details
    
    Includes all fields, engagement stats, and relationships
    """
    uploader_info = UserMinimalSerializer(source='uploader', read_only=True)
    subtopic_info = SubtopicMinimalSerializer(source='subtopic', read_only=True)
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    bookmarks_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    ratings_count = serializers.SerializerMethodField()
    engagement_score = serializers.SerializerMethodField()
    revenue_info = serializers.SerializerMethodField()
    
    class Meta:
        model = LearningMaterial
        fields = '__all__'
    
    def get_likes_count(self, obj):
        return obj.likes.count()
    
    def get_comments_count(self, obj):
        return obj.comments.count()
    
    def get_bookmarks_count(self, obj):
        return obj.bookmarks.count()
    
    def get_average_rating(self, obj):
        result = obj.ratings.aggregate(avg_rating=Avg('rating'))
        avg = result['avg_rating']
        return round(avg, 1) if avg else None
    
    def get_ratings_count(self, obj):
        return obj.ratings.count()
    
    def get_engagement_score(self, obj):
        """Calculate engagement score: (likes × 2) + (comments × 3) + (bookmarks × 4)"""
        likes = self.get_likes_count(obj)
        comments = self.get_comments_count(obj)
        bookmarks = self.get_bookmarks_count(obj)
        return (likes * 2) + (comments * 3) + (bookmarks * 4)
    
    def get_revenue_info(self, obj):
        """Get revenue breakdown"""
        return {
            'total_revenue': float(obj.total_revenue),
            'uploader_earnings': float(obj.uploader_earnings),
            'platform_earnings': float(obj.platform_earnings),
            'price': float(obj.price),
            'downloads': obj.downloads_count,
        }


class AdminContentListSerializer(serializers.ModelSerializer):
    """
    Admin serializer for LISTING content (optimized for list view)
    
    Lighter version with essential fields and basic stats
    """
    uploader_name = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    engagement_score = serializers.SerializerMethodField()
    
    class Meta:
        model = LearningMaterial
        fields = [
            'id', 'hub_type', 'content_type', 'title', 'uploader_name',
            'uploader_type', 'price', 'views_count', 'downloads_count',
            'likes_count', 'comments_count', 'engagement_score',
            'is_pinned', 'is_active', 'is_approved', 'created_at', 'updated_at'
        ]
    
    def get_uploader_name(self, obj):
        return f"{obj.uploader.first_name} {obj.uploader.last_name}"
    
    def get_likes_count(self, obj):
        return obj.likes.count()
    
    def get_comments_count(self, obj):
        return obj.comments.count()
    
    def get_engagement_score(self, obj):
        """Calculate engagement score"""
        likes = self.get_likes_count(obj)
        comments = self.get_comments_count(obj)
        bookmarks = obj.bookmarks.count()
        return (likes * 2) + (comments * 3) + (bookmarks * 4)


class BulkActionSerializer(serializers.Serializer):
    """Serializer for bulk actions on multiple content items"""
    content_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of content IDs to perform action on"
    )
    action = serializers.ChoiceField(
        choices=[
            ('pin', 'Pin content'),
            ('unpin', 'Unpin content'),
            ('approve', 'Approve content'),
            ('reject', 'Reject content'),
            ('activate', 'Activate content'),
            ('deactivate', 'Deactivate content'),
            ('delete', 'Delete content'),
        ],
        help_text="Action to perform on selected content"
    )
    
    def validate_content_ids(self, value):
        """Validate that all IDs exist"""
        if not value:
            raise serializers.ValidationError("At least one content ID is required")
        
        # Check if all IDs exist
        existing_ids = LearningMaterial.objects.filter(id__in=value).values_list('id', flat=True)
        missing_ids = set(value) - set(existing_ids)
        
        if missing_ids:
            raise serializers.ValidationError(
                f"Content IDs not found: {', '.join(map(str, missing_ids))}"
            )
        
        return value

