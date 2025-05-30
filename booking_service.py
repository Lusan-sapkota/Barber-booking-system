import sqlite3
from datetime import datetime, timedelta
from algorithms import find_available_slots, optimize_barber_schedule, time_to_minutes, minutes_to_time
from email_service import email_service
from models import Notification, AdminAction
import random

class BookingService:
    def __init__(self):
        self.db_path = 'barbershop.db'
    
    def create_booking(self, booking_data, user_id=None):
        """Create a new booking using smart algorithms"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Extract booking data
            service_id = booking_data.get('service_id')
            date = booking_data.get('appointment_date')
            time = booking_data.get('appointment_time')
            customer_name = booking_data.get('customer_name')
            customer_email = booking_data.get('customer_email')
            customer_phone = booking_data.get('customer_phone')
            notes = booking_data.get('customer_notes', '')
            
            # Get service details
            cursor.execute('SELECT * FROM services WHERE id = ?', (service_id,))
            service = cursor.fetchone()
            if not service:
                return {'success': False, 'message': 'Invalid service selected'}
            
            service_duration = service[2]  # Duration in minutes
            service_price = service[3]
            shop_id = service[4]
            
            # Calculate end time
            start_minutes = time_to_minutes(time)
            end_minutes = start_minutes + service_duration
            end_time = minutes_to_time(end_minutes)
            
            # Find available barber using algorithm
            available_slots = find_available_slots(date, service_id)
            
            # Filter slots for the requested time
            suitable_barbers = [
                slot for slot in available_slots 
                if slot['time'] == time
            ]
            
            if not suitable_barbers:
                return {'success': False, 'message': 'No barbers available at this time'}
            
            # Select best barber (you can enhance this logic)
            selected_barber = self._select_best_barber(suitable_barbers, date)
            barber_id = selected_barber['barber_id']
            
            # Create or get customer
            customer_id = self._get_or_create_customer(
                customer_name, customer_email, customer_phone, user_id
            )
            
            # Create booking
            cursor.execute('''
                INSERT INTO bookings (
                    customer_id, barber_id, service_id, shop_id, date, 
                    start_time, end_time, status, notes, total_price
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                customer_id, barber_id, service_id, shop_id, date,
                time, end_time, 'confirmed', notes, service_price
            ))
            
            booking_id = cursor.lastrowid
            
            # Update customer stats
            cursor.execute('''
                UPDATE customers 
                SET total_bookings = total_bookings + 1,
                    total_spent = total_spent + ?
                WHERE id = ?
            ''', (service_price, customer_id))
            
            # Update barber stats
            cursor.execute('''
                UPDATE barbers 
                SET total_bookings = total_bookings + 1
                WHERE id = ?
            ''', (barber_id,))
            
            conn.commit()
            
            # Get complete booking data for notifications
            booking_details = self._get_booking_details(booking_id)
            
            # Send confirmation email
            self._send_booking_notifications(booking_details)
            
            # Create notifications
            self._create_booking_notifications(booking_details, user_id)
            
            conn.close()
            
            return {
                'success': True,
                'booking_id': booking_id,
                'barber_name': booking_details['barber_name'],
                'message': 'Booking created successfully'
            }
            
        except Exception as e:
            print(f"Error creating booking: {e}")
            return {'success': False, 'message': f'An error occurred: {str(e)}'}
    
    def _select_best_barber(self, suitable_barbers, date):
        """Select the best barber based on various criteria"""
        # Simple algorithm - select barber with highest rating
        # You can enhance this with more sophisticated logic
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        best_barber = None
        best_score = -1
        
        for barber_slot in suitable_barbers:
            barber_id = barber_slot['barber_id']
            
            # Get barber details
            cursor.execute('SELECT rating, total_bookings FROM barbers WHERE id = ?', (barber_id,))
            barber_data = cursor.fetchone()
            
            if barber_data:
                rating, total_bookings = barber_data
                
                # Calculate score (rating weighted by experience)
                score = rating + (total_bookings * 0.01)  # Slight preference for experienced barbers
                
                if score > best_score:
                    best_score = score
                    best_barber = barber_slot
        
        conn.close()
        return best_barber or suitable_barbers[0]  # Fallback to first available
    
    def _get_or_create_customer(self, name, email, phone, user_id):
        """Get existing customer or create new one"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if customer exists
        cursor.execute('SELECT id FROM customers WHERE email = ?', (email,))
        customer = cursor.fetchone()
        
        if customer:
            customer_id = customer[0]
            # Update customer info
            cursor.execute('''
                UPDATE customers SET name = ?, phone = ?, user_id = ? 
                WHERE id = ?
            ''', (name, phone, user_id, customer_id))
        else:
            # Create new customer
            cursor.execute('''
                INSERT INTO customers (user_id, name, email, phone)
                VALUES (?, ?, ?, ?)
            ''', (user_id, name, email, phone))
            customer_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return customer_id
    
    def _get_booking_details(self, booking_id):
        """Get complete booking details for notifications"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT b.*, s.name as service_name, br.name as barber_name, 
                   sh.name as shop_name, sh.address as shop_address,
                   c.name as customer_name, c.email as customer_email
            FROM bookings b
            JOIN services s ON b.service_id = s.id
            JOIN barbers br ON b.barber_id = br.id
            JOIN shops sh ON b.shop_id = sh.id
            JOIN customers c ON b.customer_id = c.id
            WHERE b.id = ?
        ''', (booking_id,))
        
        booking = cursor.fetchone()
        conn.close()
        
        if booking:
            return {
                'id': booking[0],
                'customer_name': booking[17],
                'customer_email': booking[18],
                'service_name': booking[11],
                'barber_name': booking[12],
                'shop_name': booking[13],
                'shop_address': booking[14],
                'date': booking[5],
                'start_time': booking[6],
                'end_time': booking[7],
                'total_price': booking[10],
                'notes': booking[9]
            }
        return None
    
    def _send_booking_notifications(self, booking_details):
        """Send email notifications for booking"""
        if booking_details:
            # Send confirmation email to customer
            email_service.send_booking_confirmation(booking_details)
            
            # You can add barber notification here
            # email_service.send_barber_notification(booking_details)
    
    def _create_booking_notifications(self, booking_details, user_id):
        """Create in-app notifications"""
        if booking_details and user_id:
            # Customer notification
            Notification.create(
                user_id=user_id,
                title="Booking Confirmed",
                message=f"Your appointment for {booking_details['service_name']} on {booking_details['date']} at {booking_details['start_time']} has been confirmed.",
                notification_type="success",
                action_url="/user-dashboard"
            )

# Initialize booking service
booking_service = BookingService()