from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('profile/', views.student_profile, name='student_profile'),
    path('complaints/', views.student_complaints, name='student_complaints'),
    path('complaints/submit/', views.submit_complaint, name='submit_complaint'),
    path('leaves/', views.student_leaves, name='student_leaves'),
    path('leaves/submit/', views.submit_leave, name='submit_leave'),
    path('notifications/', views.student_notifications, name='student_notifications'),
]