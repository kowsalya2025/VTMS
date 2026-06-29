from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db.models.signals import post_save
from django.dispatch import receiver

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        TRAINER = 'TRAINER', 'Trainer'
        BUSINESS_TEAM = 'BUSINESS_TEAM', 'Business Team'
        TRAINEE = 'TRAINEE', 'Trainee'
        INTERN = 'INTERN', 'Intern'

    username = None
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.ADMIN)
    phone_no = models.CharField(max_length=15, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

class Course(models.Model):
    title = models.CharField(max_length=100)
    fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=[('Active', 'Active'), ('Inactive', 'Inactive')], default='Active')

    def __str__(self):
        return self.title

class Trainer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    office_mail = models.EmailField()
    personal_mail = models.EmailField()
    phone_no = models.CharField(max_length=15)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')])
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=[('Active', 'Active'), ('Inactive', 'Inactive')], default='Active')
    profile_image = models.ImageField(upload_to='trainers/', null=True, blank=True)

    def __str__(self):
        return self.full_name

class Batch(models.Model):
    class Status(models.TextChoices):
        UPCOMING = 'Upcoming', 'Upcoming'
        ACTIVE = 'Active', 'Active'
        COMPLETED = 'Completed', 'Completed'

    batch_name = models.CharField(max_length=100)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    trainer = models.ForeignKey(Trainer, on_delete=models.SET_NULL, null=True, related_name='batches')
    description = models.TextField(blank=True, null=True)
    
    start_date = models.DateField()
    end_date = models.DateField()
    duration = models.CharField(max_length=50) # e.g., "30 Days"
    
    timing_start = models.TimeField()
    timing_end = models.TimeField()
    days = models.CharField(max_length=100) # Storing comma separated e.g. "Mon,Tue,Wed"
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UPCOMING)
    batch_file = models.FileField(upload_to='batch_files/', null=True, blank=True)

    def __str__(self):
        return self.batch_name

class Trainee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    office_mail = models.EmailField(blank=True, null=True)
    personal_mail = models.EmailField()
    phone_no = models.CharField(max_length=15)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')])
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    guardian_name = models.CharField(max_length=100, blank=True, null=True)
    guardian_phone = models.CharField(max_length=15, blank=True, null=True)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True)
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, related_name='trainees')
    trainer = models.ForeignKey(Trainer, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=[('Active', 'Active'), ('Dropout', 'Dropout')], default='Active')
    progress = models.IntegerField(default=0) # percentage
    first_installment_paid = models.BooleanField(default=False)

    def __str__(self):
        return self.full_name

@receiver(post_save, sender=Trainee)
def create_trainee_payment(sender, instance, created, **kwargs):
    if instance.course:
        from .models import Payment
        if not Payment.objects.filter(trainee=instance).exists():
            Payment.objects.create(
                trainee=instance,
                course_amount=instance.course.fees,
                paid=0,
                pending=instance.course.fees,
                status='Pending',
                plan='-',
                payment_method='-',
            )

