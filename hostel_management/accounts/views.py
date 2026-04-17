from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError, transaction
from django.db.models import Q
from rooms.models import Room
from complaints.models import Complaint
from leaves.models import LeaveRequest
from notifications.models import Notification
from students.models import StudentProfile

User = get_user_model()


def recalculate_room_slots(room):
    if room is None:
        return
    assigned_count = StudentProfile.objects.filter(room=room).count()
    room.available_slots = max(room.capacity - assigned_count, 0)
    room.save(update_fields=['available_slots'])


def assign_student_room(profile, new_room):
    previous_room = profile.room
    profile.room = new_room
    profile.save(update_fields=['room'])
    if previous_room and previous_room != new_room:
        recalculate_room_slots(previous_room)
    recalculate_room_slots(new_room)


def is_management_user(user):
    return getattr(user, 'role', None) in {'admin', 'warden'}


def home_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')

def handle_login_request(request, template_name, allowed_roles=None):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        login_input = request.POST.get('username', '').strip()
        password = request.POST.get('password')

        matched_user = User.objects.filter(
            Q(username__iexact=login_input) | Q(email__iexact=login_input)
        ).first()
        username = matched_user.username if matched_user else login_input
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if allowed_roles and user.role not in allowed_roles:
                role_label = 'staff' if set(allowed_roles) == {'admin', 'warden'} else 'student'
                messages.error(request, f'This login page is only for {role_label} accounts.')
                return render(request, template_name)
            login(request, user)
            return redirect('dashboard')
        else:
            if matched_user is None:
                messages.error(request, 'Account not found. Please use your registered username or email.')
            else:
                messages.error(request, 'Incorrect password. Please try again.')
    return render(request, template_name)


def login_view(request):
    return handle_login_request(request, 'login.html', allowed_roles={'student'})


