from rest_framework import serializers
from .models import CapabilityProfile, TrainingMaterial
from core.models import Tag
from core.serializers import TagSerializer


class CapabilityProfileSerializer(serializers.ModelSerializer):
    """能力画像序列化器"""
    tag_name = serializers.CharField(source='tag.name', read_only=True)
    tag_category = serializers.CharField(source='tag.category', read_only=True)

    class Meta:
        model = CapabilityProfile
        fields = ('id', 'tag_name', 'tag_category', 'mastery_level',
                 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')


class RadarChartDataSerializer(serializers.Serializer):
    """雷达图数据序列化器"""
    tag = serializers.CharField()
    score = serializers.FloatField()


class TrendChartDataSerializer(serializers.Serializer):
    """趋势图数据序列化器"""
    date = serializers.DateField()
    tag_name = serializers.CharField()
    score = serializers.FloatField()


class TrainingMaterialSerializer(serializers.ModelSerializer):
    """培训资料序列化器"""
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        required=False
    )
    tag_details = TagSerializer(source='tags', many=True, read_only=True)
    creator_name = serializers.CharField(source='creator.username', read_only=True)
    creator_job_number = serializers.CharField(source='creator.job_number', read_only=True)

    class Meta:
        model = TrainingMaterial
        fields = ('id', 'title', 'description', 'material_type',
                 'url', 'file_path', 'tags', 'tag_details',
                 'creator_name', 'creator_job_number', 'is_active', 'is_public', 'created_at')
        read_only_fields = ('id', 'creator_name', 'creator_job_number', 'created_at')


class UserCapabilitySummarySerializer(serializers.Serializer):
    """用户能力总结序列化器"""
    user_id = serializers.IntegerField()
    overall_score = serializers.FloatField()
    weak_tags = serializers.ListField(
        child=serializers.CharField(),
        help_text="需要提升的标签列表"
    )
    strong_tags = serializers.ListField(
        child=serializers.CharField(),
        help_text="表现优秀的标签列表"
    )
    total_exams = serializers.IntegerField()
    recent_accuracy = serializers.FloatField()