class Intern(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    office_mail = models.EmailField(blank=True, null=True)
    personal_mail = models.EmailField()
    phone_no = models.CharField(max_length=15)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')])
    role = models.CharField(max_length=50) # e.g. Junior Developer
    internship_period = models.CharField(max_length=20) # e.g. 1 Month, 2 Month
    join_date = models.DateField(null=True, blank=True)
    trainer = models.ForeignKey(Trainer, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=[('Active', 'Active'), ('Completed', 'Completed')], default='Active')
    trainer_remarks = models.TextField(blank=True, null=True)
    overall_status = models.CharField(max_length=50, default='Good Performance')

    def __str__(self):
        return self.full_name

class BusinessTeam(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    office_mail = models.EmailField()
    personal_mail = models.EmailField()
    phone_no = models.CharField(max_length=15)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')])
    status = models.CharField(max_length=20, choices=[('Active', 'Active'), ('Inactive', 'Inactive')], default='Active')
    profile_image = models.ImageField(upload_to='business_team/', null=True, blank=True)

    def __str__(self):
        return self.full_name


class Message(models.Model):
    class NotificationType(models.TextChoices):
        REPORT = 'REPORT', 'Report'
        PAYMENT = 'PAYMENT', 'Payment'
        ENQUIRY = 'ENQUIRY', 'Enquiry'
        GENERAL = 'GENERAL', 'General'
        TASK = 'TASK', 'Task'
        BATCH = 'BATCH', 'Batch'

    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_messages", null=True, blank=True)
    subject = models.CharField(max_length=200)
    preview = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    notification_type = models.CharField(max_length=20, choices=NotificationType.choices, default=NotificationType.GENERAL)
    created_at = models.DateTimeField(auto_now_add=True)
    avatar_color = models.CharField(max_length=20, default="#9E69FF") # hex color
    avatar_initial = models.CharField(max_length=1)

    def __str__(self):
        return self.subject

class ContactQuery(models.Model):
    class Status(models.TextChoices):
        NEW = 'New', 'New'
        IN_PROGRESS = 'In Progress', 'In Progress'
        RESOLVED = 'Resolved', 'Resolved'

    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.email}"

class Attendance(models.Model):
    trainee = models.ForeignKey(Trainee, on_delete=models.CASCADE, null=True, blank=True)
    intern = models.ForeignKey(Intern, on_delete=models.CASCADE, null=True, blank=True)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField()
    status = models.CharField(max_length=20, choices=[('Present', 'Present'), ('Absent', 'Absent')])

class Report(models.Model):
    class ReportType(models.TextChoices):
        DAILY = 'Daily', 'Daily'
        WEEKLY = 'Weekly', 'Weekly'
        MONTHLY = 'Monthly', 'Monthly'

    report_type = models.CharField(max_length=20, choices=ReportType.choices)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE)
    date = models.DateField()
    submitted_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    status = models.CharField(max_length=30, choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected'), ('Business Team Approved', 'Business Team Approved')], default='Pending')
    content = models.TextField(blank=True, null=True)

class Payment(models.Model):
    trainee = models.ForeignKey(Trainee, on_delete=models.CASCADE, null=True, blank=True)
    intern = models.ForeignKey(Intern, on_delete=models.CASCADE, null=True, blank=True)
    course_amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pending = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[('Paid', 'Paid'), ('Pending', 'Pending')])
    date = models.DateField(auto_now_add=True)
    plan = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., 2 - Installment, One - Time Payment")
    payment_method = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., UPI, Bank Transfer")
    due_date = models.DateField(blank=True, null=True)

class SystemSetting(models.Model):
    # General
    organizer_name = models.CharField(max_length=100, default='Vetri Training Management')
    # SMTP
    smtp_email = models.EmailField(blank=True, null=True)
    smtp_host = models.CharField(max_length=100, blank=True, null=True)
    smtp_port = models.CharField(max_length=10, blank=True, null=True)
    smtp_user = models.CharField(max_length=100, blank=True, null=True)
    smtp_password = models.CharField(max_length=100, blank=True, null=True)
    # WhatsApp
    whatsapp_number = models.CharField(max_length=20, blank=True, null=True)
    # Notifications
    enable_email_notification = models.BooleanField(default=True)
    enable_whatsapp_alerts = models.BooleanField(default=False)
    # Backup
    backup_frequency = models.CharField(max_length=50, default='Daily')
    last_backup_date = models.DateTimeField(blank=True, null=True)
    last_backup_status = models.CharField(max_length=50, default='Pending')
    # Admin Permissions
    admin_edit_batch = models.BooleanField(default=True)
    admin_batch_course_control = models.BooleanField(default=True)
    admin_reports_approval = models.BooleanField(default=True)
    admin_payment_verification = models.BooleanField(default=True)
    # Trainer Permissions
    trainer_attendance_update = models.BooleanField(default=True)
    trainer_task_project_update = models.BooleanField(default=True)
    trainer_report_submission = models.BooleanField(default=True)
    # Business Team Permissions
    business_enquiry_check = models.BooleanField(default=True)
    business_document_verification = models.BooleanField(default=True)
    business_payment_handling = models.BooleanField(default=True)
    business_batch_allocation = models.BooleanField(default=True)
    business_reports_approval = models.BooleanField(default=True)

