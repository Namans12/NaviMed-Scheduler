import gymnasium as gym
import numpy as np
import pandas as pd
from gymnasium import spaces

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

class PatientSchedulingEnv(gym.Env):
    """
    Custom Gymnasium environment for smart patient appointment scheduling.
    State: patient queue, doctor slot matrix, doctor specialties, time, emergencies, no-show prob, etc.
    Action: assign patient to doctor/slot, defer, preempt, etc.
    Reward: modular, see _calculate_reward().
    """
    metadata = {"render_modes": ["human"]}

    def __init__(self, data_path='Datasets/merged_appointments.csv', max_queue=10, n_doctors=3, n_slots=32):
        super().__init__()
        try:
            self.data = pd.read_csv(data_path)
        except:
            self.data = None  # Handle missing data file gracefully
        self.max_queue = max_queue
        self.n_doctors = n_doctors
        self.n_slots = n_slots  # e.g., 15-min slots in 8 hours
        self.current_time = 0
        self.day_length = n_slots
        obs_len = max_queue * 5 + n_doctors * (3 + n_slots) + 2
        self.observation_space = spaces.Box(low=0, high=1, shape=(obs_len,), dtype=np.float32)
        # Action: [patient_idx, doctor_idx, slot_idx, action_type]
        self.action_space = spaces.MultiDiscrete([max_queue, n_doctors, n_slots, 3])
        self.reset()

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.current_time = 0
        self.done = False
        self.patient_queue = self._init_patient_queue()
        self.doctor_status = self._init_doctor_status()
        self.doctor_slots = self._init_doctor_slots()
        self.emergency_flag = 0
        self.total_patients_served = 0
        self.emergency_patients_served = 0
        return self._get_obs(), {}

    def step(self, action):
        patient_idx, doctor_idx, slot_idx, action_type = action
        reward = 0
        info = {}
        reward += self._calculate_reward(patient_idx, doctor_idx, slot_idx, action_type)
        self.current_time += 1
        
        # Add small positive reward for time progression without major issues
        if not self.done:
            reward += 0.1
            
        if self.current_time > self.day_length:
            reward -= 5  # Reduced overtime penalty
            self.done = True
        if len(self.patient_queue) == 0 or self.current_time >= self.day_length:
            # Bonus for completing the day successfully
            if len(self.patient_queue) == 0:
                reward += 10
            self.done = True
        obs = self._get_obs()
        return obs, reward, self.done, False, info

    def _get_obs(self):
        pq = np.zeros((self.max_queue, 5))
        for i, p in enumerate(self.patient_queue[:self.max_queue]):
            pq[i, 0] = p.get('priority', 0) / 3.0  # Normalize to 0-1
            pq[i, 1] = min(p.get('wait_time', 0) / 10.0, 1.0)  # Normalize wait time
            pq[i, 2] = APPOINTMENT_TYPE_MAP.get(p.get('appointment_type', 'CONSULTATION'), 0) / 3.0
            pq[i, 3] = p.get('no_show_prob', 0)
            pq[i, 4] = 1 if p.get('emergency', False) else 0
        ds = np.zeros((self.n_doctors, 3 + self.n_slots))
        for i, d in enumerate(self.doctor_status):
            ds[i, 0] = 1 if d.get('available', 1) else 0
            ds[i, 1] = SPECIALTY_MAP.get(d.get('specialty', 'GENERAL'), 0) / 2.0  # Normalize
            ds[i, 2] = 1 if d.get('emergency_capable', 0) else 0
            ds[i, 3:3+self.n_slots] = self.doctor_slots[i]
        obs = np.concatenate([
            pq.flatten(),
            ds.flatten(),
            [self.current_time / self.day_length],
            [self.emergency_flag]
        ])
        return obs.astype(np.float32)

    def _init_patient_queue(self):
        patients = []
        # Start with 3-7 patients for more realistic scenarios
        n_patients = np.random.randint(3, min(self.max_queue, 8))
        for i in range(n_patients):
            emergency = np.random.choice([0, 1], p=[0.85, 0.15])
            priority = 3 if emergency else np.random.choice([0, 1, 2], p=[0.4, 0.4, 0.2])
            patients.append({
                'priority': priority,
                'wait_time': np.random.randint(0, 3),  # Some patients already waiting
                'appointment_type': np.random.choice(list(APPOINTMENT_TYPE_MAP.keys())),
                'no_show_prob': np.random.uniform(0.05, 0.3),  # More realistic no-show range
                'emergency': emergency
            })
        return patients

    def _init_doctor_status(self):
        doctors = []
        for i in range(self.n_doctors):
            doctors.append({
                'available': 1,
                'specialty': np.random.choice(list(SPECIALTY_MAP.keys())),
                'emergency_capable': np.random.choice([0, 1], p=[0.6, 0.4])  # Not all doctors emergency capable
            })
        return doctors

    def _init_doctor_slots(self):
        # 1 = available, 0 = booked
        slots = []
        for _ in range(self.n_doctors):
            # Some slots may already be booked (realistic scenario)
            doctor_slots = np.ones(self.n_slots)
            n_booked = np.random.randint(0, self.n_slots // 4)  # Up to 25% pre-booked
            if n_booked > 0:
                booked_indices = np.random.choice(self.n_slots, n_booked, replace=False)
                doctor_slots[booked_indices] = 0
            slots.append(doctor_slots)
        return slots

    def _calculate_reward(self, patient_idx, doctor_idx, slot_idx, action_type):
        reward = 0
        
        # Check bounds
        if patient_idx >= len(self.patient_queue) or doctor_idx >= self.n_doctors or slot_idx >= self.n_slots:
            return -2  # Reduced penalty for invalid action
        
        if len(self.patient_queue) == 0:
            return 1  # Small positive for handling empty queue
            
        patient = self.patient_queue[patient_idx]
        doctor = self.doctor_status[doctor_idx]
        slot_available = self.doctor_slots[doctor_idx][slot_idx] == 1
        
        # Assign action
        if action_type == 0 and slot_available:
            base_reward = 5  # Good base reward for successful assignment
            
            # Priority-based bonuses
            if patient['priority'] == 3:  # Emergency
                base_reward += 8 if slot_idx < 3 else 3  # Big bonus for quick emergency handling
                self.emergency_patients_served += 1
            elif patient['priority'] == 2:  # High priority
                base_reward += 3 if slot_idx < 5 else 1
            else:  # Normal priority
                base_reward += 1
            
            # Wait time consideration (less penalty, more nuanced)
            wait_penalty = min(patient['wait_time'] * 0.3, 3)  # Cap wait penalty
            
            # No-show consideration (reduced impact)
            no_show_penalty = patient['no_show_prob'] * 2
            
            # Doctor utilization bonus
            utilization_bonus = 1 if np.sum(self.doctor_slots[doctor_idx]) > self.n_slots * 0.5 else 0
            
            # Emergency capability match bonus
            emergency_match_bonus = 2 if patient['priority'] == 3 and doctor['emergency_capable'] else 0
            
            reward = base_reward - wait_penalty - no_show_penalty + utilization_bonus + emergency_match_bonus
            
            # Update state
            self.doctor_slots[doctor_idx][slot_idx] = 0
            self.patient_queue.pop(patient_idx)
            self.total_patients_served += 1
            doctor['available'] = 1 if np.sum(self.doctor_slots[doctor_idx]) > 0 else 0
            
        # Defer action
        elif action_type == 1:
            if len(self.patient_queue) > 0:
                patient = self.patient_queue.pop(patient_idx)
                patient['wait_time'] += 1
                self.patient_queue.append(patient)
                
                # Less penalty for deferring, but more for emergency patients
                if patient['priority'] == 3:
                    reward = -3  # Higher penalty for deferring emergency
                else:
                    reward = -0.5  # Reduced defer penalty
                    
        # Preempt action
        elif action_type == 2 and slot_available:
            if patient['priority'] == 3:  # Emergency preemption
                self.patient_queue.pop(patient_idx)
                self.doctor_slots[doctor_idx][slot_idx] = 0
                reward = 8  # Good reward for emergency preemption
                self.emergency_patients_served += 1
            else:
                reward = -1  # Small penalty for non-emergency preemption
                
        else:
            reward = -0.5  # Small penalty for invalid/unsuccessful action
            
        # End-of-day bonuses
        if self.current_time >= self.day_length - 1:
            # Bonus for serving many patients
            service_bonus = self.total_patients_served * 0.5
            # Bonus for handling emergencies
            emergency_bonus = self.emergency_patients_served * 2
            reward += service_bonus + emergency_bonus
            
        return reward

    def render(self):
        print(f"Time: {self.current_time}/{self.day_length}, Queue: {len(self.patient_queue)}, Served: {self.total_patients_served}, Emergency: {self.emergency_patients_served}")
        print(f"Doctor slots available: {[int(np.sum(slots)) for slots in self.doctor_slots]}") 