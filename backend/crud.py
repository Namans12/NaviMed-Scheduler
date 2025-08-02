from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime, date, time
from models import (
    Patient, Doctor, Appointment, TimeSlot, User,
    PatientCreate, DoctorCreate, AppointmentRequest,
    PriorityLevel, AppointmentType, DoctorSpecialty
)

# User CRUD operations
def create_user(db: Session, email: str, password: str, name: str, role: str) -> User:
    """Create a new user"""
    db_user = User(
        email=email,
        password=password,  # In production, hash this password
        name=name,
        role=role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email"""
    return db.exec(select(User).where(User.email == email)).first()

def get_users(db: Session) -> List[User]:
    """Get all users"""
    return db.exec(select(User)).all()

# Patient CRUD operations
def create_patient(db: Session, patient: PatientCreate) -> Patient:
    """Create a new patient"""
    db_patient = Patient(**patient.dict())
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient

def get_patient(db: Session, patient_id: int) -> Optional[Patient]:
    """Get patient by ID"""
    return db.get(Patient, patient_id)

def get_patients(db: Session, skip: int = 0, limit: int = 100) -> List[Patient]:
    """Get all patients with pagination"""
    return db.exec(select(Patient).offset(skip).limit(limit)).all()

def update_patient(db: Session, patient_id: int, patient_update: dict) -> Optional[Patient]:
    """Update patient information"""
    db_patient = db.get(Patient, patient_id)
    if db_patient:
        for key, value in patient_update.items():
            if hasattr(db_patient, key):
                setattr(db_patient, key, value)
        db.commit()
        db.refresh(db_patient)
    return db_patient

def delete_patient(db: Session, patient_id: int) -> bool:
    """Delete patient"""
    db_patient = db.get(Patient, patient_id)
    if db_patient:
        db.delete(db_patient)
        db.commit()
        return True
    return False

# Doctor CRUD operations
def create_doctor(db: Session, doctor: DoctorCreate) -> Doctor:
    """Create a new doctor"""
    db_doctor = Doctor(**doctor.dict())
    db.add(db_doctor)
    db.commit()
    db.refresh(db_doctor)
    return db_doctor

def get_doctor(db: Session, doctor_id: int) -> Optional[Doctor]:
    """Get doctor by ID"""
    return db.get(Doctor, doctor_id)

def get_doctors(db: Session, skip: int = 0, limit: int = 100) -> List[Doctor]:
    """Get all doctors with pagination"""
    return db.exec(select(Doctor).offset(skip).limit(limit)).all()

def get_available_doctors(db: Session, specialty: Optional[str] = None) -> List[Doctor]:
    """Get available doctors, optionally filtered by specialty"""
    query = select(Doctor).where(Doctor.is_active == True)
    if specialty:
        query = query.where(Doctor.specialty == specialty)
    return db.exec(query).all()

def update_doctor(db: Session, doctor_id: int, doctor_update: dict) -> Optional[Doctor]:
    """Update doctor information"""
    db_doctor = db.get(Doctor, doctor_id)
    if db_doctor:
        for key, value in doctor_update.items():
            if hasattr(db_doctor, key):
                setattr(db_doctor, key, value)
        db.commit()
        db.refresh(db_doctor)
    return db_doctor

# Appointment CRUD operations
def create_appointment(db: Session, appointment_data: dict) -> Appointment:
    """Create a new appointment"""
    db_appointment = Appointment(**appointment_data)
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    return db_appointment

def get_appointment(db: Session, appointment_id: int) -> Optional[Appointment]:
    """Get appointment by ID"""
    return db.get(Appointment, appointment_id)

def get_appointments(db: Session, skip: int = 0, limit: int = 100) -> List[Appointment]:
    """Get all appointments with pagination"""
    return db.exec(select(Appointment).offset(skip).limit(limit)).all()

def get_patient_appointments(db: Session, patient_id: int) -> List[Appointment]:
    """Get all appointments for a specific patient"""
    return db.exec(select(Appointment).where(Appointment.patient_id == patient_id)).all()

def get_doctor_appointments(db: Session, doctor_id: int, date_filter: Optional[date] = None) -> List[Appointment]:
    """Get all appointments for a specific doctor, optionally filtered by date"""
    query = select(Appointment).where(Appointment.doctor_id == doctor_id)
    if date_filter:
        query = query.where(Appointment.appointment_date == date_filter)
    return db.exec(query).all()

def update_appointment(db: Session, appointment_id: int, appointment_update: dict) -> Optional[Appointment]:
    """Update appointment information"""
    db_appointment = db.get(Appointment, appointment_id)
    if db_appointment:
        for key, value in appointment_update.items():
            if hasattr(db_appointment, key):
                setattr(db_appointment, key, value)
        db_appointment.updated_at = datetime.now()
        db.commit()
        db.refresh(db_appointment)
    return db_appointment

def delete_appointment(db: Session, appointment_id: int) -> bool:
    """Delete appointment"""
    db_appointment = db.get(Appointment, appointment_id)
    if db_appointment:
        db.delete(db_appointment)
        db.commit()
        return True
    return False

# Time slot management
def get_available_slots(db: Session, doctor_id: int, target_date: date) -> List[TimeSlot]:
    """Get available time slots for a doctor on a specific date"""
    return db.exec(
        select(TimeSlot).where(
            TimeSlot.doctor_id == doctor_id,
            TimeSlot.slot_date == target_date,
            TimeSlot.is_available == True
        )
    ).all()

def book_slot(db: Session, slot_id: int, appointment_id: int) -> bool:
    """Book a time slot for an appointment"""
    slot = db.get(TimeSlot, slot_id)
    if slot and slot.is_available:
        slot.is_available = False
        slot.appointment_id = appointment_id
        db.commit()
        return True
    return False

def release_slot(db: Session, slot_id: int) -> bool:
    """Release a booked time slot"""
    slot = db.get(TimeSlot, slot_id)
    if slot:
        slot.is_available = True
        slot.appointment_id = None
        db.commit()
        return True
    return False

# Analytics and reporting
def get_patient_no_show_probability(patient_id: int) -> float:
    """Calculate no-show probability for a patient"""
    # Mock implementation - in real app, this would use ML model
    return 0.15  # 15% default no-show probability

def get_appointment_statistics(db: Session) -> dict:
    """Get appointment statistics"""
    total_appointments = len(db.exec(select(Appointment)).all())
    completed_appointments = len(db.exec(select(Appointment).where(Appointment.status == "completed")).all())
    no_show_appointments = len(db.exec(select(Appointment).where(Appointment.status == "no_show")).all())
    
    return {
        "total_appointments": total_appointments,
        "completed_appointments": completed_appointments,
        "no_show_appointments": no_show_appointments,
        "completion_rate": (completed_appointments / total_appointments) * 100 if total_appointments > 0 else 0,
        "no_show_rate": (no_show_appointments / total_appointments) * 100 if total_appointments > 0 else 0
    } 