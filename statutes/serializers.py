from rest_framework import serializers
from .models import StatuteCategory, Statute


class StatuteCategorySerializer(serializers.ModelSerializer):
    statutes_count = serializers.IntegerField(read_only=True, required=False, default=0)

    class Meta:
        model = StatuteCategory
        fields = [
            'id',
            'name',
            'name_sw',
            'slug',
            'description',
            'description_sw',
            'sort_order',
            'is_active',
            'deleted_at',
            'statutes_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'slug', 'deleted_at', 'statutes_count', 'created_at', 'updated_at']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if 'statutes_count' not in data or data['statutes_count'] is None:
            data['statutes_count'] = getattr(instance, 'statutes_count', None)
            if data['statutes_count'] is None:
                data['statutes_count'] = instance.statutes.filter(
                    is_active=True, deleted_at__isnull=True
                ).count()
        return data


class StatuteCategoryBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatuteCategory
        fields = ['id', 'name', 'name_sw', 'slug']


class StatuteSerializer(serializers.ModelSerializer):
    categories = StatuteCategoryBriefSerializer(many=True, read_only=True)
    category_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=StatuteCategory.objects.alive(),
        source='categories',
        write_only=True,
        required=False,
    )
    file_url = serializers.SerializerMethodField()
    file_size_mb = serializers.SerializerMethodField()

    class Meta:
        model = Statute
        fields = [
            'id',
            'title',
            'title_sw',
            'description',
            'description_sw',
            'file',
            'file_url',
            'file_size',
            'file_size_mb',
            'categories',
            'category_ids',
            'sort_order',
            'is_active',
            'deleted_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'file_size',
            'file_url',
            'file_size_mb',
            'deleted_at',
            'created_at',
            'updated_at',
        ]
        extra_kwargs = {
            'file': {'required': False, 'allow_null': True},
        }

    def get_file_url(self, obj):
        if not obj.file:
            return ''
        request = self.context.get('request')
        url = obj.file.url
        if request:
            return request.build_absolute_uri(url)
        return url

    def get_file_size_mb(self, obj):
        if not obj.file_size:
            return 0
        return round(obj.file_size / (1024 * 1024), 2)

    def validate_file(self, value):
        if value is None:
            return value
        name = getattr(value, 'name', '') or ''
        if not name.lower().endswith('.pdf'):
            raise serializers.ValidationError('Only PDF files are allowed.')
        # 50 MB limit
        if hasattr(value, 'size') and value.size > 50 * 1024 * 1024:
            raise serializers.ValidationError('PDF must be 50MB or smaller.')
        return value

    def to_internal_value(self, data):
        # Multipart form may send booleans / repeated category ids as strings
        if hasattr(data, 'getlist'):
            mutable = data.copy()
            if 'is_active' in mutable:
                raw = mutable.get('is_active')
                if isinstance(raw, str):
                    mutable['is_active'] = raw.lower() in ('1', 'true', 'yes', 'on')
            return super().to_internal_value(mutable)
        return super().to_internal_value(data)

    def create(self, validated_data):
        if not validated_data.get('file'):
            raise serializers.ValidationError({'file': 'PDF file is required.'})
        categories = validated_data.pop('categories', [])
        upload = validated_data.get('file')
        if upload and hasattr(upload, 'size'):
            validated_data['file_size'] = upload.size
        statute = Statute.objects.create(**validated_data)
        if categories:
            statute.categories.set(categories)
        return statute

    def update(self, instance, validated_data):
        categories = validated_data.pop('categories', None)
        upload = validated_data.get('file')
        if upload and hasattr(upload, 'size'):
            validated_data['file_size'] = upload.size
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if categories is not None:
            instance.categories.set(categories)
        return instance
