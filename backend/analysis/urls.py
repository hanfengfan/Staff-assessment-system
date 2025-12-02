from django.urls import path
from . import views

app_name = 'analysis'

urlpatterns = [
    # 能力画像相关
    path('radar/', views.radar_chart_data, name='radar-data'),
    path('capability-profiles/', views.CapabilityProfileListView.as_view(), name='capability-profiles'),
    path('summary/', views.capability_summary, name='capability-summary'),
    path('trend/', views.trend_data, name='trend-data'),
    path('recommendations/', views.weak_tag_recommendations, name='weak-recommendations'),

    # 培训资料相关
    path('materials/', views.TrainingMaterialListView.as_view(), name='training-materials'),
    path('materials/create/', views.create_training_material, name='create-training-material'),
]