"""
Hub Serializers - Legal Education Hub & Social Hubs
"""
from rest_framework import serializers
from .models import LegalEdTopic, LegalEdSubTopic
from documents.models import LearningMaterial


class LearningMaterialMinimalSerializer(serializers.ModelSerializer):
    """Minimal learning material info for subtopic listing"""
    uploader_name = serializers.SerializerMethodField()
    
    class Meta:
        model = LearningMaterial
        fields = [
            'id', 'title', 'description', 'category', 'price',
            'file_size', 'downloads_count', 'uploader_name',
            'is_approved', 'is_active', 'created_at'
        ]
    
    def get_uploader_name(self, obj):
        return f"{obj.uploader.first_name} {obj.uploader.last_name}"


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
    """Serializer for topic listing with subtopics count"""
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
