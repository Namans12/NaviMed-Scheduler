from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from collections import defaultdict, Counter
import json
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

class HealthcareAnalytics:
    def __init__(self):
        self.data_cache = {}
        self.report_cache = {}
        
    def calculate_basic_metrics(self, appointments: List[Dict], patients: List[Dict], doctors: List[Dict]) -> Dict[str, Any]:
        """Calculate basic healthcare metrics"""
        total_appointments = len(appointments)
        total_patients = len(patients)
        total_doctors = len(doctors)
        
        # Appointment status distribution
        status_counts = Counter(appointment.get('status', 'unknown') for appointment in appointments)
        
        # Calculate completion rate
        completed_appointments = status_counts.get('completed', 0)
        completion_rate = (completed_appointments / total_appointments * 100) if total_appointments > 0 else 0
        
        # Calculate no-show rate
        no_show_appointments = status_counts.get('no-show', 0)
        no_show_rate = (no_show_appointments / total_appointments * 100) if total_appointments > 0 else 0
        
        # Patient demographics
        gender_distribution = Counter(patient.get('gender', 'unknown') for patient in patients)
        age_groups = self._calculate_age_groups(patients)
        
        # Doctor workload
        doctor_workload = self._calculate_doctor_workload(appointments, doctors)
        
        return {
            "overview": {
                "total_appointments": total_appointments,
                "total_patients": total_patients,
                "total_doctors": total_doctors,
                "completion_rate": round(completion_rate, 2),
                "no_show_rate": round(no_show_rate, 2),
                "average_appointments_per_patient": round(total_appointments / total_patients, 2) if total_patients > 0 else 0
            },
            "appointment_status": dict(status_counts),
            "patient_demographics": {
                "gender_distribution": dict(gender_distribution),
                "age_groups": age_groups
            },
            "doctor_workload": doctor_workload
        }
    
    def _calculate_age_groups(self, patients: List[Dict]) -> Dict[str, int]:
        """Calculate age group distribution"""
        age_groups = {
            "0-17": 0,
            "18-30": 0,
            "31-50": 0,
            "51-65": 0,
            "65+": 0
        }
        
        current_year = datetime.now().year
        for patient in patients:
            dob = patient.get('date_of_birth')
            if dob:
                try:
                    birth_year = int(dob.split('-')[0])
                    age = current_year - birth_year
                    
                    if age < 18:
                        age_groups["0-17"] += 1
                    elif age < 31:
                        age_groups["18-30"] += 1
                    elif age < 51:
                        age_groups["31-50"] += 1
                    elif age < 66:
                        age_groups["51-65"] += 1
                    else:
                        age_groups["65+"] += 1
                except:
                    continue
        
        return age_groups
    
    def _calculate_doctor_workload(self, appointments: List[Dict], doctors: List[Dict]) -> Dict[str, Any]:
        """Calculate doctor workload statistics"""
        doctor_appointments = defaultdict(list)
        
        for appointment in appointments:
            doctor_id = appointment.get('doctor_id')
            if doctor_id:
                doctor_appointments[doctor_id].append(appointment)
        
        workload_stats = []
        for doctor in doctors:
            doctor_id = doctor.get('id')
            appointments_count = len(doctor_appointments.get(doctor_id, []))
            completed_count = len([apt for apt in doctor_appointments.get(doctor_id, []) 
                                 if apt.get('status') == 'completed'])
            
            workload_stats.append({
                "doctor_id": doctor_id,
                "doctor_name": doctor.get('name', 'Unknown'),
                "specialty": doctor.get('specialty', 'Unknown'),
                "total_appointments": appointments_count,
                "completed_appointments": completed_count,
                "completion_rate": round(completed_count / appointments_count * 100, 2) if appointments_count > 0 else 0
            })
        
        # Sort by total appointments
        workload_stats.sort(key=lambda x: x['total_appointments'], reverse=True)
        
        return {
            "top_doctors": workload_stats[:10],
            "average_appointments_per_doctor": round(sum(w['total_appointments'] for w in workload_stats) / len(workload_stats), 2) if workload_stats else 0
        }
    
    def analyze_trends(self, appointments: List[Dict], days: int = 30) -> Dict[str, Any]:
        """Analyze appointment trends over time"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Filter appointments within date range
        recent_appointments = [
            apt for apt in appointments
            if self._parse_date(apt.get('appointment_date')) >= start_date.date()
        ]
        
        # Daily appointment counts
        daily_counts = defaultdict(int)
        for apt in recent_appointments:
            date = apt.get('appointment_date')
            if date:
                daily_counts[date] += 1
        
        # Weekly patterns
        weekly_patterns = defaultdict(int)
        for apt in recent_appointments:
            date = self._parse_date(apt.get('appointment_date'))
            if date:
                weekday = date.strftime('%A')
                weekly_patterns[weekday] += 1
        
        # Monthly trends
        monthly_trends = defaultdict(int)
        for apt in recent_appointments:
            date = self._parse_date(apt.get('appointment_date'))
            if date:
                month_key = date.strftime('%Y-%m')
                monthly_trends[month_key] += 1
        
        # Calculate growth rate
        if len(monthly_trends) >= 2:
            months = sorted(monthly_trends.keys())
            current_month = months[-1]
            previous_month = months[-2]
            growth_rate = ((monthly_trends[current_month] - monthly_trends[previous_month]) / 
                          monthly_trends[previous_month] * 100) if monthly_trends[previous_month] > 0 else 0
        else:
            growth_rate = 0
        
        return {
            "daily_counts": dict(daily_counts),
            "weekly_patterns": dict(weekly_patterns),
            "monthly_trends": dict(monthly_trends),
            "growth_rate": round(growth_rate, 2),
            "total_recent_appointments": len(recent_appointments),
            "average_daily_appointments": round(len(recent_appointments) / days, 2)
        }
    
    def _parse_date(self, date_str: str) -> Optional[datetime.date]:
        """Parse date string to datetime.date object"""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            return None
    
    def analyze_patient_behavior(self, appointments: List[Dict], patients: List[Dict]) -> Dict[str, Any]:
        """Analyze patient behavior patterns"""
        patient_appointments = defaultdict(list)
        
        for appointment in appointments:
            patient_id = appointment.get('patient_id')
            if patient_id:
                patient_appointments[patient_id].append(appointment)
        
        behavior_metrics = []
        for patient in patients:
            patient_id = patient.get('id')
            patient_apts = patient_appointments.get(patient_id, [])
            
            if patient_apts:
                total_apts = len(patient_apts)
                completed_apts = len([apt for apt in patient_apts if apt.get('status') == 'completed'])
                no_shows = len([apt for apt in patient_apts if apt.get('status') == 'no-show'])
                
                # Calculate frequency
                if total_apts > 1:
                    dates = [self._parse_date(apt.get('appointment_date')) for apt in patient_apts]
                    dates = [d for d in dates if d]
                    if len(dates) > 1:
                        dates.sort()
                        avg_days_between = (dates[-1] - dates[0]).days / (len(dates) - 1)
                    else:
                        avg_days_between = 0
                else:
                    avg_days_between = 0
                
                behavior_metrics.append({
                    "patient_id": patient_id,
                    "patient_name": patient.get('name', 'Unknown'),
                    "total_appointments": total_apts,
                    "completed_appointments": completed_apts,
                    "no_shows": no_shows,
                    "completion_rate": round(completed_apts / total_apts * 100, 2) if total_apts > 0 else 0,
                    "no_show_rate": round(no_shows / total_apts * 100, 2) if total_apts > 0 else 0,
                    "average_days_between_appointments": round(avg_days_between, 1),
                    "risk_level": self._calculate_risk_level(completed_apts, no_shows, total_apts)
                })
        
        # Sort by risk level
        behavior_metrics.sort(key=lambda x: x['no_show_rate'], reverse=True)
        
        return {
            "patient_behavior": behavior_metrics,
            "high_risk_patients": [p for p in behavior_metrics if p['risk_level'] == 'high'],
            "average_completion_rate": round(sum(p['completion_rate'] for p in behavior_metrics) / len(behavior_metrics), 2) if behavior_metrics else 0,
            "average_no_show_rate": round(sum(p['no_show_rate'] for p in behavior_metrics) / len(behavior_metrics), 2) if behavior_metrics else 0
        }
    
    def _calculate_risk_level(self, completed: int, no_shows: int, total: int) -> str:
        """Calculate patient risk level based on no-show rate"""
        if total == 0:
            return 'unknown'
        
        no_show_rate = no_shows / total * 100
        
        if no_show_rate > 30:
            return 'high'
        elif no_show_rate > 15:
            return 'medium'
        else:
            return 'low'
    
    def generate_revenue_analysis(self, appointments: List[Dict]) -> Dict[str, Any]:
        """Generate revenue analysis (mock data)"""
        # Actual billing data will be used when deployed for Production!
        total_revenue = 0
        revenue_by_type = defaultdict(float)
        revenue_by_month = defaultdict(float)
        
        for appointment in appointments:
            # Mock revenue calculation
            base_cost = 150  # Base appointment cost
            if appointment.get('appointment_type') == 'emergency':
                cost = base_cost * 2
            elif appointment.get('appointment_type') == 'consultation':
                cost = base_cost * 1.5
            else:
                cost = base_cost
            
            total_revenue += cost
            revenue_by_type[appointment.get('appointment_type', 'general')] += cost
            
            date = self._parse_date(appointment.get('appointment_date'))
            if date:
                month_key = date.strftime('%Y-%m')
                revenue_by_month[month_key] += cost
        
        return {
            "total_revenue": round(total_revenue, 2),
            "revenue_by_type": dict(revenue_by_type),
            "revenue_by_month": dict(revenue_by_month),
            "average_revenue_per_appointment": round(total_revenue / len(appointments), 2) if appointments else 0
        }
    
    def generate_performance_metrics(self, appointments: List[Dict], doctors: List[Dict]) -> Dict[str, Any]:
        """Generate performance metrics for doctors and departments"""
        doctor_performance = {}
        department_performance = defaultdict(lambda: {
            'total_appointments': 0,
            'completed_appointments': 0,
            'no_shows': 0,
            'average_rating': 0,
            'total_ratings': 0
        })
        
        for doctor in doctors:
            doctor_id = doctor.get('id')
            doctor_apts = [apt for apt in appointments if apt.get('doctor_id') == doctor_id]
            
            if doctor_apts:
                completed = len([apt for apt in doctor_apts if apt.get('status') == 'completed'])
                no_shows = len([apt for apt in doctor_apts if apt.get('status') == 'no-show'])
                
                # Mock ratings
                avg_rating = np.random.uniform(4.0, 5.0) if completed > 0 else 0
                
                doctor_performance[doctor_id] = {
                    "doctor_name": doctor.get('name', 'Unknown'),
                    "specialty": doctor.get('specialty', 'Unknown'),
                    "total_appointments": len(doctor_apts),
                    "completed_appointments": completed,
                    "no_shows": no_shows,
                    "completion_rate": round(completed / len(doctor_apts) * 100, 2) if doctor_apts else 0,
                    "average_rating": round(avg_rating, 1),
                    "efficiency_score": round(completed / (len(doctor_apts) + no_shows) * 100, 2) if doctor_apts else 0
                }
                
                # Update department stats
                specialty = doctor.get('specialty', 'General')
                dept = department_performance[specialty]
                dept['total_appointments'] += len(doctor_apts)
                dept['completed_appointments'] += completed
                dept['no_shows'] += no_shows
                dept['total_ratings'] += 1
                dept['average_rating'] = round((dept['average_rating'] * (dept['total_ratings'] - 1) + avg_rating) / dept['total_ratings'], 1)
        
        # Calculate department completion rates
        for dept in department_performance.values():
            dept['completion_rate'] = round(dept['completed_appointments'] / dept['total_appointments'] * 100, 2) if dept['total_appointments'] > 0 else 0
        
        return {
            "doctor_performance": doctor_performance,
            "department_performance": dict(department_performance),
            "top_performers": sorted(doctor_performance.values(), key=lambda x: x['completion_rate'], reverse=True)[:5],
            "department_rankings": sorted(department_performance.items(), key=lambda x: x[1]['completion_rate'], reverse=True)
        }
    
    def generate_insights(self, appointments: List[Dict], patients: List[Dict], doctors: List[Dict]) -> List[Dict[str, Any]]:
        """Generate actionable insights from the data"""
        insights = []
        
        # Calculate overall metrics
        total_apts = len(appointments)
        completed_apts = len([apt for apt in appointments if apt.get('status') == 'completed'])
        no_shows = len([apt for apt in appointments if apt.get('status') == 'no-show'])
        
        # Insight 1: No-show rate
        no_show_rate = (no_shows / total_apts * 100) if total_apts > 0 else 0
        if no_show_rate > 20:
            insights.append({
                "type": "warning",
                "title": "High No-Show Rate",
                "description": f"Current no-show rate is {round(no_show_rate, 1)}%, which is above the recommended 15% threshold.",
                "recommendation": "Consider implementing reminder systems and patient education programs.",
                "impact": "high"
            })
        
        # Insight 2: Peak hours analysis
        hourly_distribution = defaultdict(int)
        for apt in appointments:
            time = apt.get('appointment_time')
            if time:
                try:
                    hour = int(time.split(':')[0])
                    hourly_distribution[hour] += 1
                except:
                    continue
        
        if hourly_distribution:
            peak_hour = max(hourly_distribution.items(), key=lambda x: x[1])
            insights.append({
                "type": "info",
                "title": "Peak Appointment Hours",
                "description": f"Peak appointment time is {peak_hour[0]}:00 with {peak_hour[1]} appointments.",
                "recommendation": "Consider adding more slots during peak hours or encouraging off-peak scheduling.",
                "impact": "medium"
            })
        
        # Insight 3: Doctor workload
        doctor_workload = defaultdict(int)
        for apt in appointments:
            doctor_id = apt.get('doctor_id')
            if doctor_id:
                doctor_workload[doctor_id] += 1
        
        if doctor_workload:
            max_workload = max(doctor_workload.items(), key=lambda x: x[1])
            avg_workload = sum(doctor_workload.values()) / len(doctor_workload)
            
            if max_workload[1] > avg_workload * 1.5:
                insights.append({
                    "type": "warning",
                    "title": "Uneven Doctor Workload",
                    "description": f"Doctor ID {max_workload[0]} has {max_workload[1]} appointments vs average of {round(avg_workload, 1)}.",
                    "recommendation": "Consider redistributing appointments or hiring additional staff.",
                    "impact": "medium"
                })
        
        # Insight 4: Patient retention
        patient_visit_counts = defaultdict(int)
        for apt in appointments:
            patient_id = apt.get('patient_id')
            if patient_id:
                patient_visit_counts[patient_id] += 1
        
        repeat_patients = len([count for count in patient_visit_counts.values() if count > 1])
        total_patients = len(patient_visit_counts)
        retention_rate = (repeat_patients / total_patients * 100) if total_patients > 0 else 0
        
        if retention_rate < 60:
            insights.append({
                "type": "warning",
                "title": "Low Patient Retention",
                "description": f"Only {round(retention_rate, 1)}% of patients return for follow-up appointments.",
                "recommendation": "Implement patient engagement programs and follow-up protocols.",
                "impact": "high"
            })
        
        return insights
    
    def create_visualization(self, data: Dict[str, Any], chart_type: str) -> str:
        """Create data visualizations and return as base64 encoded image"""
        plt.figure(figsize=(10, 6))
        
        if chart_type == "appointment_trends":
            dates = list(data.keys())
            counts = list(data.values())
            plt.plot(dates, counts, marker='o')
            plt.title("Appointment Trends")
            plt.xlabel("Date")
            plt.ylabel("Number of Appointments")
            plt.xticks(rotation=45)
        
        elif chart_type == "status_distribution":
            labels = list(data.keys())
            sizes = list(data.values())
            plt.pie(sizes, labels=labels, autopct='%1.1f%%')
            plt.title("Appointment Status Distribution")
        
        elif chart_type == "weekly_patterns":
            days = list(data.keys())
            counts = list(data.values())
            plt.bar(days, counts)
            plt.title("Weekly Appointment Patterns")
            plt.xlabel("Day of Week")
            plt.ylabel("Number of Appointments")
            plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        # Save to bytes
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        
        # Convert to base64
        img_str = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close()
        
        return f"data:image/png;base64,{img_str}"

# Global analytics service instance
analytics_service = HealthcareAnalytics() 
