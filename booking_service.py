import sqlite3
from datetime import datetime, timedelta
from algorithms import (find_available_slots, optimize_barber_schedule, time_to_minutes, 
                       minutes_to_time, smart_barber_assignment, predict_busy_hours)
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
            
            # Convert 12-hour format to 24-hour format if needed
            time = self._convert_to_24_hour_format(time)
            
            # Get service details
            cursor.execute('SELECT id, name, duration, price, shop_id FROM services WHERE id = ?', (service_id,))
            service = cursor.fetchone()
            if not service:
                conn.close()
                return {'success': False, 'message': 'Invalid service selected'}
            
            service_duration = service[2]
            service_price = service[3]
            shop_id = service[4] if len(service) > 4 else 1
            
            # Calculate end time
            start_minutes = time_to_minutes(time)
            end_minutes = start_minutes + service_duration
            end_time = minutes_to_time(end_minutes)
            
            # Use smart barber assignment algorithm
            selected_barber = smart_barber_assignment(service_id, date, time)
            
            if not selected_barber:
                conn.close()
                return {'success': False, 'message': 'No barbers available at this time'}
            
            barber_id = selected_barber['barber_id']
            
            # Create or get customer
            customer_id = self._get_or_create_customer(
                customer_name, customer_email, customer_phone, user_id
            )
            
            # Insert booking with error handling for different schema versions
            booking_id = self._insert_booking_with_fallback(
                cursor, customer_id, barber_id, service_id, shop_id,
                date, time, end_time, notes, service_price
            )
            
            if not booking_id:
                conn.close()
                return {'success': False, 'message': 'Failed to create booking'}
            
            # Update statistics
            self._update_booking_statistics(cursor, customer_id, barber_id)
            
            conn.commit()
            
            # Get barber details for response
            cursor.execute('SELECT name, specialties FROM barbers WHERE id = ?', (barber_id,))
            barber_info = cursor.fetchone()
            
            # Get complete booking data for notifications
            booking_details = self._get_booking_details(booking_id)
            
            # Send notifications
            self._send_booking_notifications(booking_details)
            self._create_booking_notifications(booking_details, user_id)
            
            # Notify shop owner about new booking
            if shop_id:
                self._notify_shop_owner(shop_id, booking_details)
            
            conn.close()
            
            return {
                'success': True,
                'booking_id': booking_id,
                'barber_name': barber_info[0] if barber_info else 'Auto-assigned',
                'barber_specialties': barber_info[1] if barber_info else 'Professional Services',
                'message': 'Booking created successfully'
            }
            
        except Exception as e:
            print(f"Error creating booking: {e}")
            if 'conn' in locals():
                conn.close()
            return {'success': False, 'message': f'An error occurred: {str(e)}'}
    
    def _insert_booking_with_fallback(self, cursor, customer_id, barber_id, service_id, 
                                    shop_id, date, time, end_time, notes, service_price):
        """Insert booking with fallback for different schema versions"""
        booking_id = None
        
        # Try different INSERT queries based on available columns
        insert_options = [
            # Option 1: All columns
            ('''INSERT INTO bookings (customer_id, barber_id, service_id, shop_id, date, 
                start_time, end_time, status, notes, total_price)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
             (customer_id, barber_id, service_id, shop_id, date, time, end_time, 'confirmed', notes, service_price)),
            
            # Option 2: Without total_price
            ('''INSERT INTO bookings (customer_id, barber_id, service_id, shop_id, date, 
                start_time, end_time, status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
             (customer_id, barber_id, service_id, shop_id, date, time, end_time, 'confirmed', notes)),
            
            # Option 3: Without notes
            ('''INSERT INTO bookings (customer_id, barber_id, service_id, shop_id, date, 
                start_time, end_time, status, total_price)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
             (customer_id, barber_id, service_id, shop_id, date, time, end_time, 'confirmed', service_price)),
            
            # Option 4: Basic columns only
            ('''INSERT INTO bookings (customer_id, barber_id, service_id, date, 
                start_time, end_time, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)''',
             (customer_id, barber_id, service_id, date, time, end_time, 'confirmed'))
        ]
        
        for query, params in insert_options:
            try:
                cursor.execute(query, params)
                booking_id = cursor.lastrowid
                break
            except sqlite3.OperationalError:
                continue
        
        return booking_id
    
    def _update_booking_statistics(self, cursor, customer_id, barber_id):
        """Update booking statistics for customer and barber"""
        # Update customer stats
        try:
            cursor.execute('''
                UPDATE customers 
                SET total_bookings = COALESCE(total_bookings, 0) + 1
                WHERE id = ?
            ''', (customer_id,))
        except sqlite3.OperationalError:
            pass
        
        # Update barber stats
        try:
            cursor.execute('''
                UPDATE barbers 
                SET total_bookings = COALESCE(total_bookings, 0) + 1
                WHERE id = ?
            ''', (barber_id,))
        except sqlite3.OperationalError:
            pass
    
    def _notify_shop_owner(self, shop_id, booking_details):
        """Notify shop owner about new booking"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get shop owner user ID
            cursor.execute('''
                SELECT owner_id FROM shops WHERE id = ?
            ''', (shop_id,))
            shop_owner = cursor.fetchone()
            
            if shop_owner and shop_owner[0]:
                owner_id = shop_owner[0]
                
                # Create notification for shop owner
                Notification.create(
                    user_id=owner_id,
                    title="New Booking Received",
                    message=f"New booking from {booking_details['customer_name']} for {booking_details['service_name']} on {booking_details['date']} at {booking_details['start_time']}",
                    notification_type="info",
                    action_url="/shop-owner-admin"
                )
                
                # Send email notification to shop owner
                cursor.execute('SELECT email, first_name FROM users WHERE id = ?', (owner_id,))
                owner_info = cursor.fetchone()
                
                if owner_info:
                    email_service.send_admin_notification(
                        owner_info[0],
                        "New Booking Notification",
                        f"A new booking has been made at your shop.",
                        booking_details
                    )
            
            conn.close()
        except Exception as e:
            print(f"Error notifying shop owner: {e}")
    
    def _convert_to_24_hour_format(self, time_str):
        """Convert 12-hour format time to 24-hour format"""
        try:
            if ':' in time_str and not ('AM' in time_str or 'PM' in time_str):
                return time_str
            
            if 'AM' in time_str or 'PM' in time_str:
                time_part = time_str.replace(' AM', '').replace(' PM', '')
                hours, minutes = time_part.split(':')
                hours = int(hours)
                minutes = int(minutes)
                
                if 'PM' in time_str and hours != 12:
                    hours += 12
                elif 'AM' in time_str and hours == 12:
                    hours = 0
                
                return f"{hours:02d}:{minutes:02d}"
            
            return time_str
        except Exception as e:
            print(f"Error converting time format: {e}")
            return time_str
    
    def _get_or_create_customer(self, name, email, phone, user_id):
        """Get existing customer or create new one"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM customers WHERE email = ?', (email,))
        customer = cursor.fetchone()
        
        if customer:
            customer_id = customer[0]
            cursor.execute('''
                UPDATE customers SET name = ?, phone = ?, user_id = ? 
                WHERE id = ?
            ''', (name, phone, user_id, customer_id))
        else:
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
        
        try:
            cursor.execute('''
                SELECT b.*, s.name as service_name, br.name as barber_name, 
                       sh.name as shop_name, sh.address as shop_address,
                       c.name as customer_name, c.email as customer_email
                FROM bookings b
                JOIN services s ON b.service_id = s.id
                JOIN barbers br ON b.barber_id = br.id
                LEFT JOIN shops sh ON b.shop_id = sh.id
                JOIN customers c ON b.customer_id = c.id
                WHERE b.id = ?
            ''', (booking_id,))
            booking = cursor.fetchone()
        except sqlite3.OperationalError:
            cursor.execute('''
                SELECT b.*, s.name as service_name, br.name as barber_name, 
                       'BookaBarber Shop' as shop_name, '123 Main St' as shop_address,
                       c.name as customer_name, c.email as customer_email
                FROM bookings b
                JOIN services s ON b.service_id = s.id
                JOIN barbers br ON b.barber_id = br.id
                JOIN customers c ON b.customer_id = c.id
                WHERE b.id = ?
            ''', (booking_id,))
            booking = cursor.fetchone()
        
        conn.close()
        
        if booking:
            try:
                return {
                    'id': booking[0],
                    'customer_name': booking[-2],
                    'customer_email': booking[-1],
                    'service_name': booking[-6],
                    'barber_name': booking[-5],
                    'shop_name': booking[-4],
                    'shop_address': booking[-3],
                    'date': booking[4] if len(booking) > 4 else '',
                    'start_time': booking[5] if len(booking) > 5 else '',
                    'end_time': booking[6] if len(booking) > 6 else '',
                    'total_price': booking[8] if len(booking) > 8 else 25,
                    'notes': booking[7] if len(booking) > 7 else ''
                }
            except (IndexError, TypeError):
                return {
                    'id': booking[0] if booking else 0,
                    'customer_name': 'Customer',
                    'customer_email': '',
                    'service_name': 'Service',
                    'barber_name': 'Auto-assigned Barber',
                    'shop_name': 'Elite Barber Shop',
                    'shop_address': '123 Main Street',
                    'date': '',
                    'start_time': '',
                    'end_time': '',
                    'total_price': 25,
                    'notes': ''
                }
        return None
    
    def _send_booking_notifications(self, booking_details):
        """Send email notifications for booking"""
        if booking_details:
            email_service.send_booking_confirmation(booking_details)
    
    def _create_booking_notifications(self, booking_details, user_id):
        """Create in-app notifications"""
        if booking_details and user_id:
            try:
                Notification.create(
                    user_id=user_id,
                    title="Booking Confirmed",
                    message=f"Your appointment for {booking_details['service_name']} on {booking_details['date']} at {booking_details['start_time']} has been confirmed with {booking_details['barber_name']}.",
                    notification_type="success",
                    action_url="/user-dashboard"
                )
            except Exception as e:
                print(f"Error creating notification: {e}")

# Initialize booking service
booking_service = BookingService()