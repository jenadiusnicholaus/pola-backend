"""
Admin Serializers for Hubs Management
Comprehensive serializers for admin topic/subtopic management
"""
from rest_framework import serializers
from .models import LegalEdTopic, LegalEdSubTopic
from documents.models import LearningMaterial


class SubtopicBasicSerializer(serializers.ModelSerializer):
    """Basic subtopic info for nested display"""
    materials_count = serializers.SerializerMethodField()
    
    class Meta:
        model = LegalEdSubTopic
        fields = [
            'id', 'name', 'name_sw', 'slug', 
            'display_order', 'is_active', 'materials_count'
        ]
        ref_name = 'AdminSubtopicBasic'
    
    def get_materials_count(self, obj):
        return obj.get_materials_count()


class TopicAdminListSerializer(serializers.ModelSerializer):
    """Serializer for listing topics in admin"""
    subtopics_count = serializers.SerializerMethodField()
    materials_count = serializers.SerializerMethodField()
    
    class Meta:
        model = LegalEdTopic
        fields = [
            'id', 'name', 'name_sw', 'slug', 
            'description', 'description_sw',
            'icon', 'display_order', 'is_active',
            'subtopics_count', 'materials_count',
            'created_at', 'last_updated'
        ]
        ref_name = 'AdminTopicList'
    
    def get_subtopics_count(self, obj):
        return obj.get_subtopics_count()
    
    def get_materials_count(self, obj):
        return obj.get_materials_count()


class TopicAdminDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for topic admin with full statistics"""
    subtopics_count = serializers.SerializerMethodField()
    materials_count = serializers.SerializerMethodField()
    active_subtopics_count = serializers.SerializerMethodField()
    subtopics = SubtopicBasicSerializer(many=True, read_only=True)
    
    class Meta:
        model = LegalEdTopic
        fields = [
            'id', 'name', 'name_sw', 'slug',
            'description', 'description_sw',
            'icon', 'display_order', 'is_active',
            'subtopics_count', 'active_subtopics_count', 
            'materials_count', 'subtopics',
            'created_at', 'last_updated'
        ]
        ref_name = 'AdminTopicDetail'
    
    def get_subtopics_count(self, obj):
        return obj.subtopics.count()
    
    def get_active_subtopics_count(self, obj):
        return obj.subtopics.filter(is_active=True).count()
    
    def get_materials_count(self, obj):
        return obj.get_materials_count()


class TopicAdminCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating topics"""
    slug = serializers.SlugField(required=False, allow_blank=True, help_text="Auto-generated from name if not provided")
    
    class Meta:
        model = LegalEdTopic
        fields = [
            'name', 'name_sw', 'slug',
            'description', 'description_sw',
            'icon', 'display_order', 'is_active'
        ]
        ref_name = 'AdminTopicCreateUpdate'
    
    def validate_name(self, value):
        """Ensure topic name is unique"""
        topic_id = self.instance.id if self.instance else None
        if LegalEdTopic.objects.filter(name=value).exclude(id=topic_id).exists():
            raise serializers.ValidationError("A topic with this name already exists.")
        return value
    
    def validate_slug(self, value):
        """Ensure slug is unique if provided"""
        if not value:  # Skip validation if empty
            return value
        topic_id = self.instance.id if self.instance else None
        if LegalEdTopic.objects.filter(slug=value).exclude(id=topic_id).exists():
            raise serializers.ValidationError("A topic with this slug already exists.")
        return value
    
    def create(self, validated_data):
        """Auto-generate slug from name if not provided"""
        from django.utils.text import slugify
        
        if not validated_data.get('slug'):
            # Generate slug from name
            base_slug = slugify(validated_data['name'])
            slug = base_slug
            counter = 1
            
            # Ensure uniqueness
            while LegalEdTopic.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            validated_data['slug'] = slug
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Auto-generate slug from name if not provided and name changed"""
        from django.utils.text import slugify
        
        # If name changed and slug not provided, regenerate slug
        if 'name' in validated_data and not validated_data.get('slug'):
            if validated_data['name'] != instance.name:
                base_slug = slugify(validated_data['name'])
                slug = base_slug
                counter = 1
                
                # Ensure uniqueness (excluding current instance)
                while LegalEdTopic.objects.filter(slug=slug).exclude(id=instance.id).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                
                validated_data['slug'] = slug
        
        return super().update(instance, validated_data)


class SubtopicAdminListSerializer(serializers.ModelSerializer):
    """Serializer for listing subtopics in admin"""
    topic_name = serializers.CharField(source='topic.name', read_only=True)
    topic_name_sw = serializers.CharField(source='topic.name_sw', read_only=True)
    materials_count = serializers.SerializerMethodField()
    
    class Meta:
        model = LegalEdSubTopic
        fields = [
            'id', 'topic', 'topic_name', 'topic_name_sw',
            'name', 'name_sw', 'slug',
            'description', 'description_sw',
            'display_order', 'is_active', 'materials_count',
            'created_at', 'last_updated'
        ]
        ref_name = 'AdminSubtopicList'
    
    def get_materials_count(self, obj):
        return obj.get_materials_count()


class SubtopicAdminDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for subtopic admin with statistics"""
    topic_name = serializers.CharField(source='topic.name', read_only=True)
    topic_name_sw = serializers.CharField(source='topic.name_sw', read_only=True)
    topic_slug = serializers.CharField(source='topic.slug', read_only=True)
    materials_count = serializers.SerializerMethodField()
    active_materials_count = serializers.SerializerMethodField()
    approved_materials_count = serializers.SerializerMethodField()
    
    class Meta:
        model = LegalEdSubTopic
        fields = [
            'id', 'topic', 'topic_name', 'topic_name_sw', 'topic_slug',
            'name', 'name_sw', 'slug',
            'description', 'description_sw',
            'display_order', 'is_active',
            'materials_count', 'active_materials_count', 
            'approved_materials_count',
            'created_at', 'last_updated'
        ]
        ref_name = 'AdminSubtopicDetail'
    
    def get_materials_count(self, obj):
        return LearningMaterial.objects.filter(subtopic=obj).count()
    
    def get_active_materials_count(self, obj):
        return LearningMaterial.objects.filter(subtopic=obj, is_active=True).count()
    
    def get_approved_materials_count(self, obj):
        return LearningMaterial.objects.filter(subtopic=obj, is_approved=True).count()


class SubtopicAdminCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating subtopics"""
    slug = serializers.SlugField(required=False, allow_blank=True, help_text="Auto-generated from name if not provided")
    
    class Meta:
        model = LegalEdSubTopic
        fields = [
            'topic', 'name', 'name_sw', 'slug',
            'description', 'description_sw',
            'display_order', 'is_active'
        ]
        ref_name = 'AdminSubtopicCreateUpdate'
    
    def validate_name(self, value):
        """Ensure subtopic name is unique within topic"""
        subtopic_id = self.instance.id if self.instance else None
        topic = self.initial_data.get('topic') or (self.instance.topic_id if self.instance else None)
        
        if topic:
            if LegalEdSubTopic.objects.filter(
                topic_id=topic, 
                name=value
            ).exclude(id=subtopic_id).exists():
                raise serializers.ValidationError(
                    "A subtopic with this name already exists in this topic."
                )
        return value
    
    def validate_slug(self, value):
        """Ensure slug is unique if provided"""
        if not value:  # Skip validation if empty
            return value
        subtopic_id = self.instance.id if self.instance else None
        if LegalEdSubTopic.objects.filter(slug=value).exclude(id=subtopic_id).exists():
            raise serializers.ValidationError("A subtopic with this slug already exists.")
        return value
    
    def create(self, validated_data):
        """Auto-generate slug from name if not provided"""
        from django.utils.text import slugify
        
        if not validated_data.get('slug'):
            # Generate slug from name
            base_slug = slugify(validated_data['name'])
            slug = base_slug
            counter = 1
            
            # Ensure uniqueness
            while LegalEdSubTopic.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            validated_data['slug'] = slug
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Auto-generate slug from name if not provided and name changed"""
        from django.utils.text import slugify
        
        # If name changed and slug not provided, regenerate slug
        if 'name' in validated_data and not validated_data.get('slug'):
            if validated_data['name'] != instance.name:
                base_slug = slugify(validated_data['name'])
                slug = base_slug
                counter = 1
                
                # Ensure uniqueness (excluding current instance)
                while LegalEdSubTopic.objects.filter(slug=slug).exclude(id=instance.id).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                
                validated_data['slug'] = slug
        
        return super().update(instance, validated_data)


class ReorderSerializer(serializers.Serializer):
    """Serializer for reordering topics/subtopics"""
    items = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField()
        ),
        help_text="List of {id: display_order} mappings"
    )
    
    class Meta:
        ref_name = 'AdminReorder'
    
    def validate_items(self, value):
        """Validate items structure"""
        for item in value:
            if 'id' not in item or 'display_order' not in item:
                raise serializers.ValidationError(
                    "Each item must have 'id' and 'display_order' fields."
                )
        return value


class BulkToggleSerializer(serializers.Serializer):
    """Serializer for bulk toggle active status"""
    ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of IDs to toggle"
    )
    is_active = serializers.BooleanField(help_text="Target active status")
    
    class Meta:
        ref_name = 'AdminBulkToggle'


class TopicStatsSerializer(serializers.Serializer):
    """Serializer for topic statistics"""
    total_topics = serializers.IntegerField()
    active_topics = serializers.IntegerField()
    inactive_topics = serializers.IntegerField()
    total_subtopics = serializers.IntegerField()
    total_materials = serializers.IntegerField()
    topics_without_subtopics = serializers.IntegerField()
    topics_without_materials = serializers.IntegerField()
    
    class Meta:
        ref_name = 'AdminTopicStats'


class SubtopicStatsSerializer(serializers.Serializer):
    """Serializer for subtopic statistics"""
    total_subtopics = serializers.IntegerField()
    active_subtopics = serializers.IntegerField()
    inactive_subtopics = serializers.IntegerField()
    total_materials = serializers.IntegerField()
    subtopics_without_materials = serializers.IntegerField()
    avg_materials_per_subtopic = serializers.FloatField()
    
    class Meta:
        ref_name = 'AdminSubtopicStats'
