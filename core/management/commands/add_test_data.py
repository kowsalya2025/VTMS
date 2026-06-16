from django.core.management.base import BaseCommand
from core.models import User, Trainer, Course, Batch, Trainee, Report, Intern
from datetime import date, time

class Command(BaseCommand):
    help = 'Adds test data to the database'

    def handle(self, *args, **options):
        # Add Courses
        course1, _ = Course.objects.get_or_create(title='Python Full Stack Development', status='Active')
        course2, _ = Course.objects.get_or_create(title='UI/UX Design', status='Active')
        course3, _ = Course.objects.get_or_create(title='Data Analytics', status='Active')
        
        # Add Trainers
        user1, _ = User.objects.get_or_create(email='meena@vtms.com', role=User.Role.TRAINER)
        trainer1, _ = Trainer.objects.get_or_create(
            user=user1,
            full_name='Meena',
            office_mail='meena@vtms.com',
            personal_mail='meena.personal@gmail.com',
            phone_no='9876543210',
            gender='Female',
            course=course2,
            status='Active'
        )
        
        user2, _ = User.objects.get_or_create(email='rahul@vtms.com', role=User.Role.TRAINER)
        trainer2, _ = Trainer.objects.get_or_create(
            user=user2,
            full_name='Rahul',
            office_mail='rahul@vtms.com',
            personal_mail='rahul.personal@gmail.com',
            phone_no='9876543211',
            gender='Male',
            course=course1,
            status='Active'
        )
        
        user3, _ = User.objects.get_or_create(email='karthik@vtms.com', role=User.Role.TRAINER)
        trainer3, _ = Trainer.objects.get_or_create(
            user=user3,
            full_name='Karthik',
            office_mail='karthik@vtms.com',
            personal_mail='karthik.personal@gmail.com',
            phone_no='9876543212',
            gender='Male',
            course=course3,
            status='Active'
        )
        
        # Add Batches
        batch1, _ = Batch.objects.get_or_create(
            batch_name='UI/UX Design - Batch 1',
            course=course2,
            trainer=trainer1,
            start_date=date(2026, 6, 1),
            end_date=date(2026, 9, 1),
            duration='3 Months',
            timing_start=time(10, 0),
            timing_end=time(12, 0),
            days='Mon,Tue,Wed,Thu,Fri',
            status='Active'
        )
        
        batch2, _ = Batch.objects.get_or_create(
            batch_name='Python Full Stack - Batch 1',
            course=course1,
            trainer=trainer2,
            start_date=date(2026, 6, 1),
            end_date=date(2026, 9, 1),
            duration='3 Months',
            timing_start=time(14, 0),
            timing_end=time(16, 0),
            days='Mon,Tue,Wed,Thu,Fri',
            status='Active'
        )
        
        batch3, _ = Batch.objects.get_or_create(
            batch_name='Data Analytics - Batch 1',
            course=course3,
            trainer=trainer3,
            start_date=date(2026, 6, 1),
            end_date=date(2026, 9, 1),
            duration='3 Months',
            timing_start=time(10, 0),
            timing_end=time(12, 0),
            days='Mon,Tue,Wed,Thu,Fri',
            status='Active'
        )
        
        # Add Trainee
        trainee_user, _ = User.objects.get_or_create(email='rahul.trainee@gmail.com', role=User.Role.TRAINEE)
        Trainee.objects.get_or_create(
            user=trainee_user,
            full_name='Rahul Kumar',
            personal_mail='rahul.trainee@gmail.com',
            phone_no='9876543213',
            gender='Male',
            course=course1,
            batch=batch2,
            trainer=trainer2,
            first_installment_paid=True,
            office_mail='rahul.kumar@vetritechnology.in'
        )
        
        # Add Reports
        Report.objects.get_or_create(
            report_type=Report.ReportType.DAILY,
            batch=batch1,
            trainer=trainer1,
            date=date(2026, 6, 15),
            status='Pending'
        )
        Report.objects.get_or_create(
            report_type=Report.ReportType.WEEKLY,
            batch=batch2,
            trainer=trainer2,
            date=date(2026, 6, 10),
            status='Pending'
        )
        Report.objects.get_or_create(
            report_type=Report.ReportType.MONTHLY,
            batch=batch3,
            trainer=trainer3,
            date=date(2026, 6, 1),
            status='Pending'
        )
        
        # Add Intern
        intern_user, _ = User.objects.get_or_create(email='sneha.intern@gmail.com', role=User.Role.INTERN)
        Intern.objects.get_or_create(
            user=intern_user,
            full_name='Sneha Verma',
            personal_mail='sneha.intern@gmail.com',
            phone_no='9876543214',
            gender='Female',
            role='Junior UI/UX Designer',
            internship_period='1 Month',
            trainer=trainer1,
            status='Active'
        )
        
        self.stdout.write(self.style.SUCCESS('Test data added successfully!'))
