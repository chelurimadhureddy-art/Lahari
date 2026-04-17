from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import StudentProfile
from complaints.models import Complaint
from leaves.models import LeaveRequest
from notifications.models import Notification


def ensure_student_profile(user):
    profile, _ = StudentProfile.objects.get_or_create(
        user=user,
        defaults={
            'student_id': f'STD{user.id:05d}',
            'phone': '',
            'address': '',
        },
    )
    return profile


@login_required
def student_dashboard(request):
    if request.user.role != 'student':
        return redirect('login')
    profile = ensure_student_profile(request.user)
    complaints = Complaint.objects.filter(student=request.user).order_by('-created_at')[:5]
    leaves = LeaveRequest.objects.filter(student=request.user).order_by('-created_at')[:5]
    notifications = Notification.objects.all().order_by('-created_at')[:5]
    context = {
        'profile': profile,
        'complaints': complaints,
        'leaves': leaves,
        'notifications': notifications,
        'complaint_count': Complaint.objects.filter(student=request.user).count(),
        'pending_complaint_count': Complaint.objects.filter(student=request.user, status='pending').count(),
        'leave_count': LeaveRequest.objects.filter(student=request.user).count(),
        'pending_leave_count': LeaveRequest.objects.filter(student=request.user, status='pending').count(),
        'notification_count': Notification.objects.count(),
    }
    return render(request, 'student_dashboard.html', context)

@login_required
def student_profile(request):
    if request.user.role != 'student':
        return redirect('login')
    profile = ensure_student_profile(request.user)
    if request.method == 'POST':
        profile.phone = request.POST.get('phone')
        profile.address = request.POST.get('address')
        profile.save()
        messages.success(request, 'Profile updated.')
        return redirect('student_profile')
    return render(request, 'student_profile.html', {'profile': profile})

@login_required
def student_complaints(request):
    if request.user.role != 'student':
        return redirect('login')
    complaints = Complaint.objects.filter(student=request.user).order_by('-created_at')
    return render(request, 'student_complaints.html', {'complaints': complaints})

@login_required
def submit_complaint(request):
    if request.user.role != 'student':
        return redirect('login')
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        Complaint.objects.create(student=request.user, title=title, description=description)
        messages.success(request, 'Complaint submitted.')
        return redirect('student_complaints')
    return render(request, 'submit_complaint.html')

@login_required
def student_leaves(request):
    if request.user.role != 'student':
        return redirect('login')
    leaves = LeaveRequest.objects.filter(student=request.user).order_by('-created_at')
    return render(request, 'student_leaves.html', {'leaves': leaves})

@login_required
def submit_leave(request):
    if request.user.role != 'student':
        return redirect('login')
    if request.method == 'POST':
        from_date = request.POST.get('from_date')
        to_date = request.POST.get('to_date')
        reason = request.POST.get('reason')
        LeaveRequest.objects.create(student=request.user, from_date=from_date, to_date=to_date, reason=reason)
        messages.success(request, 'Leave request submitted.')
        return redirect('student_leaves')
    return render(request, 'submit_leave.html')

@login_required
def student_notifications(request):
    if request.user.role != 'student':
        return redirect('login')
    notifications = Notification.objects.all().order_by('-created_at')
    return render(request, 'student_notifications.html', {'notifications': notifications})
