from datetime import date, timedelta, time
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from doctors.models import DoctorProfile, Slot
from appointments.models import Appointment, Prescription

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds database with realistic sample doctors, patients, slots, and appointments'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding MediConnect database..."))

        # 1. Create Sample Doctors
        doctors_data = [
            {
                "full_name": "Dr. Arun Kumar",
                "email": "arun.kumar@mediconnect.com",
                "password": "Password123!",
                "specialization": "Cardiologist",
                "qualification": "MBBS, MD (Cardiology), DM",
                "experience_years": 14,
                "hospital_location": "MediConnect Heart Institute, Mumbai",
                "about": "Senior Consultant Cardiologist specializing in interventional cardiology, coronary artery disease, heart failure management, and preventive heart health. Over 14 years of exemplary clinical outcomes.",
                "rating": 4.9,
                "reviews_count": 184,
                "consultation_fee": 800.00,
                "profile_image": "https://images.unsplash.com/photo-1622253692010-333f2da6031d?w=400&auto=format&fit=crop&q=80",
            },
            {
                "full_name": "Dr. Priya Sharma",
                "email": "priya.sharma@mediconnect.com",
                "password": "Password123!",
                "specialization": "Dermatologist",
                "qualification": "MBBS, MD (Dermatology & Venereology)",
                "experience_years": 9,
                "hospital_location": "MediConnect Skin & Aesthetics Center, Delhi",
                "about": "Distinguished dermatologist specializing in clinical skin health, inflammatory acne therapies, laser treatments, eczema, and pediatric dermatology.",
                "rating": 4.8,
                "reviews_count": 142,
                "consultation_fee": 650.00,
                "profile_image": "https://images.unsplash.com/photo-1594824813580-b21703e35198?w=400&auto=format&fit=crop&q=80",
            },
            {
                "full_name": "Dr. Rohan Mehta",
                "email": "rohan.mehta@mediconnect.com",
                "password": "Password123!",
                "specialization": "Neurologist",
                "qualification": "MBBS, MD, DM (Neurology)",
                "experience_years": 12,
                "hospital_location": "Neuro Care Super Specialty Hospital, Bangalore",
                "about": "Experienced neurologist with a focus on chronic migraines, neuropathic pain, epilepsy management, stroke recovery, and neuromuscular disorders.",
                "rating": 4.9,
                "reviews_count": 105,
                "consultation_fee": 900.00,
                "profile_image": "https://images.unsplash.com/photo-1537368910025-700350fe46c7?w=400&auto=format&fit=crop&q=80",
            },
            {
                "full_name": "Dr. Sneha Patel",
                "email": "sneha.patel@mediconnect.com",
                "password": "Password123!",
                "specialization": "Pediatrician",
                "qualification": "MBBS, MD (Pediatrics), DCH",
                "experience_years": 8,
                "hospital_location": "Rainbow Children's Health Center, Ahmedabad",
                "about": "Caring pediatrician dedicated to infant care, childhood vaccinations, developmental milestones, pediatric nutrition, and acute childhood illnesses.",
                "rating": 4.9,
                "reviews_count": 220,
                "consultation_fee": 550.00,
                "profile_image": "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=400&auto=format&fit=crop&q=80",
            },
            {
                "full_name": "Dr. Rajesh Verma",
                "email": "rajesh.verma@mediconnect.com",
                "password": "Password123!",
                "specialization": "Orthopedist",
                "qualification": "MBBS, MS (Orthopedics), M.Ch",
                "experience_years": 15,
                "hospital_location": "Apex Bone & Joint Hospital, Pune",
                "about": "Expert orthopedic surgeon specializing in knee and hip arthroplasty, sports injury rehabilitation, spine health, and arthroscopic surgery.",
                "rating": 4.7,
                "reviews_count": 168,
                "consultation_fee": 750.00,
                "profile_image": "https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=400&auto=format&fit=crop&q=80",
            },
            {
                "full_name": "Dr. Ananya Sen",
                "email": "ananya.sen@mediconnect.com",
                "password": "Password123!",
                "specialization": "General Physician",
                "qualification": "MBBS, MD (Internal Medicine)",
                "experience_years": 11,
                "hospital_location": "MediConnect Primary Health Hub, Kolkata",
                "about": "Compassionate internal medicine specialist focusing on metabolic syndrome, hypertension, preventative adult screenings, and overall wellness.",
                "rating": 4.8,
                "reviews_count": 195,
                "consultation_fee": 500.00,
                "profile_image": "https://images.unsplash.com/photo-1582750433449-648ed127bb54?w=400&auto=format&fit=crop&q=80",
            },
        ]

        created_doctors = []
        for d in doctors_data:
            user, created = User.objects.get_or_create(
                email=d["email"],
                defaults={
                    "full_name": d["full_name"],
                    "role": "doctor"
                }
            )
            user.set_password(d["password"])
            user.role = "doctor"
            user.save()

            doctor_profile, p_created = DoctorProfile.objects.update_or_create(
                user=user,
                defaults={
                    "specialization": d["specialization"],
                    "qualification": d["qualification"],
                    "experience_years": d["experience_years"],
                    "hospital_location": d["hospital_location"],
                    "about": d["about"],
                    "rating": d["rating"],
                    "reviews_count": d["reviews_count"],
                    "consultation_fee": d["consultation_fee"],
                    "profile_image": d["profile_image"],
                }
            )
            created_doctors.append(doctor_profile)
            self.stdout.write(self.style.SUCCESS(f"Doctor configured: {d['full_name']} ({d['specialization']})"))

        # 2. Create Sample Patients
        patients_data = [
            {
                "full_name": "John Doe",
                "email": "patient@mediconnect.com",
                "password": "Password123!",
            },
            {
                "full_name": "Sarah Jenkins",
                "email": "sarah.jenkins@mediconnect.com",
                "password": "Password123!",
            }
        ]

        created_patients = []
        for p in patients_data:
            p_user, _ = User.objects.get_or_create(
                email=p["email"],
                defaults={
                    "full_name": p["full_name"],
                    "role": "patient"
                }
            )
            p_user.set_password(p["password"])
            p_user.role = "patient"
            p_user.save()
            created_patients.append(p_user)
            self.stdout.write(self.style.SUCCESS(f"Patient configured: {p['full_name']} ({p['email']})"))

        # 3. Create Slots for each doctor for next 7 days
        today = date.today()
        slot_times = [
            time(9, 0),
            time(10, 0),
            time(11, 0),
            time(11, 30),
            time(14, 0),
            time(15, 0),
            time(16, 0),
            time(17, 0)
        ]

        total_slots = 0
        for doc in created_doctors:
            for day_offset in range(8):  # Today + 7 days
                slot_date = today + timedelta(days=day_offset)
                for t in slot_times:
                    slot, created = Slot.objects.get_or_create(
                        doctor=doc,
                        date=slot_date,
                        start_time=t,
                        defaults={"is_booked": False}
                    )
                    if created:
                        total_slots += 1

        self.stdout.write(self.style.SUCCESS(f"Created {total_slots} availability slots across doctors."))

        # 4. Create Sample Appointments for demo testing
        john_patient = created_patients[0]
        dr_arun = created_doctors[0]    # Cardiologist
        dr_priya = created_doctors[1]   # Dermatologist
        dr_rohan = created_doctors[2]   # Neurologist

        # A) Pending appointment for John with Dr. Arun tomorrow 10:00
        tomorrow = today + timedelta(days=1)
        apt1, _ = Appointment.objects.update_or_create(
            patient=john_patient,
            doctor=dr_arun,
            date=tomorrow,
            time=time(10, 0),
            defaults={"status": "pending"}
        )
        Slot.objects.filter(doctor=dr_arun, date=tomorrow, start_time=time(10, 0)).update(is_booked=True)

        # B) Accepted appointment for John with Dr. Priya in 2 days at 11:00
        in_two_days = today + timedelta(days=2)
        apt2, _ = Appointment.objects.update_or_create(
            patient=john_patient,
            doctor=dr_priya,
            date=in_two_days,
            time=time(11, 0),
            defaults={"status": "accepted"}
        )
        Slot.objects.filter(doctor=dr_priya, date=in_two_days, start_time=time(11, 0)).update(is_booked=True)

        # C) Completed appointment with Prescription for John with Dr. Rohan (yesterday or today at 09:00)
        yesterday = today - timedelta(days=1)
        apt3, _ = Appointment.objects.update_or_create(
            patient=john_patient,
            doctor=dr_rohan,
            date=yesterday,
            time=time(9, 0),
            defaults={"status": "completed"}
        )

        Prescription.objects.update_or_create(
            appointment=apt3,
            defaults={
                "medical_notes": "Patient reported recurrent tension headaches exacerbated by screen fatigue and irregular sleep cycles. Physical neurological examination was normal. Blood pressure recorded at 122/80 mmHg.",
                "prescription_text": (
                    "1. Tab. Naproxen 500mg - Take 1 tablet post-meals twice daily for 3 days as needed.\n"
                    "2. Tab. Magnesium Glycinate 200mg - Take 1 tablet at bedtime for 30 days.\n"
                    "3. Practice 20-20-20 ocular screen breaks and maintain 7+ hours of uninterrupted hydration and sleep.\n"
                    "4. Review consultation in 3 weeks if symptoms persist."
                )
            }
        )

        self.stdout.write(self.style.SUCCESS("Demo appointments and prescription created successfully!"))
        self.stdout.write(self.style.SUCCESS("All seed data created successfully!"))
