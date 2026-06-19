from django.urls import path
from . import views

from django.shortcuts import redirect

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('admin/', views.admin_redirect_view),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('trainer-dashboard/', views.trainer_dashboard, name='trainer_dashboard'),
    path('business-dashboard/', views.business_dashboard, name='business_dashboard'),
    
    # Admin Pages
    path('admin/trainers/', views.trainer_list, name='trainer_list'),
    path('admin/trainers/add/', views.trainer_add, name='trainer_add'),
    path('admin/trainers/<int:pk>/edit/', views.trainer_edit, name='trainer_edit'),
    path('admin/trainers/<int:pk>/delete/', views.trainer_delete, name='trainer_delete'),
    path('admin/batches/', views.batch_list, name='batch_list'),
    path('admin/batches/add/', views.batch_add, name='batch_add'),
    path('admin/batches/<int:pk>/', views.batch_detail, name='batch_detail'),
    path('admin/batches/<int:pk>/edit/', views.batch_edit, name='batch_edit'),
    path('admin/batches/<int:pk>/delete/', views.batch_delete, name='batch_delete'),
    path('admin/trainees/', views.trainee_list, name='trainee_list'),
    path('admin/trainees/add/', views.trainee_add, name='trainee_add'),
    path('admin/trainees/<int:pk>/', views.trainee_detail, name='trainee_detail'),
    path('admin/trainees/<int:pk>/edit/', views.trainee_edit, name='trainee_edit'),
    path('admin/trainees/<int:pk>/delete/', views.trainee_delete, name='trainee_delete'),
    path('admin/interns/', views.intern_list, name='intern_list'),
    path('admin/interns/add/', views.intern_add, name='intern_add'),
    path('admin/interns/<int:pk>/', views.intern_detail, name='intern_detail'),
    path('admin/interns/<int:pk>/edit/', views.intern_edit, name='intern_edit'),
    path('admin/interns/<int:pk>/delete/', views.intern_delete, name='intern_delete'),
    path('admin/interns/<int:pk>/performance/', views.intern_performance, name='intern_performance'),
    path('admin/reports/', views.reports_approvals, name='reports_approvals'),
    path('admin/business/', views.business_monitoring, name='business_monitoring'),
    path('admin/payments/', views.payment_revenue, name='payment_revenue'),
    path('admin/communication/', views.communication, name='communication'),
    path('admin/settings/', views.settings, name='settings'),
    path('admin/invoice/', views.invoice, name='invoice'),
    path('admin/calendar/', views.calendar_leave, name='calendar_leave'),
    
    # Trainer Pages
    path('trainer/batches/', views.trainer_batch_list, name='trainer_batch_list'),
    path('trainer/trainees/', views.trainer_trainee_list, name='trainer_trainee_list'),
    path('trainer/tasks/', views.trainer_tasks, name='trainer_tasks'),
    path('trainer/projects/', views.trainer_projects, name='trainer_projects'),
    path('trainer/reports/daily/', views.trainer_daily_reports, name='trainer_daily_reports'),
    path('trainer/reports/weekly/', views.trainer_weekly_reports, name='trainer_weekly_reports'),
    path('trainer/reports/monthly/', views.trainer_monthly_reports, name='trainer_monthly_reports'),
    path('trainer/internship/', views.trainer_internship_management, name='trainer_internship_management'),
    path('trainer/internship/assign-work/', views.trainer_assign_work, name='trainer_assign_work'),
    path('trainer/internship/performance/<int:intern_id>/', views.trainer_intern_performance, name='trainer_intern_performance'),
    path('trainer/communication/', views.trainer_communication, name='trainer_communication'),
    
    # Business Team - Pages
    path('business/enquiries/', views.enquiry_management, name='enquiry_management'),
    path('business/eligibility/', views.eligibility_management, name='eligibility_management'),
    path('business/candidates/', views.candidate_management, name='candidate_management'),
    path('business/document-verification/', views.document_verification, name='document_verification'),
    path('business/document-verification/<int:candidate_id>/', views.document_verification_detail, name='document_verification_detail'),
    path('business/payments/', views.business_payment_management, name='business_payment_management'),
    path('business/payments/update/', views.update_payment, name='update_payment'),
    path('business/payments/send-email/', views.send_payment_email, name='send_payment_email'),
    path('business/batches/', views.business_batch_management, name='business_batch_management'),
    path('business/reports/', views.business_reports, name='business_reports'),
    path('business/interview-scheduling/', views.interview_scheduling, name='interview_scheduling'),
    path('business/profile/', views.business_profile, name='business_profile'),

    # Upload / Download
    path('download/invoice/<int:payment_id>/', views.download_invoice, name='download_invoice'),
    path('download/payments/csv/', views.export_payments_csv, name='export_payments_csv'),
    path('download/intern-performance/<int:pk>/', views.download_intern_performance, name='download_intern_performance'),
    path('download/trainees/csv/', views.export_trainees_csv, name='export_trainees_csv'),
    path('upload/document/<int:candidate_id>/', views.upload_document, name='upload_document'),
    path('download/document/<int:doc_id>/', views.download_document, name='download_document'),
    path('admin/backup/', views.backup_data, name='backup_data'),
    path('admin/restore/', views.restore_data, name='restore_data'),
]
