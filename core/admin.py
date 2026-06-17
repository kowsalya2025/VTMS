from django.contrib import admin
from .models import (User, Course, Trainer, Batch, Trainee, Intern, Attendance, Report, Payment, 
                     SystemSetting, Task, TraineeTask, Project, Leave, Enquiry, Candidate, Eligibility, 
                     DocumentVerification, InterviewSchedule)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'role', 'phone_no', 'is_staff', 'is_active']
    list_filter = ['role', 'is_staff', 'is_active']
    search_fields = ['email']

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'status']
    list_filter = ['status']

@admin.register(Trainer)
class TrainerAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'office_mail', 'phone_no', 'course', 'status']
    list_filter = ['status', 'course']
    search_fields = ['full_name', 'office_mail', 'personal_mail']

@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ['batch_name', 'course', 'trainer', 'start_date', 'end_date', 'status']
    list_filter = ['status', 'course', 'trainer']

@admin.register(Trainee)
class TraineeAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'personal_mail', 'phone_no', 'course', 'batch', 'trainer', 'status', 'progress']
    list_filter = ['status', 'course', 'batch', 'trainer']
    search_fields = ['full_name', 'personal_mail']

@admin.register(Intern)
class InternAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'personal_mail', 'phone_no', 'role', 'trainer', 'status']
    list_filter = ['status', 'role', 'trainer']
    search_fields = ['full_name', 'personal_mail']

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['trainee', 'intern', 'batch', 'date', 'status']
    list_filter = ['date', 'status', 'batch']

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['report_type', 'batch', 'trainer', 'date', 'status']
    list_filter = ['report_type', 'status', 'date', 'batch', 'trainer']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['trainee', 'intern', 'course_amount', 'paid', 'pending', 'status', 'date']
    list_filter = ['status', 'date']

@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ['organizer_name', 'enable_email_notification', 'enable_whatsapp_alerts']

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['task_name', 'batch', 'trainer', 'day', 'total_task', 'assigned_date', 'due_date', 'status']
    list_filter = ['status', 'batch', 'trainer', 'assigned_date']

@admin.register(TraineeTask)
class TraineeTaskAdmin(admin.ModelAdmin):
    list_display = ['task', 'trainee', 'completed_task', 'submission_date', 'status', 'is_checked']
    list_filter = ['status', 'task', 'trainee']

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['project_name', 'batch', 'intern', 'trainer', 'assigned_date', 'deadline', 'status']
    list_filter = ['status', 'assigned_date', 'deadline', 'trainer']

@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display = ['batch', 'date', 'day', 'reason']
    list_filter = ['date', 'batch']

@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'phone', 'course_interested', 'status', 'created_at']
    list_filter = ['status', 'course_interested', 'created_at']
    search_fields = ['full_name', 'email', 'phone']

@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'phone', 'personal_email', 'course', 'payment_status', 'status', 'created_at']
    list_filter = ['status', 'payment_status', 'course', 'created_at']
    search_fields = ['full_name', 'phone', 'personal_email']

@admin.register(Eligibility)
class EligibilityAdmin(admin.ModelAdmin):
    list_display = ['candidate', 'education', 'status', 'verified_by', 'verified_at', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['candidate__full_name']

@admin.register(DocumentVerification)
class DocumentVerificationAdmin(admin.ModelAdmin):
    list_display = ['candidate', 'document_type', 'status', 'submitted_date', 'verified_by', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['candidate__full_name', 'document_type']

@admin.register(InterviewSchedule)
class InterviewScheduleAdmin(admin.ModelAdmin):
    list_display = ['candidate', 'interviewer', 'interview_date', 'interview_time', 'status', 'created_at']
    list_filter = ['status', 'interview_date', 'interviewer']
    search_fields = ['candidate__full_name']

