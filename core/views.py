from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .models import User, Trainer, Course, Batch, Trainee, Intern, Payment, Report, Enquiry, Candidate, Eligibility, DocumentVerification, InterviewSchedule
from django.utils import timezone

def login_view(request):
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

def admin_dashboard(request):
    total_trainers = Trainer.objects.filter(status='Active').count()
    total_trainees = Trainee.objects.filter(status='Active').count()
    active_batches = Batch.objects.filter(status='Active')
    active_batches_count = active_batches.count()
    pending_reports = Report.objects.filter(status='Pending').count()
    
    # For stats grid
    context = {
        'total_trainers': total_trainers,
        'total_trainees': total_trainees,
        'active_batches_count': active_batches_count,
        'pending_reports': pending_reports,
        'active_batches': active_batches,
    }
    return render(request, 'core/dashboard.html', context)

def trainer_dashboard(request):
    return render(request, 'core/trainer_dashboard.html')

def business_dashboard(request):
    total_enquiries = Enquiry.objects.count()
    total_candidates = Candidate.objects.count()
    eligible_candidates = Eligibility.objects.filter(status='Eligible').count()
    pending_interviews = InterviewSchedule.objects.filter(status='Pending').count()
    
    context = {
        'total_enquiries': total_enquiries,
        'total_candidates': total_candidates,
        'eligible_candidates': eligible_candidates,
        'pending_interviews': pending_interviews,
    }
    return render(request, 'core/business_dashboard.html', context)

# Trainer Management
def trainer_list(request):
    trainers = Trainer.objects.all()
    courses = Course.objects.all()
    return render(request, 'core/trainer_list.html', {'trainers': trainers, 'courses': courses})

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
    return render(request, 'core/trainer_form.html', {'courses': courses})

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

def trainer_delete(request, pk):
    trainer = get_object_or_404(Trainer, pk=pk)
    trainer.user.delete()  # Delete the associated user too
    messages.success(request, 'Trainer Deleted Successfully')
    return redirect('trainer_list')

# Batch Management
def batch_list(request):
    batches = Batch.objects.all()
    return render(request, 'core/batch_list.html', {'batches': batches})

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
        messages.success(request, 'New Batch Added Successfully')
        return redirect('batch_list')
    
    courses = Course.objects.all()
    trainers = Trainer.objects.filter(status='Active')
    return render(request, 'core/batch_form.html', {'courses': courses, 'trainers': trainers})

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
        
        if course_id:
            batch.course = Course.objects.get(id=course_id)
        else:
            batch.course = None
            
        if trainer_id:
            batch.trainer = Trainer.objects.get(id=trainer_id)
        else:
            batch.trainer = None
            
        batch.save()
        messages.success(request, 'Batch Updated Successfully')
        return redirect('batch_list')
    
    courses = Course.objects.all()
    trainers = Trainer.objects.filter(status='Active')
    selected_days = batch.days.split(',') if batch.days else []
    return render(request, 'core/batch_form.html', {'batch': batch, 'courses': courses, 'trainers': trainers, 'selected_days': selected_days})

def batch_delete(request, pk):
    batch = get_object_or_404(Batch, pk=pk)
    batch.delete()
    messages.success(request, 'Batch Deleted Successfully')
    return redirect('batch_list')

# Admin - Trainee List
def trainee_list(request):
    trainees = Trainee.objects.all()
    return render(request, 'core/trainee_list.html', {'trainees': trainees})

# Admin - Trainee Add
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
    return render(request, 'core/trainee_form.html', {'courses': courses, 'batches': batches, 'trainers': trainers})

# Admin - Trainee Detail
def trainee_detail(request, pk):
    trainee = get_object_or_404(Trainee, pk=pk)
    return render(request, 'core/trainee_detail.html', {'trainee': trainee})

# Admin - Trainee Edit
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
def trainee_delete(request, pk):
    trainee = get_object_or_404(Trainee, pk=pk)
    trainee.user.delete()
    messages.success(request, 'Trainee deleted successfully!')
    return redirect('trainee_list')

# Intern Management
def intern_list(request):
    interns = Intern.objects.all()
    return render(request, 'core/intern_list.html', {'interns': interns})

# Admin - Intern Add
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
        messages.success(request, 'Intern added successfully! Initial password is the phone number.')
        return redirect('intern_list')
    trainers = Trainer.objects.filter(status='Active')
    return render(request, 'core/intern_form.html', {'trainers': trainers})

