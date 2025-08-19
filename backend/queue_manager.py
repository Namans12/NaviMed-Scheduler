"""
Real-time Queue Management with RL-based prioritization
"""

import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from sqlmodel import Session, select
from models import Patient, Doctor, Appointment, get_priority_score
import logging

logger = logging.getLogger(__name__)

class PatientScorer:
    """Calculate patient priority scores for queue ordering"""
    
    @staticmethod
    def calculate_patient_score(patient: Patient, appointment_type: str, emergency: bool = False) -> float:
        """
        Calculate patient priority score based on multiple factors
        Higher score = higher priority
        """
        score = 0.0
        
        # Emergency cases get maximum priority
        if emergency:
            return 100.0
            
        # Risk level scoring (30% weight)
        risk_scores = {"high": 30, "medium": 20, "low": 10}
        score += risk_scores.get(patient.risk_level.lower(), 10)
        
        # Age-based priority (20% weight)
        if patient.age >= 65:
            score += 20  # Senior citizens
        elif patient.age <= 5:
            score += 15  # Young children
        elif patient.age <= 18:
            score += 10  # Minors
        
        # Condition severity (25% weight)
        if patient.conditions and patient.conditions.lower() != "none":
            chronic_conditions = ["diabetes", "hypertension", "heart", "cancer", "kidney", "liver"]
            if any(condition in patient.conditions.lower() for condition in chronic_conditions):
                score += 25
            else:
                score += 15
        
        # Appointment type priority (15% weight)
        type_scores = {
            "emergency": 15,
            "urgent": 12,
            "follow_up": 8,
            "consultation": 5,
            "checkup": 3
        }
        score += type_scores.get(appointment_type.lower(), 5)
        
        # Historical no-show penalty (10% weight)
        no_show_prob = getattr(patient, 'no_show_probability', 0.15)
        if no_show_prob > 0.3:
            score -= 10  # High no-show risk
        elif no_show_prob < 0.1:
            score += 5   # Reliable patient
            
        return max(score, 1.0)  # Minimum score of 1

