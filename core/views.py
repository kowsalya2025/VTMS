from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.db import DatabaseError, IntegrityError
from django.db.models import Q
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .models import User, Trainer, Course, Batch, Trainee, Intern, BusinessTeam, Payment, Report, Enquiry, Candidate, Eligibility, DocumentVerification, InterviewSchedule, SystemSetting, Task, TraineeTask, Project, Message, ContactQuery, Leave, Attendance
from django.utils import timezone
from datetime import timedelta, datetime, date
import calendar as cal_module
import json
from functools import wraps

# ─── Role Guards ────────────────────────────────────────────────────────────────

def login_required_role(*roles):
    """Decorator: requires user to be logged in and have one of the given roles."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'Please log in to continue.')
                return redirect('login')
            if request.user.role not in roles:
                messages.error(request, 'You do not have permission to access that page.')
                # Send back to their own dashboard
                if request.user.role == User.Role.ADMIN:
                    return redirect('admin_dashboard')
                if request.user.role == User.Role.TRAINER:
                    return redirect('trainer_dashboard')
                if request.user.role == User.Role.BUSINESS_TEAM:
                    return redirect('business_dashboard')
                return redirect('login')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

ADMIN = User.Role.ADMIN
TRAINER = User.Role.TRAINER
BUSINESS = User.Role.BUSINESS_TEAM

def login_view(request):
    # Clear any existing messages to avoid showing old ones on login page
    storage = messages.get_messages(request)
    for _ in storage:
        pass  # Consume all messages
    
    if request.user.is_authenticated:
        # Already logged in — send to correct dashboard
        if request.user.role == User.Role.ADMIN:
            return redirect('admin_dashboard')
        if request.user.role == User.Role.TRAINER:
            return redirect('trainer_dashboard')
        if request.user.role == User.Role.BUSINESS_TEAM:
            return redirect('business_dashboard')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        role = request.POST.get('role', '').strip()

        if not email or not password or not role:
            messages.error(request, 'Please fill in email, password, and role.')
            return render(request, 'core/login.html')

        user = authenticate(request, email=email, password=password)

        if user is None:
            messages.error(request, 'Invalid email or password.')
            return render(request, 'core/login.html')

        if user.role != role:
            messages.error(request, 'Selected role does not match this account.')
            return render(request, 'core/login.html')

        login(request, user)

        if role == User.Role.ADMIN:
            return redirect('admin_dashboard')
        if role == User.Role.TRAINER:
            return redirect('trainer_dashboard')
        if role == User.Role.BUSINESS_TEAM:
            return redirect('business_dashboard')

        messages.error(request, 'This role does not have a dashboard.')
        return render(request, 'core/login.html')

    return render(request, 'core/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required_role(ADMIN)
def admin_redirect_view(request):
    return redirect('admin_dashboard')

@login_required_role(ADMIN)
def admin_dashboard(request):
    total_trainers = Trainer.objects.filter(status='Active').count()
    total_trainees = Trainee.objects.filter(status='Active').count()
    active_batches = Batch.objects.filter(status='Active')
    active_batches_count = active_batches.count()
    pending_reports = Report.objects.filter(status='Pending').count()

    daily_pending  = Report.objects.filter(status='Pending', report_type='Daily').count()
    weekly_pending = Report.objects.filter(status='Pending', report_type='Weekly').count()
    monthly_pending= Report.objects.filter(status='Pending', report_type='Monthly').count()

    # Recent trainees (last 5)
    recent_trainees = Trainee.objects.select_related('course').order_by('-id')[:5]
    # Recent payments
    recent_payments = Payment.objects.select_related('trainee').order_by('-date')[:5]
    # Unread contact queries
    unread_queries = ContactQuery.objects.filter(is_read=False).order_by('-created_at')
    unread_queries_count = unread_queries.count()
    # Recent queries (last 5)
    recent_queries = ContactQuery.objects.order_by('-created_at')[:5]

    context = {
        'total_trainers': total_trainers,
        'total_trainees': total_trainees,
        'active_batches_count': active_batches_count,
        'pending_reports': pending_reports,
        'active_batches': active_batches,
        'daily_pending': daily_pending,
        'weekly_pending': weekly_pending,
        'monthly_pending': monthly_pending,
        'recent_trainees': recent_trainees,
        'recent_payments': recent_payments,
        'unread_queries': unread_queries,
        'unread_queries_count': unread_queries_count,
        'recent_queries': recent_queries,
    }
    return render(request, 'core/dashboard.html', context)

@login_required_role(TRAINER)
def trainer_dashboard(request):
    trainer = Trainer.objects.filter(user=request.user).first()

    assigned_batches = Batch.objects.filter(trainer=trainer).count() if trainer else 0
    total_trainees = Trainee.objects.filter(batch__trainer=trainer).count() if trainer else 0
    pending_reports = Report.objects.filter(status='Pending', trainer=trainer).count() if trainer else 0
    active_batches = Batch.objects.filter(trainer=trainer, status='Active') if trainer else Batch.objects.none()

    total_interns = Intern.objects.count()
    active_interns = Intern.objects.filter(status='Active').count()
    completed_interns = Intern.objects.filter(status='Completed').count()

    # Pending report counts by type
    daily_pending = Report.objects.filter(status='Pending', report_type='Daily', trainer=trainer).count() if trainer else 0
    weekly_pending = Report.objects.filter(status='Pending', report_type='Weekly', trainer=trainer).count() if trainer else 0
    monthly_pending = Report.objects.filter(status='Pending', report_type='Monthly', trainer=trainer).count() if trainer else 0

    context = {
        'trainer': trainer,
        'assigned_batches': assigned_batches,
        'total_trainees': total_trainees,
        'pending_reports': pending_reports,
        'active_batches': active_batches,
        'total_interns': total_interns,
        'active_interns': active_interns,
        'completed_interns': completed_interns,
        'daily_pending': daily_pending,
        'weekly_pending': weekly_pending,
        'monthly_pending': monthly_pending,
    }
    return render(request, 'core/trainer_dashboard.html', context)

@login_required_role(BUSINESS)
def business_dashboard(request):
    # Check if we need to create sample data
    if Enquiry.objects.count() == 0:
        # Create sample courses
        sample_courses = ['UI/UX Design', 'Web Development', 'Python Batch', 'React Batch']
        for course_name in sample_courses:
            Course.objects.get_or_create(title=course_name, defaults={'status': 'Active'})
        
        # Create sample enquiries
        sample_enquiries = [
            {'full_name': 'Anith', 'email': 'anith@test.com', 'phone': '9876543210'},
            {'full_name': 'Rahul', 'email': 'rahul@test.com', 'phone': '9876543211'},
            {'full_name': 'Kiran', 'email': 'kiran@test.com', 'phone': '9876543212'},
        ]
        for i, enquiry in enumerate(sample_enquiries):
            Enquiry.objects.create(
                full_name=enquiry['full_name'],
                email=enquiry['email'],
                phone=enquiry['phone'],
                status='New',
            )
    
    # Get stats
    total_enquiries = Enquiry.objects.count()
    eligible_candidates = Candidate.objects.count()  # Use Candidates as Eligible
    payments_completed = Payment.objects.filter(status='Paid').count()
    active_batches = Batch.objects.filter(status='Active').count()
    
    # If still 0, use sample numbers
    if total_enquiries == 0:
        total_enquiries = 120
    if eligible_candidates == 0:
        eligible_candidates = 86
    if payments_completed == 0:
        payments_completed = 60
    if active_batches == 0:
        active_batches = 25
    
    # Recent enquiries
    recent_enquiries = Enquiry.objects.all().order_by('-created_at')[:3]
    
    # Pending actions
    eligibility_pending = Eligibility.objects.filter(status='Pending').count()
    document_pending = DocumentVerification.objects.filter(status='Pending').count()
    payment_pending = Payment.objects.filter(status='Pending').count()
    
    # Sample if 0
    if eligibility_pending == 0:
        eligibility_pending = 10
    if document_pending == 0:
        document_pending = 5
    if payment_pending == 0:
        payment_pending = 8
    
    context = {
        'total_enquiries': total_enquiries,
        'eligible_candidates': eligible_candidates,
        'payments_completed': payments_completed,
        'active_batches': active_batches,
        'recent_enquiries': recent_enquiries,
        'eligibility_pending': eligibility_pending,
        'document_pending': document_pending,
        'payment_pending': payment_pending,
    }
    return render(request, 'core/business_dashboard.html', context)

# Trainer Management
@login_required_role(ADMIN)
def trainer_list(request):
    trainers = Trainer.objects.all()
    courses = Course.objects.all()
    return render(request, 'core/trainer_list.html', {'trainers': trainers, 'courses': courses})

@login_required_role(ADMIN)
def trainer_add(request):
    if request.method == 'POST':
        office_mail = request.POST.get('office_mail', '').strip()
        personal_mail = request.POST.get('personal_mail', '').strip()
        phone_no = request.POST.get('phone_no', '').strip()
        password = request.POST.get('password', '').strip()
        try:
            validate_email(office_mail)
            validate_email(personal_mail)
        except ValidationError:
            messages.error(request, 'Please enter valid email addresses.')
            courses = Course.objects.all()
            return render(request, 'core/trainer_list.html', {'trainers': Trainer.objects.all(), 'courses': courses})
        if not phone_no.isdigit() or not (10 <= len(phone_no) <= 15):
            messages.error(request, 'Please enter a valid phone number (10-15 digits).')
            courses = Course.objects.all()
            return render(request, 'core/trainer_list.html', {'trainers': Trainer.objects.all(), 'courses': courses})
        if User.objects.filter(email=office_mail).exists():
            messages.error(request, 'A user with this office email already exists.')
            courses = Course.objects.all()
            return render(request, 'core/trainer_list.html', {'trainers': Trainer.objects.all(), 'courses': courses})
        # If no password is provided, use phone number as default
        if not password:
            password = phone_no
        # Create user first
        user = User.objects.create_user(
            email=request.POST['office_mail'],
            password=password,
            role=User.Role.TRAINER,
            phone_no=request.POST['phone_no'],
        )
        # Create trainer
        trainer = Trainer.objects.create(
            user=user,
            full_name=request.POST['full_name'],
            office_mail=request.POST['office_mail'],
            personal_mail=request.POST['personal_mail'],
            phone_no=request.POST['phone_no'],
            gender=request.POST['gender'],
            status=request.POST['status']
        )
        if request.POST.get('course'):
            trainer.course = Course.objects.get(id=request.POST['course'])
        if request.FILES.get('profile_image'):
            trainer.profile_image = request.FILES['profile_image']
        trainer.save()
        messages.success(request, 'New Trainer Added Successfully.')
        return redirect('trainer_list')
    
    courses = Course.objects.all()
    return render(request, 'core/trainer_list.html', {'trainers': Trainer.objects.all(), 'courses': courses})

@login_required_role(ADMIN)
def trainer_edit(request, pk):
    trainer = get_object_or_404(Trainer, pk=pk)
    if request.method == 'POST':
        trainer.full_name = request.POST['full_name']
        trainer.office_mail = request.POST['office_mail']
        trainer.personal_mail = request.POST['personal_mail']
        trainer.phone_no = request.POST['phone_no']
        trainer.gender = request.POST['gender']
        trainer.status = request.POST['status']
        if request.POST.get('course'):
            trainer.course = Course.objects.get(id=request.POST['course'])
        if request.FILES.get('profile_image'):
            trainer.profile_image = request.FILES['profile_image']
        trainer.user.email = request.POST['office_mail']
        trainer.user.phone_no = request.POST['phone_no']
        # Update password if provided
        new_password = request.POST.get('password', '').strip()
        if new_password:
            trainer.user.set_password(new_password)
        trainer.user.save()
        trainer.save()
        messages.success(request, 'Trainer Updated Successfully')
        return redirect('trainer_list')
    
    courses = Course.objects.all()
    return render(request, 'core/trainer_list.html', {'trainers': Trainer.objects.all(), 'courses': courses})

@login_required_role(ADMIN)
def trainer_delete(request, pk):
    trainer = get_object_or_404(Trainer, pk=pk)
    trainer.user.delete()  # Delete the associated user too
    messages.success(request, 'Trainer Deleted Successfully')
    return redirect('trainer_list')

# Business Team Management
@login_required_role(ADMIN)
def business_team_list(request):
    business_team = BusinessTeam.objects.all()
    return render(request, 'core/business_team_list.html', {'business_team': business_team})

@login_required_role(ADMIN)
def business_team_add(request):
    if request.method == 'POST':
        office_mail = request.POST.get('office_mail', '').strip()
        personal_mail = request.POST.get('personal_mail', '').strip()
        phone_no = request.POST.get('phone_no', '').strip()
        password = request.POST.get('password', '').strip()
        try:
            validate_email(office_mail)
            validate_email(personal_mail)
        except ValidationError:
            messages.error(request, 'Please enter valid email addresses.')
            return render(request, 'core/business_team_list.html', {'business_team': BusinessTeam.objects.all()})
        if not phone_no.isdigit() or not (10 <= len(phone_no) <= 15):
            messages.error(request, 'Please enter a valid phone number (10-15 digits).')
            return render(request, 'core/business_team_list.html', {'business_team': BusinessTeam.objects.all()})
        if User.objects.filter(email=office_mail).exists():
            messages.error(request, 'A user with this office email already exists.')
            return render(request, 'core/business_team_list.html', {'business_team': BusinessTeam.objects.all()})
        # If no password provided, use phone number as default
        if not password:
            password = phone_no
        # Create user first
        user = User.objects.create_user(
            email=request.POST['office_mail'],
            password=password,
            role=User.Role.BUSINESS_TEAM,
            phone_no=request.POST['phone_no'],
        )
        # Create business team member
        business_team_member = BusinessTeam.objects.create(
            user=user,
            full_name=request.POST['full_name'],
            office_mail=request.POST['office_mail'],
            personal_mail=request.POST['personal_mail'],
            phone_no=request.POST['phone_no'],
            gender=request.POST['gender'],
            status=request.POST['status']
        )
        if request.FILES.get('profile_image'):
            business_team_member.profile_image = request.FILES['profile_image']
        business_team_member.save()
        messages.success(request, 'New Business Team Member Added Successfully.')
        return redirect('business_team_list')
    
    return render(request, 'core/business_team_list.html', {'business_team': BusinessTeam.objects.all()})

@login_required_role(ADMIN)
def business_team_edit(request, pk):
    business_team_member = get_object_or_404(BusinessTeam, pk=pk)
    if request.method == 'POST':
        business_team_member.full_name = request.POST['full_name']
        business_team_member.office_mail = request.POST['office_mail']
        business_team_member.personal_mail = request.POST['personal_mail']
        business_team_member.phone_no = request.POST['phone_no']
        business_team_member.gender = request.POST['gender']
        business_team_member.status = request.POST['status']
        if request.FILES.get('profile_image'):
            business_team_member.profile_image = request.FILES['profile_image']
        business_team_member.user.email = request.POST['office_mail']
        business_team_member.user.phone_no = request.POST['phone_no']
        # Update password if provided
        new_password = request.POST.get('password', '').strip()
        if new_password:
            business_team_member.user.set_password(new_password)
        business_team_member.user.save()
        business_team_member.save()
        messages.success(request, 'Business Team Member Updated Successfully')
        return redirect('business_team_list')
    
    return render(request, 'core/business_team_list.html', {'business_team': BusinessTeam.objects.all()})

@login_required_role(ADMIN)
def business_team_delete(request, pk):
    business_team_member = get_object_or_404(BusinessTeam, pk=pk)
    business_team_member.user.delete()  # Delete the associated user too
    messages.success(request, 'Business Team Member Deleted Successfully')
    return redirect('business_team_list')

# Batch Management
@login_required_role(ADMIN)
def batch_list(request):
    batches = Batch.objects.all()
    return render(request, 'core/batch_list.html', {'batches': batches})

@login_required_role(ADMIN)
def batch_add(request):
    if request.method == 'POST':
        batch_name = request.POST['batch_name']
        course_id = request.POST['course']
        trainer_id = request.POST['trainer']
        description = request.POST['description']
        start_date = request.POST['start_date']
        end_date = request.POST['end_date']
        duration = request.POST['duration']
        timing_start = request.POST['timing_start']
        timing_end = request.POST['timing_end']
        days = ','.join(request.POST.getlist('days'))
        status = request.POST['status']
        selected_trainee_ids = request.POST.getlist('trainees')
        email_from = request.POST.get('email_from', 'admin@vetritsystems.com')
        email_to = request.POST.get('email_to', '')
        email_subject = request.POST.get('email_subject', '')
        email_preview = request.POST.get('email_preview', '')
        
        course = Course.objects.get(id=course_id) if course_id else None
        trainer = Trainer.objects.get(id=trainer_id) if trainer_id else None
        
        batch = Batch.objects.create(
            batch_name=batch_name,
            course=course,
            trainer=trainer,
            description=description,
            start_date=start_date,
            end_date=end_date,
            duration=duration,
            timing_start=timing_start,
            timing_end=timing_end,
            days=days,
            status=status
        )
        
        if request.FILES.get('batch_file'):
            batch.batch_file = request.FILES['batch_file']
            batch.save()

        if selected_trainee_ids:
            Trainee.objects.filter(id__in=selected_trainee_ids).update(batch=batch)
        
        # Send email notification to assigned trainer
        if trainer and trainer.office_mail:
            try:
                subject = email_subject or f'New Batch: {batch_name}'
                body = email_preview or (
                    f'Dear {trainer.full_name},\n\n'
                    f'A new batch "{batch_name}" has been assigned to you.\n\n'
                    f'Start Date: {start_date}\n'
                    f'End Date: {end_date}\n\n'
                    f'Please review the batch details in VTMS.\n\n'
                    f'Best regards,\nAdmin'
                )
                email = EmailMessage(
                    subject=subject,
                    body=body,
                    from_email=email_from,
                    to=[trainer.office_mail],
                )
                if batch.batch_file:
                    email.attach_file(batch.batch_file.path)
                email.send(fail_silently=False)
                messages.success(request, 'New Batch Added Successfully and Email Sent!')
            except Exception:
                messages.warning(request, 'New Batch Added Successfully, but Email Failed to Send.')
        else:
            messages.success(request, 'New Batch Added Successfully')
        
        return redirect('batch_list')
    
    courses = Course.objects.all()
    trainers = Trainer.objects.filter(status='Active')
    trainees = Trainee.objects.filter(status='Active')
    return render(request, 'core/batch_form.html', {
        'courses': courses,
        'trainers': trainers,
        'trainees': trainees,
        'selected_days': [],
        'selected_trainees': [],
        'batch': None,
        'days_list': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    })

@login_required_role(ADMIN)
def batch_edit(request, pk):
    batch = get_object_or_404(Batch, pk=pk)
    if request.method == 'POST':
        batch.batch_name = request.POST['batch_name']
        course_id = request.POST['course']
        trainer_id = request.POST['trainer']
        batch.description = request.POST['description']
        batch.start_date = request.POST['start_date']
        batch.end_date = request.POST['end_date']
        batch.duration = request.POST['duration']
        batch.timing_start = request.POST['timing_start']
        batch.timing_end = request.POST['timing_end']
        batch.days = ','.join(request.POST.getlist('days'))
        batch.status = request.POST['status']
        selected_trainee_ids = request.POST.getlist('trainees')
        email_from = request.POST.get('email_from', 'admin@vetritsystems.com')
        email_to = request.POST.get('email_to', '')
        email_subject = request.POST.get('email_subject', '')
        email_preview = request.POST.get('email_preview', '')
        
        if course_id:
            batch.course = Course.objects.get(id=course_id)
        else:
            batch.course = None
            
        if trainer_id:
            batch.trainer = Trainer.objects.get(id=trainer_id)
        else:
            batch.trainer = None
            
        if request.FILES.get('batch_file'):
            batch.batch_file = request.FILES['batch_file']
            
        batch.save()

        if selected_trainee_ids:
            Trainee.objects.filter(batch=batch).exclude(id__in=selected_trainee_ids).update(batch=None)
            Trainee.objects.filter(id__in=selected_trainee_ids).update(batch=batch)
        else:
            Trainee.objects.filter(batch=batch).update(batch=None)
        
        # Send email notification to assigned trainer
        if batch.trainer and batch.trainer.office_mail:
            try:
                subject = email_subject or f'Batch Updated: {batch.batch_name}'
                body = email_preview or (
                    f'Dear {batch.trainer.full_name},\n\n'
                    f'Batch "{batch.batch_name}" has been updated.\n\n'
                    f'Please review the latest details in VTMS.\n\n'
                    f'Best regards,\nAdmin'
                )
                email = EmailMessage(
                    subject=subject,
                    body=body,
                    from_email=email_from,
                    to=[batch.trainer.office_mail],
                )
                if batch.batch_file:
                    email.attach_file(batch.batch_file.path)
                email.send(fail_silently=True)
                messages.success(request, 'Batch Updated Successfully and Email Sent!')
            except Exception:
                messages.warning(request, 'Batch Updated Successfully, but Email Failed to Send.')
        else:
            messages.success(request, 'Batch Updated Successfully')
        
        return redirect('batch_list')
    
    courses = Course.objects.all()
    trainers = Trainer.objects.filter(status='Active')
    trainees = Trainee.objects.filter(status='Active')
    selected_days = batch.days.split(',') if batch.days else []
    selected_trainees = list(batch.trainees.values_list('id', flat=True))
    return render(request, 'core/batch_form.html', {
        'batch': batch,
        'courses': courses,
        'trainers': trainers,
        'trainees': trainees,
        'selected_days': selected_days,
        'selected_trainees': selected_trainees,
        'days_list': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    })

@login_required_role(ADMIN)
def batch_delete(request, pk):
    batch = get_object_or_404(Batch, pk=pk)
    batch.delete()
    messages.success(request, 'Batch Deleted Successfully')
    return redirect('batch_list')

# Admin - Trainee List
@login_required_role(ADMIN)
def trainee_list(request):
    trainees = Trainee.objects.all()
    return render(request, 'core/trainee_list.html', {'trainees': trainees})

# Admin - Trainee Add
@login_required_role(ADMIN)
def trainee_add(request):
    if request.method == 'POST':
        password = request.POST.get('password', '').strip()
        if not password:
            password = request.POST['phone_no']
        # Create user
        user = User.objects.create_user(
            email=request.POST['personal_mail'],
            password=password,
            role=User.Role.TRAINEE,
            phone_no=request.POST['phone_no'],
        )
        # Create trainee
        trainee = Trainee.objects.create(
            user=user,
            full_name=request.POST['full_name'],
            personal_mail=request.POST['personal_mail'],
            phone_no=request.POST['phone_no'],
            gender=request.POST['gender'],
            date_of_birth=request.POST['date_of_birth'],
            address=request.POST['address'],
            guardian_name=request.POST['guardian_name'],
            guardian_phone=request.POST['guardian_phone'],
            status=request.POST['status'],
            progress=0
        )
        if request.POST.get('course'):
            trainee.course = Course.objects.get(id=request.POST['course'])
        if request.POST.get('batch'):
            trainee.batch = Batch.objects.get(id=request.POST['batch'])
        if request.POST.get('trainer'):
            trainee.trainer = Trainer.objects.get(id=request.POST['trainer'])
        trainee.save()

        messages.success(request, 'Trainee added successfully!')
        return redirect('trainee_list')
    courses = Course.objects.all()
    batches = Batch.objects.all()
    trainers = Trainer.objects.filter(status='Active')
    return render(request, 'core/trainee_form.html', {'courses': courses, 'batches': batches, 'trainers': trainers, 'trainee': None})

# Admin - Trainee Detail
@login_required_role(ADMIN)
def trainee_detail(request, pk):
    trainee = get_object_or_404(Trainee, pk=pk)
    return render(request, 'core/trainee_detail.html', {'trainee': trainee})

# Admin - Trainee Edit
@login_required_role(ADMIN)
def trainee_edit(request, pk):
    trainee = get_object_or_404(Trainee, pk=pk)
    if request.method == 'POST':
        trainee.full_name = request.POST['full_name']
        trainee.personal_mail = request.POST['personal_mail']
        trainee.phone_no = request.POST['phone_no']
        trainee.gender = request.POST['gender']
        trainee.date_of_birth = request.POST['date_of_birth']
        trainee.address = request.POST['address']
        trainee.guardian_name = request.POST['guardian_name']
        trainee.guardian_phone = request.POST['guardian_phone']
        trainee.status = request.POST['status']
        trainee.progress = int(request.POST.get('progress', 0))
        
        if request.POST.get('course'):
            trainee.course = Course.objects.get(id=request.POST['course'])
        if request.POST.get('batch'):
            trainee.batch = Batch.objects.get(id=request.POST['batch'])
        if request.POST.get('trainer'):
            trainee.trainer = Trainer.objects.get(id=request.POST['trainer'])
        
        trainee.user.email = request.POST['personal_mail']
        trainee.user.phone_no = request.POST['phone_no']
        # Update password if provided
        new_password = request.POST.get('password', '').strip()
        if new_password:
            trainee.user.set_password(new_password)
        trainee.user.save()
        trainee.save()
        messages.success(request, 'Trainee updated successfully!')
        return redirect('trainee_list')
    
    courses = Course.objects.all()
    batches = Batch.objects.all()
    trainers = Trainer.objects.filter(status='Active')
    return render(request, 'core/trainee_form.html', {'trainee': trainee, 'courses': courses, 'batches': batches, 'trainers': trainers})

# Admin - Trainee Delete
@login_required_role(ADMIN)
def trainee_delete(request, pk):
    trainee = get_object_or_404(Trainee, pk=pk)
    trainee.user.delete()
    messages.success(request, 'Trainee deleted successfully!')
    return redirect('trainee_list')

# Intern Management
@login_required_role(ADMIN)
def intern_list(request):
    interns = Intern.objects.all()
    return render(request, 'core/intern_list.html', {'interns': interns})

# Admin - Intern Add
@login_required_role(ADMIN)
def intern_add(request):
    trainers = Trainer.objects.filter(status='Active')
    if request.method == 'POST':
        personal_mail = request.POST.get('personal_mail', '').strip()
        phone_no = request.POST.get('phone_no', '').strip()
        password = request.POST.get('password', '').strip()
        try:
            validate_email(personal_mail)
        except ValidationError:
            messages.error(request, 'Please enter a valid email address.')
            return render(request, 'core/intern_form.html', {'trainers': trainers, 'intern': None})
        if not phone_no.isdigit() or not (10 <= len(phone_no) <= 15):
            messages.error(request, 'Please enter a valid phone number (10-15 digits).')
            return render(request, 'core/intern_form.html', {'trainers': trainers, 'intern': None})
        if User.objects.filter(email=personal_mail).exists():
            messages.error(request, 'A user with this email already exists.')
            return render(request, 'core/intern_form.html', {'trainers': trainers, 'intern': None})
        if not password:
            password = phone_no
        try:
            user = User.objects.create_user(
                email=personal_mail,
                password=password,
                role=User.Role.INTERN,
                phone_no=phone_no,
            )
            intern = Intern.objects.create(
                user=user,
                full_name=request.POST['full_name'],
                personal_mail=personal_mail,
                phone_no=phone_no,
                gender=request.POST['gender'],
                role=request.POST['role'],
                internship_period=request.POST['internship_period'],
                status=request.POST['status'],
                join_date=request.POST.get('join_date') or None,
                overall_status=request.POST.get('overall_status', 'Good Performance'),
                trainer_remarks=request.POST.get('trainer_remarks', '')
            )
            if request.POST.get('trainer'):
                intern.trainer = Trainer.objects.get(id=request.POST['trainer'])
            intern.save()
        except (IntegrityError, ValidationError, KeyError):
            messages.error(request, 'Failed to create intern. Please check all fields and try again.')
            return render(request, 'core/intern_form.html', {'trainers': trainers, 'intern': None})
        
        # Send email notification to assigned trainer
        email_from = request.POST.get('email_from', 'admin@vetritsystems.com')
        email_subject = request.POST.get('email_subject', '') or f'New Intern Assigned: {intern.full_name}'
        email_preview = request.POST.get('email_preview', '') or (
            f'Dear Trainer,\n\nA new intern "{intern.full_name}" has been assigned to you.\n\n'
            f'Role: {intern.role}\n'
            f'Internship Period: {intern.internship_period}\n\n'
            f'Best regards,\nAdmin'
        )
        if intern.trainer and intern.trainer.office_mail:
            try:
                email = EmailMessage(
                    subject=email_subject,
                    body=email_preview,
                    from_email=email_from,
                    to=[intern.trainer.office_mail],
                )
                email.send(fail_silently=True)
                messages.success(request, 'Intern added successfully and trainer notified!')
            except Exception:
                messages.warning(request, 'Intern added successfully, but trainer notification failed.')
        else:
            messages.success(request, 'Intern added successfully!')
        
        return redirect('intern_list')
    return render(request, 'core/intern_form.html', {'trainers': trainers, 'intern': None})

# Admin - Intern Detail
@login_required_role(ADMIN)
def intern_detail(request, pk):
    intern = get_object_or_404(Intern, pk=pk)
    return render(request, 'core/intern_detail.html', {'intern': intern})

# Admin - Intern Edit
@login_required_role(ADMIN)
def intern_edit(request, pk):
    intern = get_object_or_404(Intern, pk=pk)
    if request.method == 'POST':
        intern.full_name = request.POST['full_name']
        intern.personal_mail = request.POST['personal_mail']
        intern.phone_no = request.POST['phone_no']
        intern.gender = request.POST['gender']
        intern.role = request.POST['role']
        intern.internship_period = request.POST['internship_period']
        intern.status = request.POST['status']
        intern.join_date = request.POST.get('join_date') or None
        intern.overall_status = request.POST.get('overall_status', 'Good Performance')
        intern.trainer_remarks = request.POST.get('trainer_remarks', '')
        if request.POST.get('trainer'):
            intern.trainer = Trainer.objects.get(id=request.POST['trainer'])
        intern.user.email = request.POST['personal_mail']
        intern.user.phone_no = request.POST['phone_no']
        new_password = request.POST.get('password', '').strip()
        if new_password:
            intern.user.set_password(new_password)
        intern.user.save()
        intern.save()
        
        # Send email
        email_from = request.POST.get('email_from', 'admin@vetritsystems.com')
        email_to = request.POST.get('email_to', '')
        email_subject = request.POST.get('email_subject', '')
        email_preview = request.POST.get('email_preview', '')
        
        if email_to and email_subject:
            try:
                recipient_list = [email_to]
                if intern.trainer and intern.trainer.office_mail:
                    recipient_list = [intern.trainer.office_mail]
                
                send_mail(
                    subject=email_subject,
                    message=email_preview,
                    from_email=email_from,
                    recipient_list=recipient_list,
                    fail_silently=True,
                )
                messages.success(request, 'Intern updated successfully and Email Sent!')
            except Exception as e:
                messages.warning(request, 'Intern updated successfully, but Email Failed to Send.')
        else:
            messages.success(request, 'Intern updated successfully!')
        
        return redirect('intern_list')
    trainers = Trainer.objects.filter(status='Active')
    return render(request, 'core/intern_form.html', {'intern': intern, 'trainers': trainers})

# Admin - Intern Delete
def intern_delete(request, pk):
    intern = get_object_or_404(Intern, pk=pk)
    intern.user.delete()
    messages.success(request, 'Intern deleted successfully!')
    return redirect('intern_list')

# Admin - Intern Performance
def intern_performance(request, pk):
    intern = get_object_or_404(Intern, pk=pk)
    
    # Get Attendance data
    attendance_records = Attendance.objects.filter(intern=intern)
    total_days = attendance_records.count()
    present_days = attendance_records.filter(status='Present').count()
    absent_days = total_days - present_days
    attendance_percent = 0
    attendance_circle_offset = 408.4
    if total_days > 0:
        attendance_percent = int((present_days / total_days) * 100)
        attendance_circle_offset = 408.4 * (1 - (attendance_percent / 100))
    
    # Get Project data
    projects = Project.objects.filter(intern=intern)
    total_projects = projects.count()
    completed_projects = projects.filter(status='Completed').count()
    pending_projects = total_projects - completed_projects
    completion_percent = 0
    if total_projects > 0:
        completion_percent = int((completed_projects / total_projects) * 100)
    
    return render(request, 'core/intern_performance.html', {
        'intern': intern,
        'total_days': total_days,
        'present_days': present_days,
        'absent_days': absent_days,
        'attendance_percent': attendance_percent,
        'attendance_circle_offset': attendance_circle_offset,
        'total_projects': total_projects,
        'completed_projects': completed_projects,
        'pending_projects': pending_projects,
        'completion_percent': completion_percent,
    })

# Reports & Approvals
def reports_approvals(request):
    return render(request, 'core/reports_approvals.html')

# Business Monitoring
@login_required_role(BUSINESS)
def business_monitoring(request):
    total_enquiries = Enquiry.objects.count()
    eligible_candidates = Eligibility.objects.filter(status='Eligible').count()
    converted_count = Enquiry.objects.filter(status='Converted').count()
    conversion_rate = 0
    if total_enquiries > 0:
        conversion_rate = round((converted_count / total_enquiries) * 100, 1)
    
    return render(request, 'core/business_monitoring.html', {
        'total_enquiries': total_enquiries,
        'eligible_candidates': eligible_candidates,
        'conversion_rate': conversion_rate
    })

# Payment & Revenue
def payment_revenue(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        trainee_id = request.POST.get('trainee_id')
        trainee = Trainee.objects.get(id=trainee_id)
        
        if action == 'mark_installment':
            trainee.first_installment_paid = True
            trainee.save()
        elif action == 'create_office_email':
            office_email = request.POST.get('office_email')
            trainee.office_mail = office_email
            trainee.save()
    
    payments = Payment.objects.all()
    
    # Calculate stats
    total_revenue = 0
    total_collected = 0
    total_pending = 0
    pending_payments_count = 0
    
    for payment in payments:
        total_revenue += payment.course_amount
        total_collected += payment.paid
        total_pending += payment.pending
        if payment.status == 'Pending':
            pending_payments_count += 1
    
    return render(request, 'core/payment_revenue.html', {
        'payments': payments,
        'total_revenue': total_revenue,
        'total_collected': total_collected,
        'total_pending': total_pending,
        'pending_payments_count': pending_payments_count
    })

# Communication
@login_required_role(ADMIN, TRAINER, BUSINESS)
def communication(request):
    search_query = request.GET.get('q', '')
    active_filter = request.GET.get('filter', 'all')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'toggle_read':
            msg = get_object_or_404(Message, id=request.POST.get('msg_id'))
            msg.is_read = not msg.is_read
            msg.save()
        elif action == 'send':
                recipient_id = request.POST.get('recipient')
                subject = request.POST.get('subject', '').strip()
                body = request.POST.get('body', '').strip()
                if recipient_id and subject and body:
                    recipient = get_object_or_404(User, id=recipient_id)
                    # Send email using configured SMTP
                    from_email = settings.DEFAULT_FROM_EMAIL
                    try:
                        email_msg = EmailMessage(
                            subject=subject,
                            body=body,
                            from_email=from_email,
                            to=[recipient.email],
                        )
                        email_msg.send(fail_silently=False)
                        messages.success(request, 'Email sent successfully!')
                    except Exception as e:
                        messages.error(request, f'Failed to send email: {str(e)}')
                    # Record the communication in the internal Message model
                    Message.objects.create(
                        sender=request.user,
                        recipient=recipient,
                        subject=subject,
                        preview=body[:200],
                        is_read=False,
                        avatar_initial=subject[0].upper() if subject else 'M',
                    )
                else:
                    messages.error(request, 'Please fill in recipient, subject, and message.')
        return redirect('communication')

    msgs = Message.objects.all().select_related('sender', 'recipient').order_by('-created_at')

    if active_filter == 'unread':
        msgs = msgs.filter(is_read=False, recipient=request.user)
    elif active_filter == 'sent':
        msgs = msgs.filter(sender=request.user)
    if search_query:
        msgs = msgs.filter(Q(subject__icontains=search_query) | Q(preview__icontains=search_query))

    users = User.objects.exclude(id=request.user.id).order_by('email')
    return render(request, 'core/communication.html', {
        'messages_list': msgs,
        'search_query': search_query,
        'active_filter': active_filter,
        'users': users,
    })


# Business Communication
@login_required_role(ADMIN, BUSINESS)
def business_communication(request):
    active_tab = request.GET.get('tab', 'email')  # Default to email tab
    
    if request.method == 'POST':
        # Get active tab from form hidden field
        active_tab = request.POST.get('active_tab', 'email')
        
        if active_tab == 'email':
            # Email submission
                        # Determine recipient: either a predefined user or a custom address
            to_option = request.POST.get('to')
            if to_option == 'custom':
                # User entered a custom email address
                to_email = request.POST.get('to_custom', '').strip()
            else:
                # Use the selected predefined email option (trim whitespace)
                to_email = to_option.strip() if to_option else ''
            # Fallback to default from address if empty (should not happen for valid forms)
            if not to_email:
                to_email = settings.DEFAULT_FROM_EMAIL
            # Strip whitespace and ensure a value exists
            if not to_email:
                messages.error(request, 'Please provide a valid recipient email.')
                return redirect(f'{reverse("business_communication")}?tab=email')
            # Optional: validate email format
            try:
                validate_email(to_email)
            except ValidationError:
                messages.error(request, 'Invalid email address format.')
                return redirect(f'{reverse("business_communication")}?tab=email')
            subject = request.POST.get('subject')
            body = request.POST.get('body')
            # Use logged-in user's email as "From" address
            from_email = settings.DEFAULT_FROM_EMAIL
            
            try:
                from django.core.mail import EmailMessage
                email = EmailMessage(
                    subject=subject,
                    body=body,
                    from_email=from_email,
                    to=[to_email],
                )
                
                # Handle attachments
                if request.FILES:
                    for file in request.FILES.getlist('attachments'):
                        email.attach(file.name, file.read(), file.content_type)
                
                email.send(fail_silently=False)
                messages.success(request, 'Email sent successfully!')
            except Exception as e:
                messages.error(request, f'Failed to send email: {str(e)}')
        
        elif active_tab == 'whatsapp':
            # WhatsApp submission (placeholder - you'll need an actual WhatsApp API)
            phone = request.POST.get('phone') or request.POST.get('phone_custom')
            message = request.POST.get('message')
            messages.info(request, 'WhatsApp feature requires API integration. Message saved for now.')
        
        # Redirect with the active tab
        return redirect(f'{reverse("business_communication")}?tab={active_tab}')
    
    # Get data
    trainees = Trainee.objects.all()
    interns = Intern.objects.all()
    return render(request, 'core/business_communication.html', {
        'active_tab': active_tab,
        'user': request.user,
        'trainees': trainees,
        'interns': interns,
    })

# Settings
def system_settings(request):
    # Get or create the first SystemSetting
    setting, created = SystemSetting.objects.get_or_create(id=1)
    
    if request.method == 'POST':
        # Update General
        setting.organizer_name = request.POST.get('organizer_name', setting.organizer_name)
        # Update SMTP
        setting.smtp_email = request.POST.get('smtp_email', setting.smtp_email)
        setting.smtp_host = request.POST.get('smtp_host', setting.smtp_host)
        setting.smtp_port = request.POST.get('smtp_port', setting.smtp_port)
        setting.smtp_user = request.POST.get('smtp_user', setting.smtp_user)
        setting.smtp_password = request.POST.get('smtp_password', setting.smtp_password)
        # Update WhatsApp
        setting.whatsapp_number = request.POST.get('whatsapp_number', setting.whatsapp_number)
        # Update Notifications
        setting.enable_email_notification = request.POST.get('enable_email_notification') == 'on'
        setting.enable_whatsapp_alerts = request.POST.get('enable_whatsapp_alerts') == 'on'
        # Update Backup
        setting.backup_frequency = request.POST.get('backup_frequency', setting.backup_frequency)
        
        # Update Permissions
        setting.admin_edit_batch = request.POST.get('admin_edit_batch') == 'on'
        setting.admin_batch_course_control = request.POST.get('admin_batch_course_control') == 'on'
        setting.admin_reports_approval = request.POST.get('admin_reports_approval') == 'on'
        setting.admin_payment_verification = request.POST.get('admin_payment_verification') == 'on'
        
        setting.trainer_attendance_update = request.POST.get('trainer_attendance_update') == 'on'
        setting.trainer_task_project_update = request.POST.get('trainer_task_project_update') == 'on'
        setting.trainer_report_submission = request.POST.get('trainer_report_submission') == 'on'
        
        setting.business_enquiry_check = request.POST.get('business_enquiry_check') == 'on'
        setting.business_document_verification = request.POST.get('business_document_verification') == 'on'
        setting.business_payment_handling = request.POST.get('business_payment_handling') == 'on'
        setting.business_batch_allocation = request.POST.get('business_batch_allocation') == 'on'
        setting.business_reports_approval = request.POST.get('business_reports_approval') == 'on'
        
        setting.save()
        messages.success(request, 'Settings updated successfully!')
        return redirect('settings')
    
    return render(request, 'core/settings.html', {'setting': setting})

# Admin - Invoice
def invoice(request):
    payments = Payment.objects.all()
    return render(request, 'core/invoice.html', {'payments': payments})

# Admin - Calendar & Leave
@login_required_role(ADMIN)
def calendar_leave(request):
    batches = Batch.objects.all()
    batch_id = request.GET.get('batch') or request.POST.get('batch_id')
    selected_batch = None
    if batch_id:
        selected_batch = Batch.objects.filter(id=batch_id).first()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_leave':
            batch = get_object_or_404(Batch, id=request.POST.get('batch_id'))
            leave_date = datetime.strptime(request.POST.get('leave_date'), '%Y-%m-%d').date()
            reason = request.POST.get('reason', '').strip() or 'Leave'
            day_name = leave_date.strftime('%A')
            Leave.objects.create(batch=batch, date=leave_date, day=day_name, reason=reason)
            messages.success(request, f'Leave added for {batch.batch_name} on {leave_date.strftime("%d/%m/%Y")}.')
        elif action == 'generate_schedule':
            batch = get_object_or_404(Batch, id=request.POST.get('batch_id'))
            if batch.start_date and batch.end_date:
                current = batch.start_date
                created_count = 0
                while current <= batch.end_date:
                    if current.weekday() >= 5:
                        day_name = current.strftime('%A')
                        _, was_created = Leave.objects.get_or_create(
                            batch=batch, date=current,
                            defaults={'day': day_name, 'reason': 'Weekend / Non-working day'}
                        )
                        if was_created:
                            created_count += 1
                    current += timedelta(days=1)
                messages.success(request, f'Schedule generated: {created_count} leave day(s) added for {batch.batch_name}.')
            else:
                messages.error(request, 'Batch must have start and end dates to generate a schedule.')
        elif action == 'delete_leave':
            leave = get_object_or_404(Leave, id=request.POST.get('leave_id'))
            leave.delete()
            messages.success(request, 'Leave entry removed.')
        redirect_url = reverse('calendar_leave') + f'?year={request.POST.get("year", timezone.now().year)}'
        if batch_id:
            redirect_url += f'&batch={batch_id}'
        return redirect(redirect_url)

    try:
        year = int(request.GET.get('year', timezone.now().year))
    except (TypeError, ValueError):
        year = timezone.now().year

    leaves_qs = Leave.objects.select_related('batch').filter(date__year=year)
    if selected_batch:
        leaves_qs = leaves_qs.filter(batch=selected_batch)

    leave_dates = [l.date.isoformat() for l in leaves_qs]
    batch_dates = []
    for b in batches:
        if b.start_date and b.end_date:
            current = b.start_date
            while current <= b.end_date and current.year == year:
                if current.weekday() < 5:
                    batch_dates.append(current.isoformat())
                current += timedelta(days=1)

    return render(request, 'core/calendar_leave.html', {
        'batches': batches,
        'leaves': leaves_qs.order_by('-date'),
        'leave_dates_json': json.dumps(leave_dates),
        'batch_dates_json': json.dumps(batch_dates),
        'year': year,
        'selected_batch': selected_batch,
        'month_names': list(cal_module.month_name)[1:],
    })

# Trainer - Profile
@login_required_role(TRAINER)
def trainer_profile(request):
    trainer = Trainer.objects.filter(user=request.user).first()
    if request.method == 'POST':
        if trainer:
            trainer.full_name = request.POST.get('full_name', trainer.full_name)
            trainer.office_mail = request.POST.get('office_mail', trainer.office_mail)
            trainer.personal_mail = request.POST.get('personal_mail', trainer.personal_mail)
            trainer.phone_no = request.POST.get('phone_no', trainer.phone_no)
            trainer.gender = request.POST.get('gender', trainer.gender)
            trainer.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('trainer_profile')
    return render(request, 'core/trainer_profile.html', {'trainer': trainer, 'user': request.user})

# Trainer - Batches
@login_required_role(TRAINER)
def trainer_batch_list(request):
    trainer = Trainer.objects.filter(user=request.user).first()
    batches = Batch.objects.filter(trainer=trainer) if trainer else Batch.objects.all()
    return render(request, 'core/trainer_batch_list.html', {'batches': batches})

# Trainer - Trainees
@login_required_role(TRAINER)
def trainer_trainee_list(request):
    trainer = Trainer.objects.filter(user=request.user).first()
    trainees = Trainee.objects.filter(trainer=trainer) if trainer else Trainee.objects.all()
    return render(request, 'core/trainer_trainee_list.html', {'trainees': trainees})

# Trainer - Tasks
@login_required_role(TRAINER)
def trainer_tasks(request):
    trainer = Trainer.objects.filter(user=request.user).first()  # Current trainer
    active_tab = request.GET.get('tab', 'tasks')
    
    tasks = []
    projects = []
    selected_task = None
    trainee_tasks = []

    if trainer:
        tasks = Task.objects.filter(trainer=trainer)
        projects = Project.objects.filter(trainer=trainer)

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_trainee_task':
            trainee_task_id = request.POST.get('trainee_task_id')
            trainee_task = get_object_or_404(TraineeTask, id=trainee_task_id)
            
            status = request.POST.get('status')
            completed_task = int(request.POST.get('completed_task', 0))
            submission_date = request.POST.get('submission_date', None)
            is_checked = request.POST.get('is_checked') == 'on'
            
            trainee_task.status = status
            trainee_task.completed_task = completed_task
            if submission_date:
                trainee_task.submission_date = submission_date
            trainee_task.is_checked = is_checked
            trainee_task.save()
            
            messages.success(request, 'Task updated successfully!')
            
            return redirect(f'/trainer/tasks/?tab=trainees&task_id={trainee_task.task.id}')
        
        elif action == 'toggle_check':
            trainee_task_id = request.POST.get('trainee_task_id')
            trainee_task = get_object_or_404(TraineeTask, id=trainee_task_id)
            trainee_task.is_checked = not trainee_task.is_checked
            trainee_task.save()
            
            return redirect(f'/trainer/tasks/?tab=trainees&task_id={trainee_task.task.id}')
    
    task_id = request.GET.get('task_id')
    if task_id:
        selected_task = get_object_or_404(Task, id=task_id)
        # Get all trainees for the task's batch
        if selected_task.batch:
            trainees = selected_task.batch.trainees.all()
            # Create TraineeTask records if they don't exist yet
            for trainee in trainees:
                TraineeTask.objects.get_or_create(
                    task=selected_task,
                    trainee=trainee,
                    defaults={
                        'total_task': selected_task.total_task,
                        'completed_task': 0,
                        'status': 'Incomplete',
                        'is_checked': False
                    }
                )
            trainee_tasks = TraineeTask.objects.filter(task=selected_task)
    
    context = {
        'active_tab': active_tab,
        'tasks': tasks,
        'projects': projects,
        'selected_task': selected_task,
        'trainee_tasks': trainee_tasks,
    }
    return render(request, 'core/trainer_tasks.html', context)


# Trainer - Internship Management (Active Interns List)
@login_required_role(TRAINER)
def trainer_internship_management(request):
    trainer = Trainer.objects.filter(user=request.user).first()
    interns = Intern.objects.filter(trainer=trainer) if trainer else Intern.objects.all()
    return render(request, 'core/trainer_internship_management.html', {'interns': interns})


# Trainer - Assign Work Page
@login_required_role(TRAINER)
def trainer_assign_work(request):
    intern_id = request.GET.get('intern_id')
    intern = None
    if intern_id:
        intern = get_object_or_404(Intern, id=intern_id)
    return render(request, 'core/trainer_assign_work.html', {'intern': intern})


# Trainer - Intern Performance Page
@login_required_role(TRAINER)
def trainer_intern_performance(request, intern_id):
    intern = get_object_or_404(Intern, id=intern_id)
    return render(request, 'core/trainer_intern_performance.html', {'intern': intern})


# Trainer - Communication Page
@login_required_role(TRAINER)
def trainer_communication(request):
    active_tab = request.GET.get('tab', 'email')  # Default to email tab
    
    if request.method == 'POST':
        # Get active tab from form hidden field
        active_tab = request.POST.get('active_tab', 'email')
        
        if active_tab == 'email':
            # Email submission
            to_email = request.POST.get('to') or request.POST.get('to_custom')
            subject = request.POST.get('subject')
            body = request.POST.get('body')
            # Use logged-in user's email as "From" address
            from_email = request.user.email
            
            try:
                from django.core.mail import EmailMessage
                email = EmailMessage(
                    subject=subject,
                    body=body,
                    from_email=from_email,
                    to=[to_email],
                )
                
                # Handle attachments
                if request.FILES:
                    for file in request.FILES.getlist('attachments'):
                        email.attach(file.name, file.read(), file.content_type)
                
                email.send(fail_silently=False)
                messages.success(request, 'Email sent successfully!')
            except Exception as e:
                messages.error(request, f'Failed to send email: {str(e)}')
        
        elif active_tab == 'whatsapp':
            # WhatsApp submission (placeholder - you'll need an actual WhatsApp API)
            phone = request.POST.get('phone') or request.POST.get('phone_custom')
            message = request.POST.get('message')
            messages.info(request, 'WhatsApp feature requires API integration. Message saved for now.')
        
        # Redirect with the active tab
        return redirect(f'{reverse("trainer_communication")}?tab={active_tab}')
    
    # Get data
    trainees = Trainee.objects.all()
    interns = Intern.objects.all()
    
    return render(request, 'core/trainer_communication.html', {
        'active_tab': active_tab,
        'user': request.user,
        'trainees': trainees,
        'interns': interns
    })

# Trainer - Projects
@login_required_role(TRAINER)
def trainer_projects(request):
    trainer = Trainer.objects.filter(user=request.user).first()
    projects = Project.objects.filter(trainer=trainer) if trainer else Project.objects.all()
    return render(request, 'core/trainer_projects.html', {'projects': projects})

# Trainer - Daily Reports
@login_required_role(TRAINER)
def trainer_daily_reports(request):
    trainer = Trainer.objects.filter(user=request.user).first()
    reports = Report.objects.filter(report_type='Daily', trainer=trainer).order_by('-date') if trainer else Report.objects.filter(report_type='Daily').order_by('-date')
    return render(request, 'core/trainer_daily_reports.html', {'reports': reports})

# Trainer - Weekly Reports
@login_required_role(TRAINER)
def trainer_weekly_reports(request):
    trainer = Trainer.objects.filter(user=request.user).first()
    reports = Report.objects.filter(report_type='Weekly', trainer=trainer).order_by('-date') if trainer else Report.objects.filter(report_type='Weekly').order_by('-date')
    return render(request, 'core/trainer_weekly_reports.html', {'reports': reports})

# Trainer - Monthly Reports
@login_required_role(TRAINER)
def trainer_monthly_reports(request):
    trainer = Trainer.objects.filter(user=request.user).first()
    reports = Report.objects.filter(report_type='Monthly', trainer=trainer).order_by('-date') if trainer else Report.objects.filter(report_type='Monthly').order_by('-date')
    return render(request, 'core/trainer_monthly_reports.html', {'reports': reports})

# Trainer - Attendance
@login_required_role(TRAINER)
def trainer_attendance(request):
    trainer = Trainer.objects.filter(user=request.user).first()
    from core.models import Attendance
    attendance_records = Attendance.objects.filter(batch__trainer=trainer).order_by('-date') if trainer else Attendance.objects.order_by('-date')
    return render(request, 'core/trainer_attendance.html', {'attendance_records': attendance_records, 'trainer': trainer})

# Trainer - Calendar
@login_required_role(TRAINER)
def trainer_calendar(request):
    trainer = Trainer.objects.filter(user=request.user).first()
    batches = Batch.objects.filter(trainer=trainer) if trainer else Batch.objects.all()
    return render(request, 'core/trainer_calendar.html', {'batches': batches})

# Business Team - Enquiry Management
@login_required_role(BUSINESS)
def enquiry_management(request):
    # Create sample data if needed
    if Enquiry.objects.count() == 0:
        courses = Course.objects.all()
        if courses.count() == 0:
            c1 = Course.objects.create(title="UI/UX Design", status="Active")
            c2 = Course.objects.create(title="Web Development", status="Active")
            c3 = Course.objects.create(title="Python Programming", status="Active")
            c4 = Course.objects.create(title="Full Stack Development", status="Active")
            courses = [c1, c2, c3, c4]
        
        sample_enquiries = [
            {"name": "Meena", "email": "meena245@gmail.com", "phone": "9867897610", "course": courses[0], "age": 25, "qualification": "Bsc", "status": "New", "gender": "Female", "address": "23/8, New Bustand, Tenkasi"},
            {"name": "Rahul", "email": "rahul4@gmail.com", "phone": "9867897611", "course": courses[1], "age": 30, "qualification": "B.com", "status": "Contacted", "gender": "Male", "address": "12/5, Main Road, Tenkasi"},
            {"name": "Pratheepa", "email": "pratheepa2@gmail.com", "phone": "9867897612", "course": courses[2], "age": 25, "qualification": "BE", "status": "Interested", "gender": "Female", "address": "45/2, North Street, Tenkasi"},
            {"name": "Lakshmi", "email": "mlakshmi@gmail.com", "phone": "9867897613", "course": courses[3], "age": 28, "qualification": "BA English", "status": "Converted", "gender": "Female", "address": "67/3, South Street, Tenkasi"},
        ]
        
        for sample in sample_enquiries:
            Enquiry.objects.create(
                full_name=sample['name'],
                email=sample['email'],
                phone=sample['phone'],
                course_interested=sample['course'],
                status=sample['status'],
                age=sample['age'],
                qualification=sample['qualification'],
                gender=sample['gender'],
                address=sample['address']
            )
    
    enquiries = Enquiry.objects.all()
    
    # Handle view
    view_mode = request.GET.get('view', 'list')
    selected_enquiry = None
    if view_mode == 'detail' and 'enquiry_id' in request.GET:
        selected_enquiry = get_object_or_404(Enquiry, id=request.GET.get('enquiry_id'))
    
    if request.method == 'POST':
        action = request.POST.get('action')
        enquiry_id = request.POST.get('enquiry_id')
        enquiry = get_object_or_404(Enquiry, id=enquiry_id)
        
        if action == 'update_status':
            new_status = request.POST.get('status')
            enquiry.status = new_status
            enquiry.save()
            messages.success(request, 'Enquiry status updated successfully!')
        elif action == 'update_enquiry':
            # Update enquiry details
            enquiry.full_name = request.POST.get('full_name', enquiry.full_name)
            enquiry.email = request.POST.get('email', enquiry.email)
            enquiry.phone = request.POST.get('phone', enquiry.phone)
            enquiry.age = request.POST.get('age', enquiry.age)
            enquiry.gender = request.POST.get('gender', enquiry.gender)
            enquiry.qualification = request.POST.get('qualification', enquiry.qualification)
            enquiry.address = request.POST.get('address', enquiry.address)
            enquiry.status = request.POST.get('status', enquiry.status)
            
            course_id = request.POST.get('course')
            if course_id:
                enquiry.course_interested = Course.objects.get(id=course_id)
            
            enquiry.save()
            messages.success(request, 'Enquiry updated successfully!')
    
    return render(request, 'core/enquiry_management.html', {
        'enquiries': enquiries, 
        'view_mode': view_mode, 
        'selected_enquiry': selected_enquiry,
        'courses': Course.objects.all()
    })

# Business Team - Candidate Management
@login_required_role(BUSINESS)
def candidate_management(request):
    candidates = Candidate.objects.all()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        candidate_id = request.POST.get('candidate_id')
        
        if action == 'update_payment_status':
            candidate = get_object_or_404(Candidate, id=candidate_id)
            candidate.payment_status = request.POST.get('payment_status')
            candidate.save()
            messages.success(request, 'Payment status updated successfully!')
    
    return render(request, 'core/candidate_management.html', {'candidates': candidates})

# Business Team - Document Verification
@login_required_role(BUSINESS)
def document_verification(request):
    documents = DocumentVerification.objects.all()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        doc_id = request.POST.get('doc_id')
        document = get_object_or_404(DocumentVerification, id=doc_id)
        
        if action == 'verify':
            document.status = 'Verified'
            document.verification_date = timezone.now().date()
            document.save()
            messages.success(request, 'Document verified successfully!')
        elif action == 'reject':
            document.status = 'Rejected'
            document.save()
            messages.success(request, 'Document rejected!')
    
    return render(request, 'core/document_verification.html', {'documents': documents})

@login_required_role(BUSINESS)
def document_verification_detail(request, candidate_id):
    candidate = get_object_or_404(Candidate, id=candidate_id)
    documents = DocumentVerification.objects.filter(candidate=candidate)

    if request.method == 'POST':
        action = request.POST.get('action')
        doc_id = request.POST.get('doc_id')
        document = get_object_or_404(DocumentVerification, id=doc_id)

        if action == 'verify':
            document.status = 'Verified'
            document.verification_date = timezone.now().date()
            document.verified_by = request.user if request.user.is_authenticated else None
            document.save()
            messages.success(request, 'Document verified successfully!')
            return redirect('document_verification_detail', candidate_id=candidate_id)
        elif action == 'reject':
            document.status = 'Rejected'
            document.remarks = request.POST.get('remarks', '')
            document.save()
            messages.success(request, 'Document rejected!')
            return redirect('document_verification_detail', candidate_id=candidate_id)

    return render(request, 'core/document_verification_detail.html', {
        'candidate': candidate,
        'documents': documents
    })

# Business Team - Payment Management
@login_required_role(BUSINESS)
def business_payment_management(request):
    import json
    from django.core.serializers.json import DjangoJSONEncoder
    # Ensure trainees have payment records so the business payment page always shows new trainee rows
    for trainee in Trainee.objects.filter(payment__isnull=True):
        course_amount = getattr(trainee.course, 'fees', 0) if trainee.course else 0
        Payment.objects.create(
            trainee=trainee,
            course_amount=course_amount,
            paid=0,
            pending=course_amount,
            status='Pending',
            plan='One-time',
            payment_method='UPI',
            due_date=timezone.now().date() + timedelta(days=30)
        )

    payments = Payment.objects.select_related('trainee', 'intern', 'trainee__course').all()
    
    # Handle search
    search_query = request.GET.get('search', '')
    if search_query:
        payments = payments.filter(
            trainee__full_name__icontains=search_query
        ) | payments.filter(
            intern__full_name__icontains=search_query
        )
    
    # Handle status filter
    status_filter = request.GET.get('status', '')
    if status_filter:
        payments = payments.filter(status=status_filter)
    
    # Calculate statistics
    total_revenue = sum(p.course_amount for p in payments)
    total_collected = sum(p.paid for p in payments)
    total_pending = sum(p.pending for p in payments)
    pending_count = payments.filter(status='Pending').count()

    # Prepare payments json
    payments_list = []
    for payment in payments:
        payment_dict = {
            'id': payment.id,
            'course_amount': payment.course_amount,
            'paid': payment.paid,
            'pending': payment.pending,
            'status': payment.status,
            'plan': payment.plan,
            'payment_method': payment.payment_method,
            'date': payment.date.isoformat() if payment.date else None,
            'due_date': payment.due_date.isoformat() if payment.due_date else None,
        }
        if payment.trainee:
            payment_dict['trainee'] = {
                'full_name': payment.trainee.full_name,
                'personal_mail': payment.trainee.personal_mail,
                'phone_no': payment.trainee.phone_no,
                'gender': payment.trainee.gender,
                'date_of_birth': payment.trainee.date_of_birth.isoformat() if payment.trainee.date_of_birth else None,
                'address': payment.trainee.address,
            }
            if payment.trainee.course:
                payment_dict['trainee']['course'] = {'title': payment.trainee.course.title}
        else:
            payment_dict['trainee'] = None
        
        if payment.intern:
            payment_dict['intern'] = {
                'full_name': payment.intern.full_name,
                'personal_email': payment.intern.personal_email,
                'phone_no': payment.intern.phone_no,
                'role': payment.intern.role,
            }
        else:
            payment_dict['intern'] = None
        payments_list.append(payment_dict)

    payments_json = json.dumps(payments_list, cls=DjangoJSONEncoder)
    
    return render(request, 'core/business_payment_management.html', {
        'payments': payments,
        'payments_json': payments_json,
        'total_revenue': total_revenue,
        'total_collected': total_collected,
        'total_pending': total_pending,
        'pending_count': pending_count,
        'search_query': search_query,
        'status_filter': status_filter,
    })

# Update Payment
def update_payment(request):
    if request.method == 'POST':
        payment_id = request.POST.get('payment_id')
        payment = get_object_or_404(Payment, id=payment_id)
        
        if request.POST.get('course_amount'):
            payment.course_amount = float(request.POST.get('course_amount'))
        payment.plan = request.POST.get('plan', payment.plan)
        payment.payment_method = request.POST.get('payment_method', payment.payment_method)
        
        if request.POST.get('paid'):
            payment.paid = float(request.POST.get('paid'))
            payment.pending = payment.course_amount - payment.paid
        
        if request.POST.get('date'):
            from datetime import datetime
            payment.date = datetime.strptime(request.POST.get('date'), '%Y-%m-%d').date()
        
        if request.POST.get('due_date'):
            from datetime import datetime
            payment.due_date = datetime.strptime(request.POST.get('due_date'), '%Y-%m-%d').date()
        
        payment.status = request.POST.get('status', payment.status)
        payment.save()
        messages.success(request, 'Payment updated successfully!')
    return redirect('business_payment_management')

# Send Payment Email
def send_payment_email(request):
    if request.method == 'POST':
        payment_id = request.POST.get('payment_id')
        payment = get_object_or_404(Payment, id=payment_id)
        to_email = request.POST.get('to_email')
        subject = request.POST.get('subject', 'Payment Request')
        message = request.POST.get('message')
        
        # Get system settings
        setting, _ = SystemSetting.objects.get_or_create(id=1)
        from_email = setting.smtp_email or getattr(settings, 'DEFAULT_FROM_EMAIL', 'webmaster@localhost')
        
        try:
            from django.core.mail import send_mail
            send_mail(
                subject,
                message,
                from_email,
                [to_email],
                fail_silently=False,
            )
            messages.success(request, 'Email sent successfully!')
        except Exception as e:
            messages.error(request, f'Failed to send email: {e}')
    
    return redirect('business_payment_management')

# Download Invoice
@login_required_role(ADMIN, BUSINESS)
def download_invoice(request, payment_id):
    from django.http import HttpResponse
    from django.template.loader import get_template
    from xhtml2pdf import pisa
    from io import BytesIO
    
    payment = get_object_or_404(Payment, id=payment_id)
    
    template_path = 'core/invoice_pdf.html'
    context = {'payment': payment}
    
    # Create a Django response object, and specify content_type as pdf
    response = HttpResponse(content_type='application/pdf')
    filename = f"{payment.trainee.full_name.replace(' ', '_') if payment.trainee else payment.intern.full_name.replace(' ', '_')}_invoice.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # find the template and render it.
    template = get_template(template_path)
    html = template.render(context)
    
    # create a pdf
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    # if error then show some fun view
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response

# Business Team - Batch Management
@login_required_role(BUSINESS)
def business_batch_management(request):
    search_query = request.GET.get('search', '').strip()

    if request.method == 'POST':
        batch_id = request.POST.get('batch_id')
        selected_trainee_ids = request.POST.getlist('trainees')
        batch = get_object_or_404(Batch, id=batch_id)

        if selected_trainee_ids:
            Trainee.objects.filter(id__in=selected_trainee_ids, status='Active').update(
                batch=batch,
                course=batch.course,
                trainer=batch.trainer
            )
            messages.success(request, 'Trainee added to batch successfully!')
        else:
            messages.warning(request, 'Please select at least one trainee.')

        return redirect('business_batch_management')

    batches = Batch.objects.select_related('course', 'trainer').prefetch_related('trainees').order_by('-start_date')

    if search_query:
        batches = batches.filter(
            Q(batch_name__icontains=search_query) |
            Q(course__title__icontains=search_query) |
            Q(trainer__full_name__icontains=search_query) |
            Q(status__icontains=search_query)
        )

    return render(request, 'core/business_batch_management.html', {
        'batches': batches,
        'trainees': Trainee.objects.filter(status='Active').select_related('batch').order_by('full_name'),
        'search_query': search_query,
    })

# Business Team - Interview Scheduling
@login_required_role(BUSINESS)
def interview_scheduling(request):
    interviews = InterviewSchedule.objects.all()
    trainers = Trainer.objects.filter(status='Active')
    candidates = Candidate.objects.all()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'schedule':
            candidate_id = request.POST.get('candidate')
            trainer_id = request.POST.get('trainer')
            interview_date = request.POST.get('date')
            interview_time = request.POST.get('time')
            location = request.POST.get('location')
            
            InterviewSchedule.objects.create(
                candidate_id=candidate_id,
                interviewer_id=trainer_id,
                interview_date=interview_date,
                interview_time=interview_time,
                location_link=location,
                status='Scheduled'
            )
            messages.success(request, 'Interview scheduled successfully!')
        elif action == 'update_status':
            interview_id = request.POST.get('interview_id')
            interview = get_object_or_404(InterviewSchedule, id=interview_id)
            interview.status = request.POST.get('status')
            interview.save()
            messages.success(request, 'Interview status updated!')
    
    return render(request, 'core/interview_scheduling.html', {
        'interviews': interviews,
        'trainers': trainers,
        'candidates': candidates
    })

# Business Team - Eligibility Management
@login_required_role(BUSINESS)
def eligibility_management(request):
    # Create sample data if needed
    if Eligibility.objects.count() == 0:
        # First create sample candidates
        if Candidate.objects.count() == 0:
            courses = Course.objects.all()
            if courses.count() == 0:
                c1 = Course.objects.create(title="UI/UX Design", status="Active")
                c2 = Course.objects.create(title="Python Programming", status="Active")
                c3 = Course.objects.create(title="Full Stack Development", status="Active")
                courses = [c1, c2, c3]
            
            Candidate.objects.create(
                full_name="Pratheepa",
                phone="9867897612",
                personal_email="pratheepa02@gmail.com",
                course=courses[1] if len(courses) > 1 else courses[0],
                designation="Candidate",
                fees=50000,
                payment_status="Pending",
                status="Pending",
                age=25
            )
            Candidate.objects.create(
                full_name="Ranveer",
                phone="9867897613",
                personal_email="ranveer32@gmail.com",
                course=courses[2] if len(courses) > 2 else courses[0],
                designation="Candidate",
                fees=60000,
                payment_status="Pending",
                status="Pending",
                age=25
            )
            Candidate.objects.create(
                full_name="Devi",
                phone="9867897614",
                personal_email="devi2342@gmail.com",
                course=courses[1] if len(courses) > 1 else courses[0],
                designation="Candidate",
                fees=55000,
                payment_status="Pending",
                status="Pending",
                age=45
            )
        
        # Now create eligibility entries
        candidates = Candidate.objects.all()
        sample_data = [
            {'candidate': candidates[0], 'education': 'BE', 'age': 25, 'status': 'Pending', 'reason': None},
            {'candidate': candidates[1], 'education': 'BA English', 'age': 25, 'status': 'Pending', 'reason': None},
            {'candidate': candidates[2], 'education': 'Msc Computer Science', 'age': 45, 'status': 'Not Eligible', 'reason': 'Candidate exceeds the age eligibility criteria.'}
        ]
        for data in sample_data:
            # Check if candidate already has an eligibility entry
            if not Eligibility.objects.filter(candidate=data['candidate']).exists():
                Eligibility.objects.create(
                    candidate=data['candidate'],
                    education=data['education'],
                    status=data['status'],
                    reason=data['reason']
                )
    
    eligibilities = Eligibility.objects.all()
    candidates = Candidate.objects.all()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        eligibility_id = request.POST.get('eligibility_id')
        eligibility = get_object_or_404(Eligibility, id=eligibility_id)
        
        if action == 'mark_eligible':
            eligibility.status = 'Eligible'
            eligibility.reason = None
            eligibility.verified_at = timezone.now()
            # Ensure this is a manual action by business team
            eligibility.is_auto_eligible = False
            eligibility.save()
            messages.success(request, 'Candidate marked as eligible!')
        elif action == 'mark_not_eligible':
            eligibility.status = 'Not Eligible'
            eligibility.reason = request.POST.get('reason', '')
            eligibility.is_auto_eligible = False
            eligibility.save()
            messages.success(request, 'Candidate marked as not eligible!')
        
        return redirect('eligibility_management')
    
    pending_count = Eligibility.objects.filter(status='Pending').count()
    eligible_count = Eligibility.objects.filter(status='Eligible').count()
    not_eligible_count = Eligibility.objects.filter(status='Not Eligible').count()
    
    return render(request, 'core/eligibility_management.html', {
        'eligibilities': eligibilities,
        'candidates': candidates,
        'pending_count': pending_count,
        'eligible_count': eligible_count,
        'not_eligible_count': not_eligible_count
    })

# Reports & Approvals (Admin)
def reports_approvals(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        report_id = request.POST.get('report_id')
        report = get_object_or_404(Report, id=report_id)
        
        if action == 'approve':
            report.status = 'Approved'
            messages.success(request, 'Report approved!')
        elif action == 'reject':
            report.status = 'Rejected'
            messages.success(request, 'Report rejected!')
        
        report.save()
        return redirect('reports_approvals')
    
    view_mode = request.GET.get('view')
    report_id = request.GET.get('id')
    active_tab = request.GET.get('tab', 'weekly')
    
    report = None
    if view_mode == 'detail' and report_id:
        report = get_object_or_404(Report, id=report_id)
    
    # Filter reports based on tab
    if active_tab == 'daily':
        reports = Report.objects.filter(report_type='Daily')
    elif active_tab == 'monthly':
        reports = Report.objects.filter(report_type='Monthly')
    else:  # weekly
        reports = Report.objects.filter(report_type='Weekly')
    
    return render(request, 'core/reports_approvals.html', {
        'reports': reports,
        'active_tab': active_tab,
        'view_mode': view_mode,
        'report': report
    })

# Business Team - Reports
@login_required_role(BUSINESS)
def business_reports(request):
    def get_report_context(error_message=None, success_message=None):
        view_mode = request.GET.get('view')
        report_id = request.GET.get('id')
        active_tab = request.GET.get('tab', 'weekly')

        report = None
        if view_mode == 'detail' and report_id:
            report = get_object_or_404(Report, id=report_id)

        if active_tab == 'daily':
            reports = Report.objects.filter(report_type='Daily')
        elif active_tab == 'monthly':
            reports = Report.objects.filter(report_type='Monthly')
        else:
            reports = Report.objects.filter(report_type='Weekly')

        return {
            'reports': reports,
            'active_tab': active_tab,
            'view_mode': view_mode,
            'report': report,
            'error_message': error_message,
            'success_message': success_message,
        }

    if request.method == 'POST':
        action = request.POST.get('action')
        report_id = request.POST.get('report_id')
        report = get_object_or_404(Report, id=report_id)

        if action == 'approve':
            report.status = 'Business Team Approved'
            success_message = 'Report approved by business team!'
        elif action == 'reject':
            report.status = 'Rejected'
            success_message = 'Report rejected!'
        else:
            return render(request, 'core/business_reports.html', get_report_context(
                error_message='Invalid report action.'
            ))

        try:
            report.save(update_fields=['status'])
        except DatabaseError:
            return render(request, 'core/business_reports.html', get_report_context(
                error_message='Could not update this report because the database is currently read-only. Please restart the local server or check database write permission.'
            ))

        return render(request, 'core/business_reports.html', get_report_context(
            success_message=success_message
        ))

    return render(request, 'core/business_reports.html', get_report_context())

# Admin - Batch Detail
def batch_detail(request, pk):
    batch = get_object_or_404(Batch, pk=pk)
    return render(request, 'core/batch_detail.html', {'batch': batch})

# ─── Download / Upload Views ─────────────────────────────────────────────────

import csv
import io
import json
from django.http import HttpResponse, FileResponse
from django.utils.text import slugify





# ── 2. Download all payments as CSV (export) ─────────────────────────────────
@login_required_role(ADMIN, BUSINESS)
def export_payments_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="payments-export.csv"'

    writer = csv.writer(response)
    writer.writerow(['Name', 'Course', 'Total Amount', 'Paid', 'Pending',
                     'Status', 'Plan', 'Payment Method', 'Date', 'Due Date'])
    for p in Payment.objects.select_related('trainee', 'intern').all():
        person = p.trainee or p.intern
        name = person.full_name if person else '-'
        course = ''
        if p.trainee and p.trainee.course:
            course = p.trainee.course.title
        elif p.intern:
            course = p.intern.role or '-'
        writer.writerow([
            name, course, p.course_amount, p.paid, p.pending,
            p.status, p.plan or '-', p.payment_method or '-',
            p.date.strftime('%d/%m/%Y'),
            p.due_date.strftime('%d/%m/%Y') if p.due_date else '-',
        ])
    return response


# ── 3. Download intern performance report as CSV ─────────────────────────────
@login_required_role(ADMIN, TRAINER)
def download_intern_performance(request, pk):
    intern = get_object_or_404(Intern, pk=pk)
    response = HttpResponse(content_type='text/csv')
    safe_name = slugify(intern.full_name)
    response['Content-Disposition'] = f'attachment; filename="{safe_name}-performance.csv"'

    writer = csv.writer(response)
    writer.writerow(['Intern Performance Report'])
    writer.writerow([])
    writer.writerow(['Name', intern.full_name])
    writer.writerow(['Email', intern.personal_mail])
    writer.writerow(['Role', intern.role])
    writer.writerow(['Internship Period', intern.internship_period])
    writer.writerow(['Status', intern.status])
    writer.writerow([])
    writer.writerow(['Attendance', '90%'])
    writer.writerow(['Projects Completed', '4 / 5'])
    writer.writerow(['Completion Rate', '80%'])
    return response


# ── 4. Download all trainees as CSV ──────────────────────────────────────────
@login_required_role(ADMIN)
def export_trainees_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="trainees-export.csv"'

    writer = csv.writer(response)
    writer.writerow(['Name', 'Email', 'Phone', 'Gender', 'Course', 'Batch',
                     'Trainer', 'Status', 'Progress'])
    for t in Trainee.objects.select_related('course', 'batch', 'trainer').all():
        writer.writerow([
            t.full_name, t.personal_mail, t.phone_no, t.gender,
            t.course.title if t.course else '-',
            t.batch.batch_name if t.batch else '-',
            t.trainer.full_name if t.trainer else '-',
            t.status, f'{t.progress}%',
        ])
    return response


# ── 5. Upload document for a candidate ───────────────────────────────────────
@login_required_role(ADMIN, BUSINESS)
def upload_document(request, candidate_id):
    candidate = get_object_or_404(Candidate, id=candidate_id)
    if request.method == 'POST' and request.FILES.get('document_file'):
        doc_type = request.POST.get('document_type', 'Document')
        doc_file = request.FILES['document_file']
        DocumentVerification.objects.create(
            candidate=candidate,
            document_type=doc_type,
            document_file=doc_file,
            status='Pending',
        )
        messages.success(request, f'{doc_type} uploaded successfully!')
    else:
        messages.error(request, 'Please select a file to upload.')
    return redirect('document_verification_detail', candidate_id=candidate_id)


# ── 6. Download a document file ──────────────────────────────────────────────
@login_required_role(ADMIN, BUSINESS)
def download_document(request, doc_id):
    doc = get_object_or_404(DocumentVerification, id=doc_id)
    if not doc.document_file:
        messages.error(request, 'No file attached to this document.')
        return redirect('document_verification_detail', candidate_id=doc.candidate.id)
    file_handle = doc.document_file.open('rb')
    filename = doc.document_file.name.split('/')[-1]
    response = FileResponse(file_handle, as_attachment=True, filename=filename)
    return response


# ── 7. Backup database as JSON ────────────────────────────────────────────────
@login_required_role(ADMIN)
def backup_data(request):
    from django.core import serializers as dj_serializers
    from core.models import (User, Trainer, Course, Batch, Trainee, Intern, BusinessTeam,
                              Payment, Report, Enquiry, Candidate, Eligibility,
                              DocumentVerification, InterviewSchedule,
                              SystemSetting, Task, TraineeTask, Project, Message, ContactQuery, Leave)

    all_models = [User, Trainer, Course, Batch, Trainee, Intern, BusinessTeam, Payment,
                  Report, Enquiry, Candidate, Eligibility, DocumentVerification,
                  InterviewSchedule, SystemSetting, Task, TraineeTask, Project, Message, ContactQuery, Leave]

    data = {}
    for model in all_models:
        model_name = model.__name__
        qs = model.objects.all()
        data[model_name] = json.loads(dj_serializers.serialize('json', qs))

    response = HttpResponse(
        json.dumps(data, indent=2, default=str),
        content_type='application/json'
    )
    from django.utils.timezone import now
    filename = f'vtms-backup-{now().strftime("%Y%m%d-%H%M%S")}.json'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # Update last_backup_date in settings
    setting = SystemSetting.objects.first()
    if setting:
        setting.last_backup_date = now()
        setting.last_backup_status = 'Success'
        setting.save()

    return response


# ── 8. Restore from JSON backup ───────────────────────────────────────────────
@login_required_role(ADMIN)
def restore_data(request):
    if request.method != 'POST' or not request.FILES.get('backup_file'):
        messages.error(request, 'Please upload a backup JSON file.')
        return redirect('settings')

    backup_file = request.FILES['backup_file']
    if not backup_file.name.endswith('.json'):
        messages.error(request, 'Only .json backup files are supported.')
        return redirect('settings')

    try:
        from django.core import serializers as dj_serializers
        raw = backup_file.read().decode('utf-8')
        all_data = json.loads(raw)

        restored_count = 0
        for model_name, objects_list in all_data.items():
            json_str = json.dumps(objects_list)
            for obj in dj_serializers.deserialize('json', json_str):
                try:
                    obj.save()
                    restored_count += 1
                except Exception:
                    pass  # skip duplicate/conflict rows

        messages.success(request, f'Backup restored successfully! ({restored_count} records restored)')
    except Exception as e:
        messages.error(request, f'Restore failed: {str(e)}')

    return redirect('settings')


# ── 9. Upload / update business profile photo ────────────────────────────────
@login_required_role(BUSINESS)
def business_profile(request):
    user = request.user
    # Try to get an associated business user profile data
    business_team_member = BusinessTeam.objects.filter(user=user).first()
    context = {'user': user, 'business_team_member': business_team_member}

    if request.method == 'POST':
        full_name = request.POST.get('name')
        office_mail = request.POST.get('office_mail')
        
        if full_name:
            user.first_name = full_name
            user.save()
        
        if office_mail:
            user.email = office_mail
            user.save()
        
        if business_team_member:
            if full_name:
                business_team_member.full_name = full_name
            if office_mail:
                business_team_member.office_mail = office_mail
            business_team_member.save()
        
        if request.FILES.get('profile_image'):
            profile_image = request.FILES['profile_image']
            if business_team_member:
                business_team_member.profile_image = profile_image
                business_team_member.save()
            messages.success(request, 'Profile photo updated successfully!')
        return redirect('business_profile')

    return render(request, 'core/business_profile.html', context)

# Forgot Password
def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        role = request.POST.get('role')
        
        try:
            user = User.objects.get(email=email, role=role)
            # In a real app, you would send an email with a reset link
            # For this demo, we'll show a success message and proceed
            messages.success(request, f'Password reset link sent to {email}. Please check your email.')
            # Store user ID in session for reset (in real app, use token)
            request.session['reset_user_id'] = user.id
            return redirect('reset_password')
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email and role.')
    
    return render(request, 'core/forgot_password.html')

# Reset Password
def reset_password(request):
    if 'reset_user_id' not in request.session:
        messages.error(request, 'Please start the password reset process first.')
        return redirect('forgot_password')
    
    user_id = request.session['reset_user_id']
    
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if new_password != confirm_password:
            messages.error(request, 'Passwords do not match.')
        elif len(new_password) < 6:
            messages.error(request, 'Password must be at least 6 characters long.')
        else:
            try:
                user = User.objects.get(id=user_id)
                user.set_password(new_password)
                user.save()
                # Clear session
                del request.session['reset_user_id']
                messages.success(request, 'Password reset successfully! Please login with your new password.')
                return redirect('login')
            except User.DoesNotExist:
                messages.error(request, 'User not found.')
                return redirect('forgot_password')
    
    return render(request, 'core/reset_password.html')

# Contact Admin
def contact_admin(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        
        # Save the contact query to database
        ContactQuery.objects.create(
            name=name,
            email=email,
            message=message
        )
        
        messages.success(request, 'Your message has been sent to admin. They will contact you soon.')
        return redirect('login')
    
    return render(request, 'core/contact_admin.html')

# Admin: View all contact queries
@login_required_role(ADMIN)
def contact_queries(request):
    queries = ContactQuery.objects.all().order_by('-created_at')
    context = {
        'queries': queries,
    }
    return render(request, 'core/contact_queries.html', context)

# Admin: Mark query as read and view details
@login_required_role(ADMIN)
def mark_query_read(request, query_id):
    query = get_object_or_404(ContactQuery, id=query_id)
    query.is_read = True
    query.save()
    return redirect('contact_queries')

# Admin: Update query status
@login_required_role(ADMIN)
def update_query_status(request, query_id):
    if request.method == 'POST':
        query = get_object_or_404(ContactQuery, id=query_id)
        status = request.POST.get('status')
        query.status = status
        query.save()
        messages.success(request, 'Query status updated successfully!')
    return redirect('contact_queries')

# Mark message as read (works for all roles)
@login_required_role(ADMIN, TRAINER, BUSINESS)
def mark_message_read(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    # Make sure the user is the recipient of the message
    if message.recipient == request.user:
        message.is_read = True
        message.save()
    # Redirect back to the previous page or dashboard
    next_url = request.META.get('HTTP_REFERER')
    if next_url:
        return redirect(next_url)
    # Fallback to appropriate dashboard
    if request.user.role == ADMIN:
        return redirect('admin_dashboard')
    elif request.user.role == TRAINER:
        return redirect('trainer_dashboard')
    else:
        return redirect('business_dashboard')
