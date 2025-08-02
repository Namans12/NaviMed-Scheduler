import numpy as np
import pandas as pd
from datetime import datetime, date, time, timedelta
from typing import List, Dict, Tuple, Optional
from stable_baselines3 import PPO
from rl_env import PatientSchedulingEnv
from models import Patient, Doctor, Appointment, PriorityLevel, AppointmentType
from crud import get_patient, get_doctor, get_available_slots, get_patient_no_show_probability
from sqlalchemy import select

APPOINTMENT_TYPE_MAP = {
    "CONSULTATION": 0,
    "FOLLOW_UP": 1,
    "EMERGENCY": 2,
    "SPECIALIST": 3
}
SPECIALTY_MAP = {
    "GENERAL": 0,
    "CARDIOLOGY": 1,
    "ONCOLOGY": 2
}

class RLService:
    """Service for RL-based patient scheduling"""
    def __init__(self, model_path: str = "ppo_patient_scheduler.zip"):
        try:
            self.model = PPO.load(model_path)
            print(f"RL model loaded from {model_path}")
        except Exception as e:
            print(f"Error loading RL model: {e}")
            self.model = None
        self.env = PatientSchedulingEnv()

    def get_scheduling_recommendation(
        self,
        session,
        patient_id: int,
        appointment_type: str,  # Changed from AppointmentType to str
        priority: str,         # Changed from PriorityLevel to str
        preferred_date: Optional[date] = None,
        emergency: bool = False
    ) -> Dict:
        try:
            # Get available slots for the next 30 days (expanded window)
            start_date = preferred_date or datetime.now().date()
            end_date = start_date + timedelta(days=30)
            
            # Get doctor availability
            doctors = session.exec(select(Doctor)).all()
            if not doctors:
                return {
                    'status': 'error',
                    'message': 'No doctors available',
                    'available_slots': []
                }
            
            # Get current appointments
            # Ensure Appointment.appointment_date is a date, not str
            appointments = session.exec(
                select(Appointment)
            ).all()
            # Filter appointments by date range
            appointments = [apt for apt in appointments if isinstance(apt.appointment_date, date) and start_date <= apt.appointment_date <= end_date]
            
            # Get patient info for risk assessment
            patient = session.get(Patient, patient_id)
            if not patient:
                return {
                    'status': 'error',
                    'message': 'Patient not found',
                    'available_slots': []
                }
            
            # Calculate no-show probability
            no_show_prob = get_patient_no_show_probability(patient_id)
            
            # Generate available slots
            available_slots = []
            current_date = start_date
            while current_date <= end_date:
                for doctor in doctors:
                    # Parse working hours (support both HH:MM and HH:MM:SS)
                    def parse_time(tstr, default):
                        if tstr is None:
                            return default
                        try:
                            return datetime.strptime(str(tstr), '%H:%M').time()
                        except ValueError:
                            try:
                                return datetime.strptime(str(tstr), '%H:%M:%S').time()
                            except Exception:
                                return default
                    # Use default working hours if missing
                    default_start = time(9, 0)
                    default_end = time(17, 0)
                    start_time = parse_time(getattr(doctor, 'working_hours_start', None), default_start)
                    end_time = parse_time(getattr(doctor, 'working_hours_end', None), default_end)
                    current_datetime = datetime.combine(current_date, start_time)
                    end_datetime = datetime.combine(current_date, end_time)
                    while current_datetime < end_datetime:
                        # Check if slot is available
                        slot_taken = any(
                            apt.appointment_date == current_date and
                            apt.appointment_time == current_datetime.time()
                            for apt in appointments
                        )
                        
                        if not slot_taken:
                            slot_score = self._calculate_slot_score(
                                current_datetime,
                                doctor,
                                patient,
                                no_show_prob,
                                priority,
                                emergency
                            )
                            
                            available_slots.append({
                                'datetime': current_datetime.isoformat(),
                                'doctor_id': doctor.id,
                                'doctor_name': doctor.name,
                                'score': slot_score,
                                'specialty': doctor.specialty
                            })
                        
                        current_datetime += timedelta(minutes=30)  # 30-minute slots
                current_date += timedelta(days=1)
            
            print(f"[DEBUG] Found {len(available_slots)} available slots for patient {patient_id}")
            # Sort slots by score
            available_slots.sort(key=lambda x: x['score'], reverse=True)
            
            return {
                'status': 'success',
                'message': 'Recommendations generated successfully',
                'patient_risk_level': 'high' if no_show_prob > 0.5 else 'medium' if no_show_prob > 0.3 else 'low',
                'available_slots': available_slots[:5],  # Return top 5 recommendations
                'emergency_slots_available': any(slot['score'] > 0.8 for slot in available_slots)
            }
            
        except Exception as e:
            print(f"Error in scheduling recommendation: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'available_slots': []
            }

    def _get_current_clinic_state(self, session, target_date: date) -> Dict:
        from crud import get_doctor
        doctors = session.exec(select(Doctor)).all()
        # Get appointments for the target date
        appointments = session.exec(select(Appointment)).all()
        appointments = [apt for apt in appointments if apt.appointment_date == target_date]
        doctor_availability = []
        doctor_slots = []
        n_slots = self.env.n_slots
        for doctor in doctors:
            doctor_appointments = [apt for apt in appointments if apt.doctor_id == doctor.id]
            slots = np.ones(n_slots)
            for apt in doctor_appointments:
                # Use appointment_time for slot index
                if hasattr(apt, 'appointment_time') and apt.appointment_time:
                    slot_idx = min(int((apt.appointment_time.hour * 60 + apt.appointment_time.minute) / (8*60/n_slots)), n_slots-1)
                    slots[slot_idx] = 0
            workload = len([apt for apt in doctor_appointments if apt.status == "scheduled"])
            specialty_val = doctor.specialty if isinstance(doctor.specialty, str) else getattr(doctor.specialty, 'value', 'GENERAL')
            doctor_availability.append({
                'id': doctor.id,
                'specialty': SPECIALTY_MAP.get(specialty_val, 0),
                'emergency_capable': getattr(doctor, 'emergency_capable', False),
                'available': workload < getattr(doctor, 'max_patients_per_day', 10),
                'current_workload': workload,
                'max_patients': getattr(doctor, 'max_patients_per_day', 10)
            })
            doctor_slots.append(slots)
        patient_queue = []
        return {
            'patient_queue': patient_queue,
            'doctor_availability': doctor_availability,
            'doctor_slots': doctor_slots,
            'current_time': datetime.now(),
            'emergency_flag': False
        }

    def _create_patient_request(
        self,
        session,
        patient_id: int,
        appointment_type: AppointmentType,
        priority: PriorityLevel,
        emergency: bool
    ) -> Dict:
        patient = get_patient(session, patient_id)
        if not patient:
            raise ValueError(f"Patient with ID {patient_id} not found")
        priority_scores = {
            PriorityLevel.LOW: 0,
            PriorityLevel.MEDIUM: 1,
            PriorityLevel.HIGH: 2,
            PriorityLevel.EMERGENCY: 3
        }
        no_show_prob = get_patient_no_show_probability(patient_id)
        return {
            'id': patient_id,
            'priority': priority_scores[priority],
            'appointment_type': APPOINTMENT_TYPE_MAP.get(appointment_type.value, 0),
            'no_show_prob': no_show_prob,
            'emergency': emergency,
            'wait_time': 0,
            'age': patient.age,
            'gender': patient.gender
        }

    def _get_rl_recommendation(self, clinic_state: Dict):
        try:
            if self.model is None:
                return self._fallback_recommendation(clinic_state), 0.5
            obs = self._state_to_observation(clinic_state)
            action, _states = self.model.predict(obs, deterministic=False)
            # Compute confidence from model's action probability distribution
            confidence = 0.8
            try:
                if hasattr(self.model, 'policy') and hasattr(self.model.policy, 'get_distribution'):
                    import torch
                    obs_tensor = torch.tensor(obs, dtype=torch.float32).unsqueeze(0)
                    dist = self.model.policy.get_distribution(obs_tensor)
                    # Safely extract action probabilities if available
                    action_probs = None
                    if hasattr(dist, 'distribution'):
                        distribution = dist.distribution
                        probs = getattr(distribution, 'probs', None)
                        if probs is not None:
                            action_probs = probs.detach().cpu().numpy()
                            confidence = float(np.max(action_probs))
            except Exception:
                pass
            recommendation = self._interpret_action(clinic_state, action)
            return recommendation, confidence
        except Exception as e:
            print(f"Error getting RL recommendation: {e}")
            return self._fallback_recommendation(clinic_state), 0.5

    def _state_to_observation(self, clinic_state: Dict) -> np.ndarray:
        # This should match the new env observation
        pq = np.zeros((self.env.max_queue, 5))
        for i, p in enumerate(clinic_state['patient_queue'][:self.env.max_queue]):
            pq[i, 0] = p.get('priority', 0)
            pq[i, 1] = p.get('wait_time', 0)
            pq[i, 2] = p.get('appointment_type', 0)
            pq[i, 3] = p.get('no_show_prob', 0)
            pq[i, 4] = 1 if p.get('emergency', False) else 0
        ds = np.zeros((self.env.n_doctors, 3 + self.env.n_slots))
        for i, d in enumerate(clinic_state['doctor_availability']):
            ds[i, 0] = 1 if d.get('available', 1) else 0
            ds[i, 1] = d.get('specialty', 0)
            ds[i, 2] = 1 if d.get('emergency_capable', 0) else 0
            ds[i, 3:3+self.env.n_slots] = clinic_state['doctor_slots'][i]
        obs = np.concatenate([
            pq.flatten(),
            ds.flatten(),
            [clinic_state['current_time'].hour / 24.0],
            [1.0 if clinic_state['emergency_flag'] else 0.0]
        ])
        return obs.astype(np.float32)

    def _interpret_action(self, clinic_state: Dict, action: np.ndarray) -> Dict:
        patient_idx, doctor_idx, slot_idx, action_type = action
        
        # Ensure indices are within bounds
        patient_idx = min(int(patient_idx), len(clinic_state['patient_queue']) - 1) if clinic_state['patient_queue'] else 0
        doctor_idx = min(int(doctor_idx), len(clinic_state['doctor_availability']) - 1) if clinic_state['doctor_availability'] else 0
        slot_idx = min(int(slot_idx), self.env.n_slots - 1)
        
        if action_type == 0:  # Assign
            if (patient_idx < len(clinic_state['patient_queue']) and 
                doctor_idx < len(clinic_state['doctor_availability']) and
                clinic_state['patient_queue'] and clinic_state['doctor_availability']):
                patient = clinic_state['patient_queue'][patient_idx]
                doctor = clinic_state['doctor_availability'][doctor_idx]
                return {
                    'action': 'assign',
                    'patient_id': patient['id'],
                    'doctor_id': doctor['id'],
                    'slot_idx': slot_idx,
                    'reasoning': f"Assign patient {patient['id']} to doctor {doctor['id']} at slot {slot_idx}"
                }
        elif action_type == 1:  # Defer
            return {
                'action': 'defer',
                'patient_id': clinic_state['patient_queue'][patient_idx]['id'] if (clinic_state['patient_queue'] and patient_idx < len(clinic_state['patient_queue'])) else None,
                'reasoning': "Defer patient to later slot"
            }
        elif action_type == 2:  # Preempt
            return {
                'action': 'preempt',
                'patient_id': clinic_state['patient_queue'][patient_idx]['id'] if (clinic_state['patient_queue'] and patient_idx < len(clinic_state['patient_queue'])) else None,
                'doctor_id': clinic_state['doctor_availability'][doctor_idx]['id'] if (clinic_state['doctor_availability'] and doctor_idx < len(clinic_state['doctor_availability'])) else None,
                'slot_idx': slot_idx,
                'reasoning': "Preempt for emergency"
            }
        return {
            'action': 'unknown',
            'reasoning': "No clear action recommended"
        }

    def _generate_reasoning(self, clinic_state: Dict, recommendation: Dict) -> str:
        if recommendation['action'] == 'assign':
            return f"RL model recommends assigning patient to doctor {recommendation['doctor_id']} at slot {recommendation['slot_idx']} based on current clinic state and optimization goals."
        elif recommendation['action'] == 'defer':
            return "RL model suggests deferring this appointment to optimize overall clinic efficiency."
        elif recommendation['action'] == 'preempt':
            return "RL model recommends preempting current schedule for emergency handling."
        else:
            return "No specific recommendation available."

    def _get_alternative_slots(self, clinic_state: Dict) -> List[datetime]:
        # Placeholder - would calculate based on doctor availability
        return []

    def _fallback_recommendation(self, clinic_state: Dict) -> Dict:
        available_doctors = [d for d in clinic_state['doctor_availability'] if d['available']]
        if available_doctors:
            doctor = available_doctors[0]
            return {
                'action': 'assign',
                'doctor_id': doctor['id'],
                'reasoning': 'Fallback: Assign to first available doctor'
            }
        return {
            'action': 'defer',
            'reasoning': 'No doctors available'
        }

    def _fallback_scheduling(
        self,
        session,
        patient_id: int,
        appointment_type: AppointmentType,
        priority: PriorityLevel,
        preferred_date: Optional[date] = None,
        emergency: bool = False
    ) -> Dict:
        # Fallback: assign to any available doctor
        doctors = session.exec(select(Doctor)).all()
        if emergency:
            doctors = [doc for doc in doctors if getattr(doc, 'emergency_capable', False)]
        if doctors:
            doctor = doctors[0]
            recommended_action = {
                'action': 'assign',
                'doctor_id': doctor.id,
                'reasoning': f'Fallback: Assign to {doctor.specialty} doctor'
            }
        else:
            recommended_action = {
                'action': 'defer',
                'reasoning': 'No suitable doctors available'
            }
        return {
            'recommended_action': recommended_action,
            'confidence_score': 0.5,
            'reasoning': recommended_action['reasoning'],
            'alternative_slots': []
        }

    def _calculate_slot_score(
        self,
        slot_datetime: datetime,
        doctor: Doctor,
        patient: Patient,
        no_show_probability: float,
        priority: str,
        emergency: bool
    ) -> float:
        """Calculate a score for a given slot based on various factors"""
        score = 0.0
        
        # Base score
        score += 0.5
        
        # Priority boost
        if priority == 'high':
            score += 0.2
        elif priority == 'medium':
            score += 0.1
            
        # Emergency boost
        if emergency:
            score += 0.3
            
        # Doctor specialty match
        if patient.conditions and any(cond.lower() in doctor.specialty.lower() for cond in patient.conditions.split(',')):
            score += 0.2
            
        # Preferred time (assume business hours are preferred)
        hour = slot_datetime.hour
        if 9 <= hour <= 16:  # Core business hours
            score += 0.1
            
        # No-show risk penalty
        score -= no_show_probability * 0.2
        
        # Doctor rating boost
        if doctor.rating:
            score += (doctor.rating / 5.0) * 0.1
            
        # Experience boost
        if doctor.experience_years:
            score += min(doctor.experience_years / 20.0, 1.0) * 0.1
            
        # Emergency capability boost for urgent cases
        if emergency and doctor.emergency_capable:
            score += 0.2
            
        # Normalize score to 0-1 range
        return max(0.0, min(1.0, score)) 