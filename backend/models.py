from typing import Optional, List
from datetime import datetime, time
from pydantic import BaseModel, Field
from sqlmodel import SQLModel, Field as SQLField
from enum import Enum

# Enums
class PriorityLevel(str, Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"  # Keep for backward compatibility

# Priority ranking for proper queue sorting (higher number = higher priority)
PRIORITY_RANKING = {
    PriorityLevel.CRITICAL: 7,
    PriorityLevel.EMERGENCY: 7,  # Same as CRITICAL for backward compatibility
    PriorityLevel.VERY_HIGH: 5,
    PriorityLevel.HIGH: 4,
    PriorityLevel.MEDIUM: 3,
    PriorityLevel.LOW: 2,
    PriorityLevel.VERY_LOW: 1
}

# Helper function to get priority score for sorting
def get_priority_score(priority: str) -> int:
    """Convert priority string to numerical score for sorting"""
    if isinstance(priority, str):
        # Try to match the priority string to PriorityLevel enum values
        for level in PriorityLevel:
            if level.value == priority.lower():
                return PRIORITY_RANKING.get(level, 3)
        return 3  # Default to medium priority if not found
    return int(priority) if isinstance(priority, (int, float)) else 3  # Backward compatibility

class AppointmentType(str, Enum):
    GENERAL_CHECKUP = "general_checkup"
    FOLLOWUP = "followup"
    DIAGNOSTICS = "diagnostics"
    CONSULTATION_ROUTINE = "consultation_routine"
    CONSULTATION_URGENT = "consultation_urgent"
    EMERGENCY = "emergency"
    # Legacy types for backward compatibility
    CONSULTATION = "consultation"
    FOLLOW_UP = "follow_up"
    SPECIALIST = "specialist"

class DoctorSpecialty(str, Enum):
    GENERAL = "general"
    CARDIOLOGY = "cardiology"
    ONCOLOGY = "oncology"
    PEDIATRICS = "pediatrics"
    EMERGENCY = "emergency"

# Database Models
class User(SQLModel, table=True):
    id: Optional[int] = SQLField(default=None, primary_key=True)
    email: str = SQLField(unique=True)
    password: str
    name: str
    role: str  # patient, doctor, admin
    is_active: bool = SQLField(default=True)
    created_at: datetime = SQLField(default_factory=datetime.now)

class Patient(SQLModel, table=True):
    id: Optional[int] = SQLField(default=None, primary_key=True)
    name: str
    age: int
    gender: str
    phone: str
    email: Optional[str] = None
    address: Optional[str] = None
    date_of_birth: Optional[str] = None
    emergency_contact: Optional[str] = None
    blood_type: Optional[str] = None
    allergies: Optional[str] = None
    conditions: Optional[str] = None
    medications: Optional[str] = None
    last_visit: Optional[datetime] = None
    next_appointment: Optional[datetime] = None
    status: str = SQLField(default="active")
    risk_level: str = SQLField(default="low")
    insurance: Optional[str] = None
    primary_doctor: Optional[str] = None
    notes: Optional[str] = None
    medical_history: Optional[str] = None
    no_show_probability: float = SQLField(default=0.0)
    created_at: datetime = SQLField(default_factory=datetime.now)

class Doctor(SQLModel, table=True):
    id: Optional[int] = SQLField(default=None, primary_key=True)
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    specialty: str = SQLField(default="general")
    department: Optional[str] = None
    availability: Optional[str] = None
    rating: float = SQLField(default=4.5)
    experience_years: int = SQLField(default=5)
    emergency_capable: bool = SQLField(default=False)
    max_patients_per_day: int = SQLField(default=20)
    working_hours_start: time = SQLField(default=time(9, 0))
    working_hours_end: time = SQLField(default=time(17, 0))
    is_active: bool = SQLField(default=True)

class Appointment(SQLModel, table=True):
    id: Optional[int] = SQLField(default=None, primary_key=True)
    patient_id: int = SQLField(foreign_key="patient.id")
    doctor_id: int = SQLField(foreign_key="doctor.id")
    appointment_date: str  # Store as string for consistency
    appointment_time: str  # Store as string for consistency
    appointment_type: str = SQLField(default="consultation")
    priority: str = SQLField(default="medium")
    status: str = SQLField(default="scheduled")  # scheduled, completed, cancelled, no_show
    duration: Optional[int] = SQLField(default=30)  # Duration in minutes
    notes: Optional[str] = None
    symptoms: Optional[str] = None
    diagnosis: Optional[str] = None
    treatment: Optional[str] = None
    follow_up_date: Optional[str] = None
    created_at: datetime = SQLField(default_factory=datetime.now)
    updated_at: datetime = SQLField(default_factory=datetime.now)

class TimeSlot(SQLModel, table=True):
    id: Optional[int] = SQLField(default=None, primary_key=True)
    doctor_id: int = SQLField(foreign_key="doctor.id")
    slot_date: datetime
    slot_time: time
    is_available: bool = SQLField(default=True)
    appointment_id: Optional[int] = SQLField(foreign_key="appointment.id", default=None)

# API Request/Response Models
class PatientCreate(BaseModel):
    name: str
    age: int
    gender: str
    phone: str
    email: Optional[str] = None
    address: Optional[str] = None
    medical_history: Optional[str] = None

class PatientResponse(BaseModel):
    id: int
    name: str
    age: int
    gender: str
    phone: str
    email: Optional[str] = None
    no_show_probability: float
    created_at: datetime

class DoctorCreate(BaseModel):
    name: str
    specialty: DoctorSpecialty
    emergency_capable: bool = False
    max_patients_per_day: int = 20
    working_hours_start: time = time(9, 0)
    working_hours_end: time = time(17, 0)

class DoctorResponse(BaseModel):
    id: int
    name: str
    specialty: DoctorSpecialty
    emergency_capable: bool
    max_patients_per_day: int
    working_hours_start: time
    working_hours_end: time
    is_active: bool

class AppointmentRequest(BaseModel):
    patient_id: int
    doctor_id: Optional[int] = None  # Optional for RL scheduling
    appointment_date: Optional[datetime] = None  # Use this instead of preferred_date
    preferred_date: Optional[datetime] = None  # Keep for compatibility
    appointment_type: AppointmentType
    priority: PriorityLevel = PriorityLevel.MEDIUM
    notes: Optional[str] = None
    emergency: bool = False

class AppointmentBookingRequest(BaseModel):
    patient_name: str
    patient_email: Optional[str] = ""
    patient_phone: Optional[str] = ""
    age: int = 25
    gender: Optional[str] = "Not specified"
    date_of_birth: Optional[str] = None
    appointment_type: AppointmentType = AppointmentType.CONSULTATION
    symptoms: Optional[str] = ""
    priority: PriorityLevel = PriorityLevel.MEDIUM
    is_emergency: bool = False
    preferred_doctor_id: Optional[int] = None
    notes: Optional[str] = ""

class AppointmentResponse(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    appointment_date: datetime
    appointment_type: AppointmentType
    priority: PriorityLevel
    status: str
    notes: Optional[str] = None
    created_at: datetime

class SchedulingRequest(BaseModel):
    patient_id: int
    appointment_type: AppointmentType
    priority: PriorityLevel = PriorityLevel.MEDIUM
    preferred_date: Optional[datetime] = None
    emergency: bool = False
    notes: Optional[str] = None

class SchedulingResponse(BaseModel):
    appointment_id: int
    doctor_id: int
    appointment_date: datetime
    confidence_score: float
    reasoning: str
    alternative_slots: List[datetime] = []

class RLStateRequest(BaseModel):
    patient_queue: List[dict]
    doctor_availability: List[dict]
    current_time: datetime
    emergency_flag: bool = False

class RLStateResponse(BaseModel):
    state_vector: List[float]
    available_actions: List[dict]
    recommended_action: dict
    confidence: float 