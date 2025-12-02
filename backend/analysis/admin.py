from django.contrib import admin
from .models import CapabilityProfile, TrainingMaterial


@admin.register(CapabilityProfile)
class CapabilityProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'tag', 'mastery_level', 'created_at', 'updated_at')
    list_filter = ('tag', 'mastery_level', 'created_at')
    search_fields = ('user__job_number', 'user__username', 'tag__name')
    readonly_fields = ('created_at', 'updated_at')

    def get_readonly_fields(self, request, obj=None):
        # 对于已存在的对象，不允许直接修改掌握度（应该通过考试自动更新）
        if obj:
            return ('user', 'tag', 'created_at', 'updated_at')
        return super().get_readonly_fields(request, obj)


@admin.register(TrainingMaterial)
class TrainingMaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'material_type', 'is_active', 'created_at')
    list_filter = ('material_type', 'is_active', 'tags', 'created_at')
    search_fields = ('title', 'description')
    filter_horizontal = ('tags',)
    readonly_fields = ('created_at', 'updated_at')