# Admin - Intern Detail
def intern_detail(request, pk):
    intern = get_object_or_404(Intern, pk=pk)
    return render(request, 'core/intern_detail.html', {'intern': intern})

# Admin - Intern Edit
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
    return render(request, 'core/business_monitoring.html')

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
    
    trainees = Trainee.objects.all()
    payments = Payment.objects.all()
    return render(request, 'core/payment_revenue.html', {'trainees': trainees, 'payments': payments})

# Communication
def communication(request):
    return render(request, 'core/communication.html')

# Settings
def settings(request):
    return render(request, 'core/settings.html')

# Admin - Invoice
def invoice(request):
    return render(request, 'core/invoice.html')

# Admin - Calendar & Leave
def calendar_leave(request):
    return render(request, 'core/calendar_leave.html')

# Business - Profile
def business_profile(request):
    return render(request, 'core/business_profile.html')

# Trainer - Batches
def trainer_batch_list(request):
    # For demo, assume trainer is logged in, get their batches
    batches = Batch.objects.all()
    return render(request, 'core/trainer_batch_list.html', {'batches': batches})

# Trainer - Trainees
def trainer_trainee_list(request):
    trainees = Trainee.objects.all()
    return render(request, 'core/trainer_trainee_list.html', {'trainees': trainees})

# Trainer - Tasks
def trainer_tasks(request):
    return render(request, 'core/trainer_tasks.html')

# Trainer - Projects
def trainer_projects(request):
    return render(request, 'core/trainer_projects.html')

# Trainer - Daily Reports
def trainer_daily_reports(request):
    return render(request, 'core/trainer_daily_reports.html')

# Trainer - Weekly Reports
def trainer_weekly_reports(request):
    return render(request, 'core/trainer_weekly_reports.html')

# Trainer - Monthly Reports
def trainer_monthly_reports(request):
    return render(request, 'core/trainer_monthly_reports.html')

# Trainer - Attendance
def trainer_attendance(request):
    return render(request, 'core/trainer_attendance.html')

# Trainer - Calendar
def trainer_calendar(request):
    return render(request, 'core/trainer_calendar.html')

# Trainer - Profile
def trainer_profile(request):
    return render(request, 'core/trainer_profile.html')

# Business Team - Enquiry Management
def enquiry_management(request):
    enquiries = Enquiry.objects.all()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        enquiry_id = request.POST.get('enquiry_id')
        enquiry = get_object_or_404(Enquiry, id=enquiry_id)
        
        if action == 'update_status':
            new_status = request.POST.get('status')
            enquiry.status = new_status
            enquiry.save()
            messages.success(request, 'Enquiry status updated successfully!')
        elif action == 'convert_to_candidate':
            # Create candidate from enquiry
            candidate = Candidate.objects.create(
                full_name=enquiry.full_name,
                personal_email=enquiry.email,
                phone=enquiry.phone,
                course=enquiry.course_interested,
                status='Pending',
                payment_status='Pending'
            )
            messages.success(request, 'Enquiry converted to candidate successfully!')
    
    return render(request, 'core/enquiry_management.html', {'enquiries': enquiries})

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
    eligibilities = Eligibility.objects.all()
    candidates = Candidate.objects.all()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        eligibility_id = request.POST.get('eligibility_id')
        eligibility = get_object_or_404(Eligibility, id=eligibility_id)
        
        if action == 'mark_eligible':
            eligibility.status = 'Eligible'
            eligibility.verified_at = timezone.now()
            eligibility.save()
            messages.success(request, 'Candidate marked as eligible!')
        elif action == 'mark_not_eligible':
            eligibility.status = 'Not Eligible'
            eligibility.save()
            messages.success(request, 'Candidate marked as not eligible!')
    
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

# Reports & Approvals (Business Team)
def reports_approvals(request):
    reports = Report.objects.all()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        report_id = request.POST.get('report_id')
        report = get_object_or_404(Report, id=report_id)
        
        if action == 'approve':
            report.status = 'Approved'
            report.save()
            messages.success(request, 'Report approved!')
        elif action == 'reject':
            report.status = 'Pending'
            report.save()
            messages.success(request, 'Report sent back for review!')
    
    return render(request, 'core/reports_approvals.html', {'reports': reports})

# Admin - Batch Detail
def batch_detail(request, pk):
    batch = get_object_or_404(Batch, pk=pk)
    return render(request, 'core/batch_detail.html', {'batch': batch})
