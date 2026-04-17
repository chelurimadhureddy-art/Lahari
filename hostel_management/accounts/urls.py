from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('staff/login/', views.staff_login_view, name='staff_login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('warden/dashboard/', views.warden_dashboard, name='warden_dashboard'),
    path('admin/students/', views.admin_students, name='admin_students'),
    path('admin/students/add/', views.add_student, name='add_student'),
    path('admin/students/<int:student_id>/edit/', views.edit_student, name='edit_student'),
    path('admin/students/<int:student_id>/delete/', views.delete_student, name='delete_student'),
    path('admin/students/<int:student_id>/assign_room/', views.assign_room, name='assign_room'),
    path('admin/complaints/', views.admin_complaints, name='admin_complaints'),
    path('admin/complaints/<int:complaint_id>/update/', views.update_complaint_status, name='update_complaint_status'),
    path('admin/leaves/', views.admin_leaves, name='admin_leaves'),
    path('admin/leaves/<int:leave_id>/update/', views.update_leave_status, name='update_leave_status'),
    path('admin/rooms/', views.admin_rooms, name='admin_rooms'),
    path('admin/rooms/add/', views.add_room, name='add_room'),
    path('admin/notifications/', views.admin_notifications, name='admin_notifications'),
    path('admin/notifications/add/', views.add_notification, name='add_notification'),
]
