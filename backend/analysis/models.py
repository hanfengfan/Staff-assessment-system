from django.db import models
from django.contrib.auth import get_user_model
from core.models import BaseTimestampedModel, Tag

User = get_user_model()


class CapabilityProfile(BaseTimestampedModel):
    """能力画像模型，记录用户在各标签下的能力水平"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='capability_profiles',
        verbose_name='关联用户'
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name='capability_profiles',
        verbose_name='关联标签'
    )
    mastery_level = models.FloatField(
        default=50.0,
        verbose_name='掌握度评分',
        help_text='0-100，数值越高表示掌握程度越好'
    )

    class Meta:
        verbose_name = '能力画像'
        verbose_name_plural = '能力画像'
        db_table = 'capability_profiles'
        unique_together = ['user', 'tag']
        ordering = ['user', 'tag']

    def __str__(self):
        return f"{self.user.job_number} - {self.tag.name}: {self.mastery_level:.1f}"


class TrainingMaterial(BaseTimestampedModel):
    """培训资料模型（预留扩展）"""
    class MaterialType(models.TextChoices):
        DOCUMENT = 'document', '文档资料'
        VIDEO = 'video', '视频教程'
        EXERCISE = 'exercise', '练习题'
        OTHER = 'other', '其他'

    title = models.CharField(max_length=200, verbose_name='资料标题')
    description = models.TextField(blank=True, verbose_name='资料描述')
    material_type = models.CharField(
        max_length=20,
        choices=MaterialType.choices,
        default=MaterialType.DOCUMENT,
        verbose_name='资料类型'
    )
    url = models.URLField(blank=True, verbose_name='资料链接')
    file_path = models.CharField(max_length=500, blank=True, verbose_name='文件路径')
    tags = models.ManyToManyField(
        Tag,
        related_name='training_materials',
        verbose_name='关联标签',
        blank=True
    )
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_materials',
        verbose_name='创建者',
        default=1  # 默认设置为管理员用户
    )
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    is_public = models.BooleanField(default=True, verbose_name='是否公开')

    class Meta:
        verbose_name = '培训资料'
        verbose_name_plural = '培训资料'
        db_table = 'training_materials'
        ordering = ['-created_at']

    def __str__(self):
        return self.title