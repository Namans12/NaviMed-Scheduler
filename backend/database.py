from sqlmodel import SQLModel, create_engine, Session
from typing import Generator
import os

# Database URL - using SQLite for development
DATABASE_URL = "sqlite:///./patient_scheduling.db"

# Create engine
engine = create_engine(
    DATABASE_URL, 
    echo=True,  # Set to False in production
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

def create_db_and_tables():
    """Create database and tables"""
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    """Dependency to get database session"""
    with Session(engine) as session:
        yield session

# Initialize database on import
def init_db():
    """Initialize database with minimal essential data and clear queue"""
    create_db_and_tables()
    
    # Clear all existing data except admin user
    clear_all_data_except_admin()
    
    # Only create admin user if it doesn't exist
    from models import User
    from crud import get_user_by_email, create_user
    
    with Session(engine) as session:
        # Create default admin user only
        admin_user = get_user_by_email(session, "admin@navimed.com")
        if not admin_user:
            create_user(session, "admin@navimed.com", "admin123", "System Administrator", "admin")
            print("Default admin user created: admin@navimed.com / admin123")
        
        print("Database initialized with minimal data - Queue cleared!")

def clear_all_data_except_admin():
    """Clear all patients, appointments, and queue data except admin user"""
    from models import Patient, Appointment, Doctor, TimeSlot
    from sqlmodel import select
    
    with Session(engine) as session:
        try:
            # Clear all patients
            patients = session.exec(select(Patient)).all()
            for patient in patients:
                session.delete(patient)
            
            # Clear all appointments  
            appointments = session.exec(select(Appointment)).all()
            for appointment in appointments:
                session.delete(appointment)
            
            # Clear all doctors (optional - you can comment this out if you want to keep doctors)
            doctors = session.exec(select(Doctor)).all()
            for doctor in doctors:
                session.delete(doctor)
            
            # Clear all time slots
            time_slots = session.exec(select(TimeSlot)).all()
            for time_slot in time_slots:
                session.delete(time_slot)
            
            session.commit()
            print("✅ Cleared all patients, appointments, and queue data")
            
        except Exception as e:
            session.rollback()
            print(f"❌ Error clearing data: {e}")
        finally:
            session.close() 