class DynamicQueueManager:
    """Manages real-time queue ordering based on RL and scoring"""
    
    def __init__(self, rl_service):
        self.rl_service = rl_service
        self.scorer = PatientScorer()
        
    def calculate_queue_order(self, session: Session, appointment_queue: Optional[List] = None) -> List[Dict]:
        """
        Calculate optimal queue order using RL recommendations and patient scoring
        Preserves the first appointment in position 1
        Returns ordered list of patient queue items
        """
        try:
            # If appointment_queue is provided, use it to preserve first appointment
            first_appointment_patient_id = None
            if appointment_queue and len(appointment_queue) > 0:
                first_appointment_patient_id = appointment_queue[0].get('patient_id')
                print(f"DEBUG: Preserving first appointment for patient ID {first_appointment_patient_id}")
            
            # Get all patients with pending/waiting appointments
            patients = session.exec(select(Patient)).all()
            appointments = session.exec(select(Appointment)).all()
            
            # Find patients without scheduled appointments (waiting queue)
            scheduled_patient_ids = set(apt.patient_id for apt in appointments if apt.status == "scheduled")
            waiting_patients = [p for p in patients if p.id not in scheduled_patient_ids]
            
            # Calculate scores for waiting patients
            scored_patients = []
            first_appointment_item = None
            
            for patient in waiting_patients:
                # Default appointment type for queue calculation
                appointment_type = "consultation"
                is_emergency = False
                
                # Check if this patient exists in the appointment_queue to get emergency status
                if appointment_queue:
                    queue_patient = next((q for q in appointment_queue if q.get('patient_id') == patient.id), None)
                    if queue_patient:
                        appointment_type = queue_patient.get('appointment_type', appointment_type)
                        is_emergency = queue_patient.get('is_emergency', False)
                        print(f"DEBUG: Found patient {patient.name} in appointment_queue with is_emergency: {is_emergency}")
                
                # Check if there are any pending appointment requests for this patient
                pending_appointments = [apt for apt in appointments 
                                      if apt.patient_id == patient.id and apt.status == "pending"]
                if pending_appointments:
                    appointment_type = pending_appointments[0].appointment_type
                    # Check if appointment type indicates emergency
                    if appointment_type.lower() == "emergency":
                        is_emergency = True
                
                score = self.scorer.calculate_patient_score(patient, appointment_type, is_emergency)
                
                patient_item = {
                    "patient": patient,
                    "score": score,
                    "appointment_type": appointment_type,
                    "is_emergency": is_emergency,  # Add emergency status
                    "wait_time_minutes": self._calculate_wait_time(patient),
                    "rl_recommendation": None
                }
                
                # Check if this is the first appointment - preserve it
                if patient.id == first_appointment_patient_id:
                    first_appointment_item = patient_item
                    print(f"DEBUG: Found first appointment patient: {patient.name}")
                else:
                    scored_patients.append(patient_item)
            
            # Get RL recommendations for top patients (excluding first appointment)
            for item in scored_patients[:10]:  # Limit RL calls for performance
                try:
                    rl_rec = self.rl_service.get_scheduling_recommendation(
                        session=session,
                        patient_id=item["patient"].id,
                        appointment_type=item["appointment_type"],
                        priority=item["patient"].risk_level,
                        emergency=False
                    )
                    item["rl_recommendation"] = rl_rec
                    
                    # Boost score if RL finds urgent need
                    if rl_rec and rl_rec.get("urgency_boost"):
                        item["score"] += rl_rec.get("urgency_boost", 0)
                        
                except Exception as e:
                    logger.warning(f"RL recommendation failed for patient {item['patient'].id}: {e}")
            
            # Sort by combined score (RL + manual scoring) - but only for non-first appointments
            scored_patients.sort(key=lambda x: x["score"], reverse=True)
            
            # Format for API response
            queue_items = []
            
            # Define appointment type durations (in minutes)
            appointment_durations = {
                'general_checkup': 15,
                'followup': 12,
                'diagnostics': 30,
                'consultation_routine': 25,
                'consultation_urgent': 40,
                'emergency': 60,
                # Legacy mapping for backward compatibility
                'consultation': 25,
                'checkup': 15,
                'follow_up': 12,
                'urgent': 40
            }
            
            # Initialize cumulative waiting time
            cumulative_wait_time = 0
            
            print(f"DEBUG: Creating queue items with emergency status:")
            # Always put first appointment at position 1
            if first_appointment_item:
                patient = first_appointment_item["patient"]
                appointment_type = first_appointment_item["appointment_type"]
                is_emergency = first_appointment_item.get("is_emergency", False)
                appointment_duration = appointment_durations.get(appointment_type, 15)
                
                print(f"  First appointment: {patient.name} - Emergency: {is_emergency}")
                
                # Check if this is the only patient (current patient)
                total_patients = len(scored_patients) + 1
                is_only_patient = total_patients == 1
                
                queue_items.append({
                    "id": patient.id,
                    "name": patient.name,
                    "age": patient.age,
                    "conditions": patient.conditions,
                    "risk_level": patient.risk_level,
                    "score": round(first_appointment_item["score"], 2),
                    "queue_position": 1,
                    "estimated_wait_minutes": 0 if is_only_patient else appointment_duration,  # 0 if only patient
                    "appointment_duration": appointment_duration,
                    "appointment_type": first_appointment_item["appointment_type"],
                    "is_emergency": first_appointment_item.get("is_emergency", False),  # Add emergency status
                    "status": "waiting",
                    "priority_reason": "First appointment - no reordering",
                    "rl_optimized": False  # First appointment is not RL optimized
                })
                print(f"DEBUG: First appointment preserved at position 1 for {patient.name}")
                
                # Initialize cumulative wait time with first appointment's duration (unless it's the only patient)
                if not is_only_patient:
                    cumulative_wait_time = appointment_duration
            
            # Add RL-optimized appointments starting from position 2
            start_position = 2 if first_appointment_item else 1
            total_patients = len(scored_patients) + (1 if first_appointment_item else 0)
            
            for index, item in enumerate(scored_patients):
                patient = item["patient"]
                position = index + start_position
                is_emergency = item.get("is_emergency", False)
                
                print(f"  Position {position}: {patient.name} - Emergency: {is_emergency}")
                
                # Get appointment duration for this patient
                appointment_type = item["appointment_type"]
                appointment_duration = appointment_durations.get(appointment_type, 15)
                
                # Last patient (current patient) should have 0 wait time
                if position == total_patients:
                    # Last patient is the current patient - no wait time
                    estimated_wait_minutes = 0
                elif position == 1:
                    # First patient waits for their appointment duration
                    estimated_wait_minutes = appointment_duration
                    cumulative_wait_time = appointment_duration
                else:
                    # Other patients wait cumulative time of all patients before them
                    estimated_wait_minutes = cumulative_wait_time
                    # Add current patient's duration to cumulative time for next patients
                    cumulative_wait_time += appointment_duration
                
                queue_items.append({
                    "id": patient.id,
                    "name": patient.name,
                    "age": patient.age,
                    "conditions": patient.conditions,
                    "risk_level": patient.risk_level,
                    "score": round(item["score"], 2),
                    "queue_position": position,
                    "estimated_wait_minutes": estimated_wait_minutes,
                    "appointment_duration": appointment_duration,
                    "appointment_type": item["appointment_type"],
                    "is_emergency": item.get("is_emergency", False),  # Add emergency status
                    "status": "waiting",
                    "priority_reason": self._get_priority_reason(item),
                    "rl_optimized": item["rl_recommendation"] is not None
                })
            
            return queue_items
            
        except Exception as e:
            logger.error(f"Queue calculation failed: {e}")
            return []
    
    def reorder_queue_for_emergency(self, session: Session, emergency_patient_id: int) -> List[Dict]:
        """
        Reorder queue when emergency patient arrives
        """
        try:
            # Get current queue
            current_queue = self.calculate_queue_order(session)
            
            # Find emergency patient
            emergency_patient = session.get(Patient, emergency_patient_id)
            if not emergency_patient:
                return current_queue
            
            # Calculate emergency score
            emergency_score = self.scorer.calculate_patient_score(
                emergency_patient, "emergency", emergency=True
            )
            
            # Create emergency queue item
            emergency_item = {
                "id": emergency_patient.id,
                "name": emergency_patient.name,
                "age": emergency_patient.age,
                "conditions": emergency_patient.conditions,
                "risk_level": "high",  # Force high for emergency
                "score": emergency_score,
                "queue_position": 1,  # Always first
                "estimated_wait_minutes": 0,
                "appointment_type": "emergency",
                "status": "emergency",
                "priority_reason": "Emergency case - immediate attention required",
                "rl_optimized": False
            }
            
            # Reorder: Emergency first, then reposition others
            reordered_queue = [emergency_item]
            for item in current_queue:
                if item["id"] != emergency_patient_id:
                    item["queue_position"] += 1
                    item["estimated_wait_minutes"] += 15  # Add emergency delay
                    reordered_queue.append(item)
            
            return reordered_queue
            
        except Exception as e:
            logger.error(f"Emergency reorder failed: {e}")
            return self.calculate_queue_order(session)
    
    def _calculate_wait_time(self, patient: Patient) -> int:
        """Calculate estimated wait time for patient"""
        base_wait = 15  # Base consultation time in minutes
        
        # Adjust based on risk level
        if patient.risk_level == "high":
            return base_wait
        elif patient.risk_level == "medium":
            return base_wait + 10
        else:
            return base_wait + 20
    
    def _get_priority_reason(self, item: Dict) -> str:
        """Generate human-readable reason for queue position"""
        patient = item["patient"]
        score = item["score"]
        
        reasons = []
        
        if score >= 80:
            reasons.append("High priority")
        elif score >= 60:
            reasons.append("Medium priority")
        else:
            reasons.append("Standard priority")
            
        if patient.age >= 65:
            reasons.append("senior citizen")
        elif patient.age <= 5:
            reasons.append("young child")
            
        if patient.risk_level == "high":
            reasons.append("high risk condition")
            
        if patient.conditions and patient.conditions.lower() != "none":
            reasons.append("chronic condition")
            
        if item.get("rl_optimized"):
            reasons.append("AI optimized")
            
        return " - ".join(reasons).capitalize()

# Global instance
queue_manager = None

def get_queue_manager(rl_service):
    """Get singleton queue manager instance"""
    global queue_manager
    if queue_manager is None:
        queue_manager = DynamicQueueManager(rl_service)
    return queue_manager
