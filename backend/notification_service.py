from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

class NotificationType(Enum):
    APPOINTMENT_REMINDER = "appointment_reminder"
    MEDICATION_REMINDER = "medication_reminder"
    HEALTH_TIP = "health_tip"
    EMERGENCY_ALERT = "emergency_alert"
    SYSTEM_UPDATE = "system_update"
    APPOINTMENT_CONFIRMATION = "appointment_confirmation"
    APPOINTMENT_CANCELLATION = "appointment_cancellation"
    LAB_RESULTS = "lab_results"
    PRESCRIPTION_READY = "prescription_ready"
    ANNUAL_CHECKUP = "annual_checkup"
    QUEUE_POSITION = "queue_position"  # New type for queue notifications

class NotificationPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class NotificationChannel(Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"

class Notification:
    def __init__(
        self,
        id: str,
        user_id: int,
        type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        channels: List[NotificationChannel] = None,
        data: Dict[str, Any] = None,
        scheduled_for: Optional[datetime] = None,
        expires_at: Optional[datetime] = None
    ):
        self.id = id
        self.user_id = user_id
        self.type = type
        self.title = title
        self.message = message
        self.priority = priority
        self.channels = channels or [NotificationChannel.IN_APP]
        self.data = data or {}
        self.scheduled_for = scheduled_for or datetime.utcnow()
        self.expires_at = expires_at
        self.created_at = datetime.utcnow()
        self.sent_at = None
        self.read_at = None
        self.status = "pending"

class NotificationService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@navimed.com")
        
        # Mock storage - in production, use database
        self.notifications: List[Notification] = []
        self.user_preferences: Dict[int, Dict[str, bool]] = {}

    def create_notification(
        self,
        user_id: int,
        type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        channels: List[NotificationChannel] = None,
        data: Dict[str, Any] = None,
        scheduled_for: Optional[datetime] = None
    ) -> Notification:
        """Create a new notification"""
        notification_id = f"notif_{len(self.notifications) + 1}_{datetime.utcnow().timestamp()}"
        
        notification = Notification(
            id=notification_id,
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            priority=priority,
            channels=channels,
            data=data,
            scheduled_for=scheduled_for
        )
        
        self.notifications.append(notification)
        return notification

    def get_user_notifications(
        self,
        user_id: int,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get notifications for a specific user"""
        user_notifications = [
            n for n in self.notifications 
            if n.user_id == user_id
        ]
        
        if unread_only:
            user_notifications = [n for n in user_notifications if not n.read_at]
        
        # Sort by creation date (newest first)
        user_notifications.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply pagination
        paginated_notifications = user_notifications[offset:offset + limit]
        
        return [
            {
                "id": n.id,
                "type": n.type.value,
                "title": n.title,
                "message": n.message,
                "priority": n.priority.value,
                "created_at": n.created_at.isoformat(),
                "read_at": n.read_at.isoformat() if n.read_at else None,
                "data": n.data
            }
            for n in paginated_notifications
        ]

    def mark_as_read(self, notification_id: str, user_id: int) -> bool:
        """Mark a notification as read"""
        for notification in self.notifications:
            if notification.id == notification_id and notification.user_id == user_id:
                notification.read_at = datetime.utcnow()
                return True
        return False

    def mark_all_as_read(self, user_id: int) -> int:
        """Mark all notifications as read for a user"""
        count = 0
        for notification in self.notifications:
            if notification.user_id == user_id and not notification.read_at:
                notification.read_at = datetime.utcnow()
                count += 1
        return count

    def delete_notification(self, notification_id: str, user_id: int) -> bool:
        """Delete a notification"""
        for i, notification in enumerate(self.notifications):
            if notification.id == notification_id and notification.user_id == user_id:
                del self.notifications[i]
                return True
        return False

    def get_unread_count(self, user_id: int) -> int:
        """Get count of unread notifications for a user"""
        return len([
            n for n in self.notifications 
            if n.user_id == user_id and not n.read_at
        ])

    def send_notification(self, notification: Notification) -> bool:
        """Send a notification through all specified channels"""
        try:
            for channel in notification.channels:
                if channel == NotificationChannel.EMAIL:
                    self._send_email(notification)
                elif channel == NotificationChannel.SMS:
                    self._send_sms(notification)
                elif channel == NotificationChannel.PUSH:
                    self._send_push(notification)
                elif channel == NotificationChannel.IN_APP:
                    # In-app notifications are stored and retrieved via API
                    pass
            
            notification.sent_at = datetime.utcnow()
            notification.status = "sent"
            return True
        except Exception as e:
            print(f"Error sending notification: {e}")
            notification.status = "failed"
            return False

    def send_queue_position_email(self, patient_email: str, patient_name: str, 
                                  queue_position: int, estimated_wait_minutes: int,
                                  appointment_type: str = "appointment") -> bool:
        """Send queue position and wait time email to patient"""
        try:
            if not patient_email or '@' not in patient_email:
                print(f"Invalid email address: {patient_email}")
                return False

            subject = "NaviMed - Appointment Confirmation & Queue Status"
            
            print(f"\n📧 Sending queue position email to {patient_email}")
            print(f"   Patient: {patient_name}")
            print(f"   Queue Position: #{queue_position}")
            print(f"   Wait Time: {estimated_wait_minutes} minutes")
            print(f"   Appointment Type: {appointment_type}")
            
            # Create HTML email content
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                    .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    .header {{ text-align: center; color: #2c5aa0; margin-bottom: 30px; }}
                    .logo {{ font-size: 28px; font-weight: bold; margin-bottom: 10px; }}
                    .status-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center; }}
                    .queue-info {{ font-size: 24px; font-weight: bold; margin-bottom: 10px; }}
                    .wait-time {{ font-size: 18px; }}
                    .details {{ background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                    .footer {{ text-align: center; color: #666; margin-top: 30px; font-size: 14px; }}
                    .emergency {{ background: linear-gradient(135deg, #ff4757 0%, #ff3838 100%); }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div class="logo">🏥 NaviMed</div>
                        <h2>Appointment Confirmed!</h2>
                    </div>
                    
                    <p>Dear {patient_name},</p>
                    
                    <p>Your {appointment_type.replace('_', ' ').title()} appointment has been successfully booked!</p>
                    
                    <div class="status-card {'emergency' if appointment_type == 'emergency' else ''}">
                        <div class="queue-info">Queue Position: #{queue_position}</div>
                        <div class="wait-time">Estimated Wait Time: {estimated_wait_minutes} minutes</div>
                    </div>
                    
                    <div class="details">
                        <h3>📋 Appointment Details</h3>
                        <p><strong>Appointment Type:</strong> {appointment_type.replace('_', ' ').title()}</p>
                        <p><strong>Current Queue Position:</strong> {queue_position}</p>
                        <p><strong>Estimated Wait Time:</strong> {estimated_wait_minutes} minutes</p>
                        <p><strong>Status:</strong> {"🚨 Emergency - Priority Processing" if appointment_type == "emergency" else "✅ Confirmed"}</p>
                    </div>
                    
                    <div class="details">
                        <h3>ℹ️ What to Expect</h3>
                        <ul>
                            <li>You will be called based on your queue position and priority</li>
                            <li>Wait times are estimates and may vary based on medical urgency</li>
                            <li>Please arrive 15 minutes before your estimated time</li>
                            <li>Bring a valid ID and insurance card (if applicable)</li>
                        </ul>
                    </div>
                    
                    <div class="details">
                        <h3>📞 Need Help?</h3>
                        <p>If you have any questions or need to reschedule:</p>
                        <p><strong>Phone:</strong> (+91) 8112292306</p>
                        <p><strong>Email:</strong> support@navimed.com</p>
                    </div>
                    
                    <div class="footer">
                        <p>Thank you for choosing NaviMed for your healthcare needs!</p>
                        <p>This is an automated message. Please do not reply directly to this email.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Create plain text version
            text_content = f"""
NaviMed - Appointment Confirmation

Dear {patient_name},

Your {appointment_type.replace('_', ' ').title()} appointment has been successfully booked!

QUEUE STATUS:
- Position: #{queue_position}
- Estimated Wait Time: {estimated_wait_minutes} minutes
- Status: {"EMERGENCY - Priority Processing" if appointment_type == "emergency" else "Confirmed"}

APPOINTMENT DETAILS:
- Type: {appointment_type.replace('_', ' ').title()}
- Queue Position: {queue_position}
- Estimated Wait: {estimated_wait_minutes} minutes

WHAT TO EXPECT:
- You will be called based on your queue position and priority
- Wait times are estimates and may vary based on medical urgency
- Please arrive 15 minutes before your estimated time
- Bring a valid ID and insurance card (if applicable)

NEED HELP?
Phone: (+91) 8112292306
Email: support@navimed.com

Thank you for choosing NaviMed for your healthcare needs!
This is an automated message. Please do not reply directly to this email.
            """
            
            return self._send_html_email(patient_email, subject, html_content, text_content)
            
        except Exception as e:
            print(f"Error sending queue position email: {str(e)}")
            return False

    def _send_html_email(self, to_email: str, subject: str, html_content: str, text_content: str) -> bool:
        """Send HTML email with fallback to text"""
        try:
            if not all([self.smtp_server, self.smtp_username, self.smtp_password]):
                print("SMTP configuration not complete. Email not sent.")
                return False

            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject

            # Create text and HTML parts
            text_part = MIMEText(text_content, 'plain')
            html_part = MIMEText(html_content, 'html')

            # Add parts to message
            msg.attach(text_part)
            msg.attach(html_part)

            # Send email with timeout
            server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30)
            try:
                server.starttls()
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
                server.quit()
            except Exception as e:
                server.quit()
                raise e

            print(f"Queue position email sent successfully to {to_email}")
            return True

        except Exception as e:
            print(f"Failed to send queue position email to {to_email}: {str(e)}")
            return False

    def _send_email(self, notification: Notification) -> bool:
        """Send email notification"""
        if not all([self.smtp_server, self.smtp_username, self.smtp_password]):
            print("SMTP configuration not complete")
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = notification.data.get('email', 'user@example.com')
            msg['Subject'] = notification.title
            
            body = f"""
            {notification.message}
            
            ---
            NaviMed Healthcare
            This is an automated message. Please do not reply.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)
            server.quit()
            
            return True
        except Exception as e:
            print(f"Email sending failed: {str(e)}")
            return False

    def _send_sms(self, notification: Notification) -> bool:
        """Send SMS notification (mock implementation)"""
        # In production, integrate with SMS service like Twilio
        print(f"SMS to {notification.data.get('phone', 'N/A')}: {notification.message}")
        return True

    def _send_push(self, notification: Notification) -> bool:
        """Send push notification (mock implementation)"""
        # In production, integrate with push notification service
        print(f"Push notification to user {notification.user_id}: {notification.title}")
        return True

    def create_appointment_reminder(self, user_id: int, appointment_data: Dict[str, Any]) -> Notification:
        """Create appointment reminder notification"""
        title = "Appointment Reminder"
        message = f"Your appointment with {appointment_data.get('doctor_name', 'Dr. Smith')} is scheduled for {appointment_data.get('date')} at {appointment_data.get('time')}."
        
        return self.create_notification(
            user_id=user_id,
            type=NotificationType.APPOINTMENT_REMINDER,
            title=title,
            message=message,
            priority=NotificationPriority.HIGH,
            channels=[NotificationChannel.EMAIL, NotificationChannel.PUSH, NotificationChannel.IN_APP],
            data={
                "appointment_id": appointment_data.get("id"),
                "doctor_name": appointment_data.get("doctor_name"),
                "date": appointment_data.get("date"),
                "time": appointment_data.get("time"),
                "email": appointment_data.get("patient_email")
            },
            scheduled_for=appointment_data.get("reminder_time")
        )

    def create_medication_reminder(self, user_id: int, medication_data: Dict[str, Any]) -> Notification:
        """Create medication reminder notification"""
        title = "Medication Reminder"
        message = f"Time to take your {medication_data.get('medication_name', 'medication')}. Please take {medication_data.get('dosage', '1 tablet')}."
        
        return self.create_notification(
            user_id=user_id,
            type=NotificationType.MEDICATION_REMINDER,
            title=title,
            message=message,
            priority=NotificationPriority.MEDIUM,
            channels=[NotificationChannel.PUSH, NotificationChannel.IN_APP],
            data={
                "medication_id": medication_data.get("id"),
                "medication_name": medication_data.get("medication_name"),
                "dosage": medication_data.get("dosage"),
                "instructions": medication_data.get("instructions")
            }
        )

    def create_emergency_alert(self, user_id: int, alert_data: Dict[str, Any]) -> Notification:
        """Create emergency alert notification"""
        title = "Emergency Alert"
        message = alert_data.get("message", "Emergency alert from NaviMed")
        
        return self.create_notification(
            user_id=user_id,
            type=NotificationType.EMERGENCY_ALERT,
            title=title,
            message=message,
            priority=NotificationPriority.URGENT,
            channels=[NotificationChannel.EMAIL, NotificationChannel.SMS, NotificationChannel.PUSH, NotificationChannel.IN_APP],
            data=alert_data
        )

    def create_health_tip(self, user_id: int, tip_data: Dict[str, Any]) -> Notification:
        """Create health tip notification"""
        title = "Daily Health Tip"
        message = tip_data.get("tip", "Stay healthy and active!")
        
        return self.create_notification(
            user_id=user_id,
            type=NotificationType.HEALTH_TIP,
            title=title,
            message=message,
            priority=NotificationPriority.LOW,
            channels=[NotificationChannel.IN_APP],
            data=tip_data
        )

    def get_user_preferences(self, user_id: int) -> Dict[str, bool]:
        """Get notification preferences for a user"""
        return self.user_preferences.get(user_id, {
            "email": True,
            "push": True,
            "sms": False,
            "appointment_reminders": True,
            "medication_reminders": True,
            "health_tips": True,
            "emergency_alerts": True,
            "system_updates": False,
            "marketing": False
        })

    def update_user_preferences(self, user_id: int, preferences: Dict[str, bool]) -> bool:
        """Update notification preferences for a user"""
        self.user_preferences[user_id] = preferences
        return True

    def process_scheduled_notifications(self) -> int:
        """Process notifications that are scheduled to be sent"""
        now = datetime.utcnow()
        count = 0
        
        for notification in self.notifications:
            if (notification.status == "pending" and 
                notification.scheduled_for <= now and
                (not notification.expires_at or notification.expires_at > now)):
                
                if self.send_notification(notification):
                    count += 1
        
        return count

    def get_notification_statistics(self, user_id: int) -> Dict[str, Any]:
        """Get notification statistics for a user"""
        user_notifications = [n for n in self.notifications if n.user_id == user_id]
        
        return {
            "total": len(user_notifications),
            "unread": len([n for n in user_notifications if not n.read_at]),
            "read": len([n for n in user_notifications if n.read_at]),
            "by_type": {
                "appointment_reminder": len([n for n in user_notifications if n.type == NotificationType.APPOINTMENT_REMINDER]),
                "medication_reminder": len([n for n in user_notifications if n.type == NotificationType.MEDICATION_REMINDER]),
                "health_tip": len([n for n in user_notifications if n.type == NotificationType.HEALTH_TIP]),
                "emergency_alert": len([n for n in user_notifications if n.type == NotificationType.EMERGENCY_ALERT]),
                "system_update": len([n for n in user_notifications if n.type == NotificationType.SYSTEM_UPDATE])
            },
            "by_priority": {
                "low": len([n for n in user_notifications if n.priority == NotificationPriority.LOW]),
                "medium": len([n for n in user_notifications if n.priority == NotificationPriority.MEDIUM]),
                "high": len([n for n in user_notifications if n.priority == NotificationPriority.HIGH]),
                "urgent": len([n for n in user_notifications if n.priority == NotificationPriority.URGENT])
            }
        }

# Global notification service instance
notification_service = NotificationService() 