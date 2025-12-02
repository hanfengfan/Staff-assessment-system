from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # 题目相关
    path('questions/', views.QuestionListView.as_view(), name='question-list'),
    path('questions/<int:pk>/', views.QuestionDetailView.as_view(), name='question-detail'),

    # 试卷相关
    path('exam/', views.ExamPaperListView.as_view(), name='exam-list'),
    path('exam/<int:pk>/', views.ExamPaperDetailView.as_view(), name='exam-detail'),
    path('exam/generate/', views.generate_exam, name='exam-generate'),
    path('exam/<int:paper_id>/start/', views.start_exam, name='exam-start'),
    path('exam/<int:paper_id>/submit/', views.submit_exam, name='exam-submit'),
]