def staff_login_view(request):
    return handle_login_request(request, 'staff_login.html', allowed_roles={'admin', 'warden'})

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        student_id = request.POST.get('student_id', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()

        if not all([username, password, email, first_name, last_name, student_id, phone, address]):
            messages.error(request, 'Please fill in all fields.')
            return render(request, 'register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return render(request, 'register.html')

        if StudentProfile.objects.filter(student_id=student_id).exists():
            messages.error(request, 'Student ID already exists.')
            return render(request, 'register.html')

        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username,
                    password=password,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    role='student',
                )
                StudentProfile.objects.create(
                    user=user,
                    student_id=student_id,
                    phone=phone,
                    address=address,
                )
        except IntegrityError:
            messages.error(request, 'Unable to create your account right now. Please try again.')
            return render(request, 'register.html')

        messages.success(request, 'Registration successful. Please log in.')
        return redirect('login')

    return render(request, 'register.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    if request.user.role == 'admin':
        return redirect('admin_dashboard')
    if request.user.role == 'warden':
        return redirect('warden_dashboard')
    else:
        return redirect('student_dashboard')

@login_required
def admin_dashboard(request):
    if request.user.role != 'admin':
        return redirect('login')
    return management_dashboard(request, 'admin')


@login_required
def warden_dashboard(request):
    if request.user.role != 'warden':
        return redirect('login')
    return management_dashboard(request, 'warden')


def management_dashboard(request, role_name):
    students = User.objects.filter(role='student').select_related('studentprofile')
    complaints = Complaint.objects.filter(status='pending')
    leaves = LeaveRequest.objects.filter(status='pending')
    rooms = Room.objects.all()
    notifications = Notification.objects.all().order_by('-created_at')[:5]
    assigned_students = StudentProfile.objects.filter(room__isnull=False).count()
    unassigned_students = StudentProfile.objects.filter(room__isnull=True).count()
    context = {
        'dashboard_role': role_name.title(),
        'students': students,
        'complaints': complaints,
        'leaves': leaves,
        'rooms': rooms,
        'notifications': notifications,
        'student_count': students.count(),
        'pending_complaint_count': complaints.count(),
        'pending_leave_count': leaves.count(),
        'room_count': rooms.count(),
        'open_room_count': rooms.filter(available_slots__gt=0).count(),
        'assigned_students': assigned_students,
        'unassigned_students': unassigned_students,
    }
    return render(request, 'admin_dashboard.html', context)

@login_required
def admin_students(request):
    if not is_management_user(request.user):
        return redirect('login')
    students = User.objects.filter(role='student')
    return render(request, 'admin_students.html', {'students': students})

@login_required
def add_student(request):
    if not is_management_user(request.user):
        return redirect('login')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        student_id = request.POST.get('student_id', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()

        if not all([username, password, email, first_name, last_name, student_id]):
            messages.error(request, 'Please fill in all required student details.')
            return render(request, 'add_student.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'add_student.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return render(request, 'add_student.html')

        if StudentProfile.objects.filter(student_id=student_id).exists():
            messages.error(request, 'Student ID already exists.')
            return render(request, 'add_student.html')

        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role='student',
        )
        StudentProfile.objects.create(user=user, student_id=student_id, phone=phone, address=address)
        messages.success(request, 'Student added.')
        return redirect('admin_students')
    return render(request, 'add_student.html')


@login_required
def edit_student(request, student_id):
    if not is_management_user(request.user):
        return redirect('login')

    student = get_object_or_404(User, id=student_id, role='student')
    profile = get_object_or_404(StudentProfile, user=student)

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        student_id_value = request.POST.get('student_id', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        password = request.POST.get('password', '')

        if not all([username, email, first_name, last_name, student_id_value]):
            messages.error(request, 'Please fill in all required student details.')
            return render(request, 'edit_student.html', {'student_obj': student, 'profile': profile})

        if User.objects.exclude(id=student.id).filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'edit_student.html', {'student_obj': student, 'profile': profile})

        if User.objects.exclude(id=student.id).filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return render(request, 'edit_student.html', {'student_obj': student, 'profile': profile})

        if StudentProfile.objects.exclude(id=profile.id).filter(student_id=student_id_value).exists():
            messages.error(request, 'Student ID already exists.')
            return render(request, 'edit_student.html', {'student_obj': student, 'profile': profile})

        student.username = username
        student.email = email
        student.first_name = first_name
        student.last_name = last_name
        if password:
            student.set_password(password)
        student.save()

        profile.student_id = student_id_value
        profile.phone = phone
        profile.address = address
        profile.save()

        messages.success(request, 'Student updated.')
        return redirect('admin_students')

    return render(request, 'edit_student.html', {'student_obj': student, 'profile': profile})


@login_required
def delete_student(request, student_id):
    if not is_management_user(request.user):
        return redirect('login')

    student = get_object_or_404(User, id=student_id, role='student')
    profile = get_object_or_404(StudentProfile, user=student)

    if request.method == 'POST':
        previous_room = profile.room
        student.delete()
        recalculate_room_slots(previous_room)
        messages.success(request, 'Student deleted.')
        return redirect('admin_students')

    return render(request, 'delete_student.html', {'student_obj': student, 'profile': profile})

@login_required
def assign_room(request, student_id):
    if not is_management_user(request.user):
        return redirect('login')
    student = get_object_or_404(User, id=student_id, role='student')
    profile = get_object_or_404(StudentProfile, user=student)
    if request.method == 'POST':
        room_id = request.POST.get('room')
        room = get_object_or_404(Room, id=room_id)
        if profile.room == room:
            messages.info(request, 'Student is already assigned to this room.')
        elif room.available_slots > 0:
            assign_student_room(profile, room)
            messages.success(request, 'Room assigned.')
        else:
            messages.error(request, 'No available slots.')
        return redirect('admin_students')
    rooms = Room.objects.filter(Q(available_slots__gt=0) | Q(id=profile.room_id)).distinct()
    return render(request, 'assign_room.html', {'student': student, 'profile': profile, 'rooms': rooms})

@login_required
def admin_complaints(request):
    if not is_management_user(request.user):
        return redirect('login')
    complaints = Complaint.objects.all().order_by('-created_at')
    return render(request, 'admin_complaints.html', {'complaints': complaints})

@login_required
def update_complaint_status(request, complaint_id):
    if not is_management_user(request.user):
        return redirect('login')
    complaint = get_object_or_404(Complaint, id=complaint_id)
    if request.method == 'POST':
        status = request.POST.get('status')
        complaint.status = status
        complaint.save()
        messages.success(request, 'Status updated.')
        return redirect('admin_complaints')
    return render(request, 'update_complaint.html', {'complaint': complaint})

@login_required
def admin_leaves(request):
    if not is_management_user(request.user):
        return redirect('login')
    leaves = LeaveRequest.objects.all().order_by('-created_at')
    return render(request, 'admin_leaves.html', {'leaves': leaves})

@login_required
def update_leave_status(request, leave_id):
    if not is_management_user(request.user):
        return redirect('login')
    leave = get_object_or_404(LeaveRequest, id=leave_id)
    if request.method == 'POST':
        status = request.POST.get('status')
        leave.status = status
        leave.save()
        messages.success(request, 'Status updated.')
        return redirect('admin_leaves')
    return render(request, 'update_leave.html', {'leave': leave})

@login_required
def admin_rooms(request):
    if not is_management_user(request.user):
        return redirect('login')
    rooms = Room.objects.all()
    return render(request, 'admin_rooms.html', {'rooms': rooms})

@login_required
def add_room(request):
    if not is_management_user(request.user):
        return redirect('login')
    if request.method == 'POST':
        room_number = request.POST.get('room_number', '').strip()
        capacity_raw = request.POST.get('capacity', '').strip()

        if not room_number or not capacity_raw:
            messages.error(request, 'Please enter both room number and capacity.')
            return render(request, 'add_room.html')

        try:
            capacity = int(capacity_raw)
        except ValueError:
            messages.error(request, 'Capacity must be a valid number.')
            return render(request, 'add_room.html')

        if capacity <= 0:
            messages.error(request, 'Capacity must be greater than zero.')
            return render(request, 'add_room.html')

        if Room.objects.filter(room_number__iexact=room_number).exists():
            messages.error(request, f'Room {room_number} already exists.')
            return render(request, 'add_room.html')

        Room.objects.create(room_number=room_number, capacity=capacity, available_slots=capacity)
        messages.success(request, 'Room added.')
        return redirect('admin_rooms')
    return render(request, 'add_room.html')

@login_required
def admin_notifications(request):
    if not is_management_user(request.user):
        return redirect('login')
    notifications = Notification.objects.all().order_by('-created_at')
    return render(request, 'admin_notifications.html', {'notifications': notifications})

@login_required
def add_notification(request):
    if not is_management_user(request.user):
        return redirect('login')
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        Notification.objects.create(title=title, content=content, posted_by=request.user)
        messages.success(request, 'Notification posted.')
        return redirect('admin_notifications')
    return render(request, 'add_notification.html')
