from django.db import models
from django.contrib.auth.models import AbstractUser

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

    def __str__(self):
        return self.email

class Course(models.Model):
    title = models.CharField(max_length=100)
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
    trainer = models.ForeignKey(Trainer, on_delete=models.SET_NULL, null=True)
    description = models.TextField(blank=True, null=True)
    
    start_date = models.DateField()
    end_date = models.DateField()
    duration = models.CharField(max_length=50) # e.g., "30 Days"
    
    timing_start = models.TimeField()
    timing_end = models.TimeField()
    days = models.CharField(max_length=100) # Storing comma separated e.g. "Mon,Tue,Wed"
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UPCOMING)

    def __str__(self):
        return self.batch_name

class Trainee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    office_mail = models.EmailField(blank=True, null=True)
    personal_mail = models.EmailField()
    phone_no = models.CharField(max_length=15)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')])
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True)
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, related_name='trainees')
    trainer = models.ForeignKey(Trainer, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=[('Active', 'Active'), ('Dropout', 'Dropout')], default='Active')
    progress = models.IntegerField(default=0) # percentage

    def __str__(self):
        return self.full_name

class Intern(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    office_mail = models.EmailField(blank=True, null=True)
    personal_mail = models.EmailField()
    phone_no = models.CharField(max_length=15)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')])
    role = models.CharField(max_length=50) # e.g. Junior Developer
    internship_period = models.CharField(max_length=20) # e.g. 1 Month, 2 Month
    trainer = models.ForeignKey(Trainer, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=[('Active', 'Active'), ('Completed', 'Completed')], default='Active')

    def __str__(self):
        return self.full_name

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
    status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Done', 'Done'), ('Approved', 'Approved')], default='Pending')
    content = models.TextField(blank=True, null=True)

class Payment(models.Model):
    trainee = models.ForeignKey(Trainee, on_delete=models.CASCADE, null=True, blank=True)
    intern = models.ForeignKey(Intern, on_delete=models.CASCADE, null=True, blank=True)
    course_amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pending = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[('Paid', 'Paid'), ('Pending', 'Pending')])
    date = models.DateField(auto_now_add=True)

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
