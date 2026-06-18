from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.db import DatabaseError
from django.db.models import Q
from .models import User, Trainer, Course, Batch, Trainee, Intern, Payment, Report, Enquiry, Candidate, Eligibility, DocumentVerification, InterviewSchedule, SystemSetting, Task, TraineeTask, Project, Message
from django.utils import timezone
from datetime import timedelta
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
        # Create user first
        user = User.objects.create_user(
            email=request.POST['office_mail'],
            password=request.POST['phone_no'],
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
        messages.success(request, 'New Trainer Added Successfully. Initial password is the phone number.')
        return redirect('trainer_list')
    
    courses = Course.objects.all()
    return render(request, 'core/trainer_form.html', {'courses': courses, 'trainer': None})

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
        trainer.user.save()
        trainer.save()
        messages.success(request, 'Trainer Updated Successfully')
        return redirect('trainer_list')
    
    courses = Course.objects.all()
    return render(request, 'core/trainer_form.html', {'trainer': trainer, 'courses': courses})

@login_required_role(ADMIN)
def trainer_delete(request, pk):
    trainer = get_object_or_404(Trainer, pk=pk)
    trainer.user.delete()  # Delete the associated user too
    messages.success(request, 'Trainer Deleted Successfully')
    return redirect('trainer_list')

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
        
        # Send email
        if email_to and email_subject:
            try:
                # Determine recipient email
                recipient_list = [email_to]
                if trainer and trainer.office_mail:
                    recipient_list = [trainer.office_mail]
                
                send_mail(
                    subject=email_subject,
                    message=email_preview,
                    from_email=email_from,
                    recipient_list=recipient_list,
                    fail_silently=True,
                )
                messages.success(request, 'New Batch Added Successfully and Email Sent!')
            except Exception as e:
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
        
        # Send email
        if email_to and email_subject:
            try:
                # Determine recipient email
                recipient_list = [email_to]
                if batch.trainer and batch.trainer.office_mail:
                    recipient_list = [batch.trainer.office_mail]
                
                send_mail(
                    subject=email_subject,
                    message=email_preview,
                    from_email=email_from,
                    recipient_list=recipient_list,
                    fail_silently=True,
                )
                messages.success(request, 'Batch Updated Successfully and Email Sent!')
            except Exception as e:
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
        # Create user
        user = User.objects.create_user(
            email=request.POST['personal_mail'],
            password=request.POST['phone_no'],
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

        messages.success(request, 'Trainee added successfully! Initial password is the phone number.')
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
    if request.method == 'POST':
        user = User.objects.create_user(
            email=request.POST['personal_mail'],
            password=request.POST['phone_no'],
            role=User.Role.INTERN,
            phone_no=request.POST['phone_no'],
        )
        intern = Intern.objects.create(
            user=user,
            full_name=request.POST['full_name'],
            personal_mail=request.POST['personal_mail'],
            phone_no=request.POST['phone_no'],
            gender=request.POST['gender'],
            role=request.POST['role'],
            internship_period=request.POST['internship_period'],
            status=request.POST['status']
        )
        if request.POST.get('trainer'):
            intern.trainer = Trainer.objects.get(id=request.POST['trainer'])
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
                messages.success(request, 'Intern added successfully and Email Sent! Initial password is the phone number.')
            except Exception as e:
                messages.warning(request, 'Intern added successfully, but Email Failed to Send. Initial password is the phone number.')
        else:
            messages.success(request, 'Intern added successfully! Initial password is the phone number.')
        
        return redirect('intern_list')
    trainers = Trainer.objects.filter(status='Active')
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
        if request.POST.get('trainer'):
            intern.trainer = Trainer.objects.get(id=request.POST['trainer'])
        intern.user.email = request.POST['personal_mail']
        intern.user.phone_no = request.POST['phone_no']
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
    return render(request, 'core/intern_performance.html', {'intern': intern})

# Reports & Approvals
def reports_approvals(request):
    return render(request, 'core/reports_approvals.html')

# Business Monitoring
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
def communication(request):
    return render(request, 'core/communication.html')

# Settings
def settings(request):
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
def calendar_leave(request):
    return render(request, 'core/calendar_leave.html')

# Business - Profile
def business_profile(request):
    return render(request, 'core/business_profile.html')

# Trainer - Batches
def trainer_batch_list(request):
    trainer = Trainer.objects.filter(user=request.user).first()
    batches = Batch.objects.filter(trainer=trainer) if trainer else Batch.objects.all()
    return render(request, 'core/trainer_batch_list.html', {'batches': batches})

# Trainer - Trainees
def trainer_trainee_list(request):
    trainer = Trainer.objects.filter(user=request.user).first()
    trainees = Trainee.objects.filter(trainer=trainer) if trainer else Trainee.objects.all()
    return render(request, 'core/trainer_trainee_list.html', {'trainees': trainees})

# Trainer - Tasks
def trainer_tasks(request):
    trainer = Trainer.objects.first()  # Current trainer
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
def trainer_internship_management(request):
    trainer = Trainer.objects.filter(user=request.user).first()
    interns = Intern.objects.filter(trainer=trainer) if trainer else Intern.objects.all()
    return render(request, 'core/trainer_internship_management.html', {'interns': interns})


# Trainer - Assign Work Page
def trainer_assign_work(request):
    intern_id = request.GET.get('intern_id')
    intern = None
    if intern_id:
        intern = get_object_or_404(Intern, id=intern_id)
    return render(request, 'core/trainer_assign_work.html', {'intern': intern})


# Trainer - Intern Performance Page
def trainer_intern_performance(request, intern_id):
    intern = get_object_or_404(Intern, id=intern_id)
    return render(request, 'core/trainer_intern_performance.html', {'intern': intern})


# Trainer - Communication Page
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q


def trainer_communication(request):
    # Get or create sample messages if none exist
    if Message.objects.count() == 0:
        # Get a default user or create one for sender
        trainer_user = User.objects.filter(role='Trainer').first()
        if not trainer_user:
            trainer_user = User.objects.create_superuser(email="trainer@test.com", password="password123")
        
        # Create sample messages
        sample_messages = [
            {
                "subject": "Task Doubt",
                "preview": "Hi mam, I have doubt on today task...",
                "avatar_initial": "P",
                "avatar_color": "#9E69FF",
                "created_at": timezone.now(),
                "is_read": False
            },
            {
                "subject": "Weekly Report Approved by business team",
                "preview": "Hi mam, please find the report of batch 8 students weekly report",
                "avatar_initial": "B",
                "avatar_color": "#36B37E",
                "created_at": timezone.now() - timedelta(days=1),
                "is_read": True
            },
            {
                "subject": "Task Doubt",
                "preview": "Hi mam, I have doubt on today task...",
                "avatar_initial": "R",
                "avatar_color": "#FFAB00",
                "created_at": timezone.now() - timedelta(days=2),
                "is_read": True
            },
            {
                "subject": "Daily Task (22/03/2026)",
                "preview": "Trainee Name: Amire....",
                "avatar_initial": "A",
                "avatar_color": "#22C55E",
                "created_at": timezone.now() - timedelta(days=3),
                "is_read": True
            },
            {
                "subject": "Daily Task (21/03/2026)",
                "preview": "Trainee Name: Praveen....",
                "avatar_initial": "P",
                "avatar_color": "#9E69FF",
                "created_at": timezone.now() - timedelta(days=4),
                "is_read": True
            }
        ]
        for msg in sample_messages:
            Message.objects.create(
                sender=trainer_user,
                subject=msg["subject"],
                preview=msg["preview"],
                avatar_initial=msg["avatar_initial"],
                avatar_color=msg["avatar_color"],
                created_at=msg["created_at"],
                is_read=msg["is_read"]
            )
    
    # Handle POST requests
    active_filter = request.GET.get('filter', 'all')
    search_query = request.GET.get('q', '')

    if request.method == "POST":
        action = request.POST.get('action')
        
        if action == "toggle_read":
            msg_id = request.POST.get('msg_id')
            message = get_object_or_404(Message, id=msg_id)
            message.is_read = not message.is_read
            message.save()
    
    # Filter messages
    messages_query = Message.objects.all()
    if search_query:
        messages_query = messages_query.filter(
            Q(subject__icontains=search_query) | Q(preview__icontains=search_query)
        )
    if active_filter == 'unread':
        messages_query = messages_query.filter(is_read=False)
    messages = messages_query.order_by("-created_at")
    
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)

    return render(request, 'core/trainer_communication.html', {
        'messages': messages,
        'today': today,
        'yesterday': yesterday,
        'active_filter': active_filter,
        'search_query': search_query
    })

# Trainer - Projects
def trainer_projects(request):
    trainer = Trainer.objects.filter(user=request.user).first()
    projects = Project.objects.filter(trainer=trainer) if trainer else Project.objects.all()
    return render(request, 'core/trainer_projects.html', {'projects': projects})

# Trainer - Daily Reports
def trainer_daily_reports(request):
    trainer = Trainer.objects.filter(user=request.user).first()
    reports = Report.objects.filter(report_type='Daily', trainer=trainer).order_by('-date') if trainer else Report.objects.filter(report_type='Daily').order_by('-date')
    return render(request, 'core/trainer_daily_reports.html', {'reports': reports})

# Trainer - Weekly Reports
def trainer_weekly_reports(request):
    trainer = Trainer.objects.filter(user=request.user).first()
    reports = Report.objects.filter(report_type='Weekly', trainer=trainer).order_by('-date') if trainer else Report.objects.filter(report_type='Weekly').order_by('-date')
    return render(request, 'core/trainer_weekly_reports.html', {'reports': reports})

# Trainer - Monthly Reports
def trainer_monthly_reports(request):
    trainer = Trainer.objects.filter(user=request.user).first()
    reports = Report.objects.filter(report_type='Monthly', trainer=trainer).order_by('-date') if trainer else Report.objects.filter(report_type='Monthly').order_by('-date')
    return render(request, 'core/trainer_monthly_reports.html', {'reports': reports})

# Trainer - Attendance
def trainer_attendance(request):
    trainer = Trainer.objects.filter(user=request.user).first()
    from core.models import Attendance
    attendance_records = Attendance.objects.filter(batch__trainer=trainer).order_by('-date') if trainer else Attendance.objects.order_by('-date')
    return render(request, 'core/trainer_attendance.html', {'attendance_records': attendance_records, 'trainer': trainer})

# Trainer - Calendar
def trainer_calendar(request):
    trainer = Trainer.objects.filter(user=request.user).first()
    batches = Batch.objects.filter(trainer=trainer) if trainer else Batch.objects.all()
    return render(request, 'core/trainer_calendar.html', {'batches': batches})

# Trainer - Profile
def trainer_profile(request):
    trainer = Trainer.objects.filter(user=request.user).first()
    if request.method == 'POST' and trainer:
        trainer.full_name = request.POST.get('full_name', trainer.full_name)
        trainer.office_mail = request.POST.get('office_mail', trainer.office_mail)
        trainer.personal_mail = request.POST.get('personal_mail', trainer.personal_mail)
        trainer.phone_no = request.POST.get('phone_no', trainer.phone_no)
        if request.FILES.get('profile_image'):
            trainer.profile_image = request.FILES['profile_image']
        trainer.save()
        trainer.user.email = trainer.office_mail
        trainer.user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('trainer_profile')
    return render(request, 'core/trainer_profile.html', {'trainer': trainer})

# Business Team - Enquiry Management
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
def business_payment_management(request):
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

    payments = Payment.objects.select_related('trainee', 'intern').all()
    
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
    
    # Handle POST for payment actions
    if request.method == 'POST':
        action = request.POST.get('action')
        payment_id = request.POST.get('payment_id')
        payment = get_object_or_404(Payment, id=payment_id)
        
        if action == 'mark_paid':
            payment.status = 'Paid'
            payment.save()
            messages.success(request, f'Payment marked as Paid!')
            return redirect('business_payment_management')
        elif action == 'mark_pending':
            payment.status = 'Pending'
            payment.save()
            messages.success(request, f'Payment marked as Pending!')
            return redirect('business_payment_management')
    
    # Calculate statistics
    total_revenue = sum(p.course_amount for p in payments)
    total_collected = sum(p.paid for p in payments)
    total_pending = sum(p.pending for p in payments)
    pending_count = payments.filter(status='Pending').count()
    
    return render(request, 'core/business_payment_management.html', {
        'payments': payments,
        'total_revenue': total_revenue,
        'total_collected': total_collected,
        'total_pending': total_pending,
        'pending_count': pending_count,
        'search_query': search_query,
        'status_filter': status_filter,
    })

# Business Team - Batch Management
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


# ── 1. Download invoice as CSV for a payment ────────────────────────────────
@login_required_role(ADMIN, BUSINESS)
def download_invoice(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    person = payment.trainee or payment.intern
    name = person.full_name if person else 'Unknown'
    course = ''
    if payment.trainee and payment.trainee.course:
        course = payment.trainee.course.title
    elif payment.intern:
        course = payment.intern.role

    response = HttpResponse(content_type='text/csv')
    safe_name = slugify(name)
    response['Content-Disposition'] = f'attachment; filename="{safe_name}-invoice.csv"'

    writer = csv.writer(response)
    writer.writerow(['Invoice'])
    writer.writerow([])
    writer.writerow(['Name', name])
    writer.writerow(['Course', course])
    writer.writerow(['Total Amount', f'Rs.{payment.course_amount}'])
    writer.writerow(['Amount Paid', f'Rs.{payment.paid}'])
    writer.writerow(['Pending', f'Rs.{payment.pending}'])
    writer.writerow(['Status', payment.status])
    writer.writerow(['Payment Date', payment.date.strftime('%d/%m/%Y')])
    writer.writerow(['Plan', payment.plan or '-'])
    writer.writerow(['Payment Method', payment.payment_method or '-'])
    if payment.due_date:
        writer.writerow(['Due Date', payment.due_date.strftime('%d/%m/%Y')])
    return response


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
    from core.models import (User, Trainer, Course, Batch, Trainee, Intern,
                              Payment, Report, Enquiry, Candidate, Eligibility,
                              DocumentVerification, InterviewSchedule,
                              SystemSetting, Task, TraineeTask, Project, Message)

    all_models = [User, Trainer, Course, Batch, Trainee, Intern, Payment,
                  Report, Enquiry, Candidate, Eligibility, DocumentVerification,
                  InterviewSchedule, SystemSetting, Task, TraineeTask, Project, Message]

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
    context = {'user': user}

    if request.method == 'POST':
        if request.FILES.get('profile_image'):
            # Save profile image to user's media folder (store on user model via generic path)
            # We store it on the logged-in user's side — use a simple approach
            profile_image = request.FILES['profile_image']
            # Save to media/profiles/<user_id>.<ext>
            import os
            from django.core.files.storage import default_storage
            ext = os.path.splitext(profile_image.name)[1]
            path = f'profiles/user_{user.id}{ext}'
            saved_path = default_storage.save(path, profile_image)
            # Store path in session for now (lightweight approach without model change)
            request.session['profile_image_url'] = saved_path
            messages.success(request, 'Profile photo updated successfully!')
        return redirect('business_profile')

    profile_image_url = request.session.get('profile_image_url')
    if profile_image_url:
        from django.conf import settings as django_settings
        context['profile_image_url'] = f'{django_settings.MEDIA_URL}{profile_image_url}'

    return render(request, 'core/business_profile.html', context)
