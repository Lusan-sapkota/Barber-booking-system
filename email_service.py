import smtplib
import sqlite3
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from datetime import datetime
import os
from jinja2 import Environment, FileSystemLoader

class EmailService:
    def __init__(self):
        # Email configuration - Update these with your SMTP settings
        self.smtp_server = "smtp.gmail.com"  # or your SMTP server
        self.smtp_port = 587
        self.email_address = "your-email@gmail.com"  # Update this
        self.email_password = "your-app-password"    # Update this (use app password for Gmail)
        
        # Template environment
        self.template_env = Environment(
            loader=FileSystemLoader('templates/emails'),
            autoescape=True
        )
    
    def send_email(self, to_email, subject, html_content, text_content=None):
        """Send email and log the attempt"""
        try:
            # Create message
            msg = MimeMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email_address
            msg['To'] = to_email
            
            # Add text and HTML parts
            if text_content:
                text_part = MimeText(text_content, 'plain')
                msg.attach(text_part)
            
            html_part = MimeText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_address, self.email_password)
                server.send_message(msg)
            
            # Log success
            self._log_email(to_email, subject, 'sent')
            return True
            
        except Exception as e:
            # Log failure
            self._log_email(to_email, subject, 'failed', str(e))
            print(f"Email sending failed: {e}")
            return False
    
    def _log_email(self, recipient, subject, status, error_message=None):
        """Log email attempt to database"""
        conn = sqlite3.connect('barbershop.db')
        cursor = conn.cursor()
        
        sent_at = datetime.now() if status == 'sent' else None
        
        cursor.execute('''
            INSERT INTO email_logs (recipient_email, subject, status, error_message, sent_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (recipient, subject, status, error_message, sent_at))
        
        conn.commit()
        conn.close()
    
    def send_booking_confirmation(self, booking_data):
        """Send booking confirmation email"""
        try:
            template = self.template_env.get_template('booking_confirmation.html')
            html_content = template.render(booking=booking_data)
            
            subject = f"Booking Confirmation - {booking_data['service_name']}"
            
            return self.send_email(
                booking_data['customer_email'],
                subject,
                html_content
            )
        except Exception as e:
            print(f"Error sending booking confirmation: {e}")
            return False
    
    def send_booking_reminder(self, booking_data):
        """Send booking reminder email"""
        try:
            template = self.template_env.get_template('booking_reminder.html')
            html_content = template.render(booking=booking_data)
            
            subject = f"Appointment Reminder - Tomorrow at {booking_data['start_time']}"
            
            return self.send_email(
                booking_data['customer_email'],
                subject,
                html_content
            )
        except Exception as e:
            print(f"Error sending booking reminder: {e}")
            return False
    
    def send_welcome_email(self, user_data):
        """Send welcome email to new users"""
        try:
            template = self.template_env.get_template('welcome.html')
            html_content = template.render(user=user_data)
            
            subject = f"Welcome to BookaBarber, {user_data['first_name']}!"
            
            return self.send_email(
                user_data['email'],
                subject,
                html_content
            )
        except Exception as e:
            print(f"Error sending welcome email: {e}")
            return False
    
    def send_admin_notification(self, admin_email, title, message, data=None):
        """Send notification to admin"""
        try:
            template = self.template_env.get_template('admin_notification.html')
            html_content = template.render(
                title=title,
                message=message,
                data=data,
                timestamp=datetime.now()
            )
            
            return self.send_email(
                admin_email,
                f"[BookaBarber Admin] {title}",
                html_content
            )
        except Exception as e:
            print(f"Error sending admin notification: {e}")
            return False
    
    def send_password_reset_email(self, user_data):
        """Send password reset email"""
        try:
            recipient_email = user_data['email']
            first_name = user_data['first_name']
            reset_link = user_data['reset_link']
            
            subject = "Reset Your BookaBarber Password"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Password Reset - BookaBarber</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f8f9fa; }}
                    .container {{ max-width: 600px; margin: 0 auto; background: white; }}
                    .header {{ background: linear-gradient(135deg, #0d6efd, #0b5ed7); padding: 2rem; text-align: center; }}
                    .header h1 {{ color: white; margin: 0; font-size: 2rem; }}
                    .content {{ padding: 2rem; }}
                    .button {{ display: inline-block; background: #0d6efd; color: white; padding: 1rem 2rem; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 1rem 0; }}
                    .footer {{ background: #f8f9fa; padding: 1rem; text-align: center; color: #6c757d; font-size: 0.9rem; }}
                    .warning {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 1rem; border-radius: 8px; margin: 1rem 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🔑 Password Reset</h1>
                    </div>
                    <div class="content">
                        <h2>Hello {first_name}!</h2>
                        <p>We received a request to reset your BookaBarber account password.</p>
                        
                        <p>Click the button below to reset your password:</p>
                        
                        <a href="{reset_link}" class="button">Reset My Password</a>
                        
                        <div class="warning">
                            <strong>⚠️ Security Notice:</strong>
                            <ul>
                                <li>This link will expire in 1 hour</li>
                                <li>If you didn't request this reset, please ignore this email</li>
                                <li>Never share this link with anyone</li>
                            </ul>
                        </div>
                        
                        <p>If the button doesn't work, copy and paste this link into your browser:</p>
                        <p style="word-break: break-all; color: #0d6efd;">{reset_link}</p>
                        
                        <hr style="margin: 2rem 0;">
                        
                        <p><strong>Need help?</strong> Contact our support team if you have any questions.</p>
                    </div>
                    <div class="footer">
                        <p>This email was sent from BookaBarber - Your trusted barbershop booking platform</p>
                        <p>© 2024 BookaBarber. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Log email attempt
            self._log_email(recipient_email, subject, 'pending')
            
            # Send email (implement your email sending logic here)
            success = True  # Replace with actual email sending
            
            # Log result
            if success:
                self._log_email(recipient_email, subject, 'sent')
                return True
            else:
                self._log_email(recipient_email, subject, 'failed', 'Email sending failed')
                return False
                
        except Exception as e:
            print(f"Password reset email error: {e}")
            self._log_email(user_data.get('email', ''), subject, 'failed', str(e))
            return False

# Initialize email service
email_service = EmailService()