class Task(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='tasks', null=True, blank=True)
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, null=True, blank=True)
    task_name = models.CharField(max_length=200)
    day = models.CharField(max_length=20, blank=True, null=True) # e.g., Day 20
    total_task = models.IntegerField(default=30)
    assigned_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Completed', 'Completed')], default='Pending')
    assigned_to_all = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.task_name} - {self.batch.batch_name}"

class TraineeTask(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='trainee_tasks')
    trainee = models.ForeignKey(Trainee, on_delete=models.CASCADE)
    completed_task = models.IntegerField(default=0)
    submission_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[('Incomplete', 'Incomplete'), ('Complete', 'Complete'), ('Dropout', 'Dropout')], default='Incomplete')
    is_checked = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.trainee.full_name} - {self.task.task_name}"

class Project(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, null=True, blank=True)
    intern = models.ForeignKey(Intern, on_delete=models.CASCADE, null=True, blank=True)
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, null=True, blank=True)
    project_name = models.CharField(max_length=200)
    assigned_date = models.DateField(null=True, blank=True)
    deadline = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[('Assigned', 'Assigned'), ('In Progress', 'In Progress'), ('Completed', 'Completed')], default='Assigned')

    def __str__(self):
        return self.project_name

class Leave(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    date = models.DateField()
    day = models.CharField(max_length=20)
    reason = models.TextField()

class Enquiry(models.Model):
    class Status(models.TextChoices):
        NEW = 'New', 'New'
        CONTACTED = 'Contacted', 'Contacted'
        INTERESTED = 'Interested', 'Interested'
        NOT_INTERESTED = 'Not Interested', 'Not Interested'
        CONVERTED = 'Converted', 'Converted'
    
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    course_interested = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    
    # Additional fields
    age = models.IntegerField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], blank=True, null=True)
    qualification = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.full_name

class Candidate(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'Active', 'Active'
        PENDING = 'Pending', 'Pending'
        INACTIVE = 'Inactive', 'Inactive'
    
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    personal_email = models.EmailField()
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True)
    designation = models.CharField(max_length=100, blank=True, null=True)
    fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=20, choices=[('Paid', 'Paid'), ('Pending', 'Pending')], default='Pending')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    
    # Additional fields
    age = models.IntegerField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.full_name

class Eligibility(models.Model):
    class Status(models.TextChoices):
        PENDING = 'Pending', 'Pending'
        ELIGIBLE = 'Eligible', 'Eligible'
        NOT_ELIGIBLE = 'Not Eligible', 'Not Eligible'
    
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    education = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    reason = models.TextField(blank=True, null=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    is_auto_eligible = models.BooleanField(default=False)  # Track if auto-marked by age rule
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.candidate.full_name} - {self.status}"

class DocumentVerification(models.Model):
    class Status(models.TextChoices):
        PENDING = 'Pending', 'Pending'
        VERIFIED = 'Verified', 'Verified'
        REJECTED = 'Rejected', 'Rejected'
    
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    document_type = models.CharField(max_length=100)
    document_file = models.FileField(upload_to='documents/', null=True, blank=True)
    submitted_date = models.DateField(auto_now_add=True)
    verification_date = models.DateField(null=True, blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.candidate.full_name} - {self.document_type}"

class InterviewSchedule(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = 'Scheduled', 'Scheduled'
        PENDING = 'Pending', 'Pending'
        COMPLETED = 'Completed', 'Completed'
        CANCELLED = 'Cancelled', 'Cancelled'
    
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    interviewer = models.ForeignKey(Trainer, on_delete=models.SET_NULL, null=True)
    interview_date = models.DateField()
    interview_time = models.TimeField()
    location_link = models.CharField(max_length=500, blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.candidate.full_name} - {self.interview_date}"
