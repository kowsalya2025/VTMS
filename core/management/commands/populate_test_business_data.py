from django.core.management.base import BaseCommand
from core.models import User, Course, Trainer, Candidate, Enquiry, Eligibility, DocumentVerification, InterviewSchedule
from django.utils import timezone
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Populates test data for business dashboard pages'

    def handle(self, *args, **options):
        # Get or create courses
        course1, _ = Course.objects.get_or_create(title='Full Stack Development', status='Active')
        course2, _ = Course.objects.get_or_create(title='Data Science', status='Active')
        course3, _ = Course.objects.get_or_create(title='UI/UX Design', status='Active')
        
        # Get or create users for trainers
        user1, _ = User.objects.get_or_create(
            email='suresh@vtms.com',
            defaults={'role': User.Role.TRAINER, 'phone_no': '9876543210'}
        )
        user2, _ = User.objects.get_or_create(
            email='priya@vtms.com',
            defaults={'role': User.Role.TRAINER, 'phone_no': '8765432109'}
        )
        
        # Get or create trainers
        trainer1, _ = Trainer.objects.get_or_create(
            user=user1,
            defaults={
                'full_name': 'Suresh Kumar',
                'office_mail': 'suresh@vtms.com',
                'personal_mail': 'suresh.personal@gmail.com',
                'phone_no': '9876543210',
                'gender': 'Male',
                'course': course1,
                'status': 'Active'
            }
        )
        trainer2, _ = Trainer.objects.get_or_create(
            user=user2,
            defaults={
                'full_name': 'Priya Sharma',
                'office_mail': 'priya@vtms.com',
                'personal_mail': 'priya.personal@gmail.com',
                'phone_no': '8765432109',
                'gender': 'Female',
                'course': course2,
                'status': 'Active'
            }
        )
        
        # Create candidates
        candidates_data = [
            {'full_name': 'Arun Kumar', 'phone': '9876543210', 'personal_email': 'arun.kumar@email.com', 'course': course1, 'designation': 'Fresher', 'fees': 35000, 'payment_status': 'Pending', 'status': 'Active'},
            {'full_name': 'Priya Sharma', 'phone': '8765432109', 'personal_email': 'priya.sharma@email.com', 'course': course2, 'designation': 'Fresher', 'fees': 40000, 'payment_status': 'Paid', 'status': 'Active'},
            {'full_name': 'Lakshmi Nair', 'phone': '7654321098', 'personal_email': 'lakshmi.nair@email.com', 'course': course3, 'designation': 'Fresher', 'fees': 30000, 'payment_status': 'Paid', 'status': 'Active'},
            {'full_name': 'Arjun Verma', 'phone': '6543210987', 'personal_email': 'arjun.verma@email.com', 'course': course1, 'designation': 'Working Professional', 'fees': 35000, 'payment_status': 'Pending', 'status': 'Pending'},
        ]
        
        candidates = []
        for data in candidates_data:
            candidate, created = Candidate.objects.get_or_create(
                full_name=data['full_name'],
                defaults=data
            )
            candidates.append(candidate)
        
        # Create enquiries
        enquiries_data = [
            {'full_name': 'Rahul Gupta', 'email': 'rahul.gupta@email.com', 'phone': '9123456780', 'course_interested': course1, 'status': 'New', 'message': 'Interested in Full Stack course'},
            {'full_name': 'Anita Patel', 'email': 'anita.patel@email.com', 'phone': '9123456781', 'course_interested': course2, 'status': 'Contacted', 'message': 'Want to know more about Data Science'},
            {'full_name': 'Vikram Singh', 'email': 'vikram.singh@email.com', 'phone': '9123456782', 'course_interested': course3, 'status': 'Interested', 'message': 'Looking for UI/UX Design course'},
        ]
        
        for data in enquiries_data:
            Enquiry.objects.get_or_create(
                full_name=data['full_name'],
                defaults=data
            )
        
        # Create eligibility records
        eligibility_data = [
            {'candidate': candidates[0], 'education': 'B.Tech (CSE)', 'status': 'Pending'},
            {'candidate': candidates[1], 'education': 'M.Sc (CS)', 'status': 'Eligible'},
            {'candidate': candidates[2], 'education': 'B.Des', 'status': 'Not Eligible'},
            {'candidate': candidates[3], 'education': 'BCA', 'status': 'Pending'},
        ]
        
        for data in eligibility_data:
            Eligibility.objects.get_or_create(
                candidate=data['candidate'],
                defaults=data
            )
        
        # Create document verifications
        doc_data = [
            {'candidate': candidates[0], 'document_type': 'Aadhaar Card', 'status': 'Verified'},
            {'candidate': candidates[1], 'document_type': '10th Marksheet', 'status': 'Pending'},
            {'candidate': candidates[2], 'document_type': '12th Marksheet', 'status': 'Verified'},
            {'candidate': candidates[3], 'document_type': 'Graduation Certificate', 'status': 'Rejected'},
        ]
        
        for data in doc_data:
            DocumentVerification.objects.get_or_create(
                candidate=data['candidate'],
                document_type=data['document_type'],
                defaults=data
            )
        
        # Create interview schedules
        interview_data = [
            {'candidate': candidates[0], 'interviewer': trainer1, 'interview_date': timezone.now().date() + timedelta(days=1), 'interview_time': datetime.strptime('10:00', '%H:%M').time(), 'location_link': 'Zoom Link', 'status': 'Scheduled'},
            {'candidate': candidates[1], 'interviewer': trainer2, 'interview_date': timezone.now().date() + timedelta(days=2), 'interview_time': datetime.strptime('14:00', '%H:%M').time(), 'location_link': 'Conference Room', 'status': 'Pending'},
            {'candidate': candidates[2], 'interviewer': trainer1, 'interview_date': timezone.now().date() - timedelta(days=1), 'interview_time': datetime.strptime('11:00', '%H:%M').time(), 'location_link': 'Google Meet', 'status': 'Completed'},
        ]
        
        for data in interview_data:
            InterviewSchedule.objects.get_or_create(
                candidate=data['candidate'],
                interview_date=data['interview_date'],
                defaults=data
            )
        
        self.stdout.write(self.style.SUCCESS('Successfully populated test data for business dashboard!'))
