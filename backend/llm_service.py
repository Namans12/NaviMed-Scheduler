import openai
import os
from typing import Dict, List, Optional
from datetime import datetime
import json
from dotenv import load_dotenv

load_dotenv()

class LLMService:
    """LLM service for intelligent chatbot and appointment assistance"""
    
    def __init__(self):
        # Initialize OpenAI client
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.model = "gpt-3.5-turbo"  # Can be upgraded to gpt-4 for better performance
        
        # System prompt for healthcare context
        self.system_prompt = """You are NaviMed, an intelligent healthcare assistant for a patient appointment scheduling system. 

Your capabilities include:
- Helping patients book, reschedule, or cancel appointments
- Providing information about doctors, specialties, and available slots
- Answering questions about appointment preparation
- Explaining the AI-powered scheduling system
- Handling emergency appointment requests

Key information about the system:
- We use AI (Reinforcement Learning) to optimize appointment scheduling
- Emergency appointments are prioritized automatically
- Patients can choose their preferred doctor or let AI recommend the best match
- The system considers doctor availability, patient priority, and wait times

Always be helpful, professional, and prioritize patient safety. If a patient mentions urgent symptoms, recommend they call emergency services immediately."""

    def chat_with_patient(self, user_message: str, context: Dict = None) -> Dict:
        """Handle patient chat messages and provide intelligent responses"""
        
        try:
            # Prepare conversation context
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Add context if provided
            if context:
                context_message = f"Current context: {json.dumps(context, default=str)}"
                messages.append({"role": "system", "content": context_message})
            
            # Add user message
            messages.append({"role": "user", "content": user_message})
            
            # Get response from OpenAI
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            assistant_response = response.choices[0].message.content
            
            # Analyze intent and extract actions
            intent_analysis = self._analyze_intent(user_message, assistant_response)
            
            return {
                "response": assistant_response,
                "intent": intent_analysis["intent"],
                "confidence": intent_analysis["confidence"],
                "actions": intent_analysis["actions"],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "response": "I apologize, but I'm experiencing technical difficulties. Please try again or contact our support team.",
                "intent": "error",
                "confidence": 0.0,
                "actions": [],
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _analyze_intent(self, user_message: str, assistant_response: str) -> Dict:
        """Analyze user intent and extract potential actions"""
        
        user_message_lower = user_message.lower()
        
        # Intent classification
        intents = {
            "book_appointment": ["book", "schedule", "make appointment", "new appointment"],
            "reschedule": ["reschedule", "change", "move", "postpone"],
            "cancel": ["cancel", "cancel appointment"],
            "doctor_info": ["doctor", "specialist", "physician", "who"],
            "availability": ["available", "when", "time", "slot"],
            "emergency": ["emergency", "urgent", "immediate", "critical"],
            "general_help": ["help", "how", "what", "explain"]
        }
        
        detected_intent = "general_help"
        confidence = 0.5
        
        for intent, keywords in intents.items():
            for keyword in keywords:
                if keyword in user_message_lower:
                    detected_intent = intent
                    confidence = 0.8
                    break
            if confidence > 0.5:
                break
        
        # Extract potential actions
        actions = []
        if detected_intent == "book_appointment":
            actions.append("redirect_to_booking")
        elif detected_intent == "reschedule":
            actions.append("redirect_to_reschedule")
        elif detected_intent == "emergency":
            actions.append("emergency_booking")
            actions.append("urgent_priority")
        
        return {
            "intent": detected_intent,
            "confidence": confidence,
            "actions": actions
        }
    
    def generate_appointment_suggestions(self, patient_info: Dict, available_slots: List[Dict]) -> str:
        """Generate personalized appointment suggestions using LLM"""
        
        prompt = f"""Based on the following patient information and available slots, suggest the best appointment options:

Patient Information:
- Age: {patient_info.get('age', 'N/A')}
- Medical History: {patient_info.get('medical_history', 'N/A')}
- Preferred Time: {patient_info.get('preferred_time', 'Any')}
- Urgency: {patient_info.get('urgency', 'Regular')}

Available Slots:
{json.dumps(available_slots, indent=2)}

Please provide 2-3 personalized suggestions with reasoning for each recommendation."""

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a healthcare scheduling assistant. Provide clear, helpful appointment suggestions."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Unable to generate suggestions due to technical issues: {str(e)}"
    
    def explain_ai_scheduling(self, patient_question: str) -> str:
        """Explain how the AI scheduling system works"""
        
        prompt = f"""A patient asked: "{patient_question}"

Explain how our AI-powered scheduling system works in simple terms. Include:
- How we use machine learning to optimize appointments
- How we prioritize patients (emergency, urgent, regular)
- How we match patients with the best available doctors
- Benefits of AI scheduling vs traditional methods

Keep it simple and reassuring for patients."""

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are explaining AI technology to patients in a friendly, understandable way."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return "Our AI scheduling system uses advanced machine learning to find the best appointment times and doctor matches for each patient, considering factors like urgency, doctor availability, and wait times."
    
    def generate_health_tips(self, appointment_type: str, patient_age: Optional[int] = None) -> str:
        """Generate personalized health tips based on appointment type"""
        
        prompt = f"""Generate 3-4 helpful health tips for a patient with:
- Appointment Type: {appointment_type}
- Age: {patient_age if patient_age else 'Not specified'}

Tips should be:
- Relevant to the appointment type
- Age-appropriate if age is provided
- Practical and actionable
- Encouraging and supportive

Format as a friendly list."""

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a caring healthcare assistant providing helpful health tips."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=250,
                temperature=0.8
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return "Remember to bring any relevant medical records and arrive 10 minutes early for your appointment. Stay hydrated and get a good night's sleep before your visit." 