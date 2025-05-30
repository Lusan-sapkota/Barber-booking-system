from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_file
import sqlite3
from datetime import datetime, date
import hashlib
from models import (init_db, Booking, Barber, Customer, Service, User, Shop, 
                   Notification, AdminAction, SystemSettings)
from algorithms import find_available_slots, optimize_barber_schedule
import os
import requests
import json
import random
from typing import Tuple, Optional
import math

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-default-secret-key')

# Add this configuration for better session security
app.config.update(
    SESSION_COOKIE_SECURE=False,  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=3600  # 1 hour
)

# Initialize database
init_db()

# Add user authentication tables
def init_auth_tables():
    """Initialize authentication tables with all required columns"""
    conn = sqlite3.connect('barbershop.db')
    cursor = conn.cursor()
    
    # Create users table with all required columns
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        phone TEXT,
        user_type TEXT NOT NULL DEFAULT 'customer',
        shop_id INTEGER,
        status TEXT DEFAULT 'active',
        last_login TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create password_resets table for forgot password functionality
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS password_resets (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        token TEXT NOT NULL,
        expires_at INTEGER NOT NULL,
        used BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Create admin_actions table for logging
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS admin_actions (
        id INTEGER PRIMARY KEY,
        admin_id INTEGER NOT NULL,
        action_type TEXT NOT NULL,
        target_type TEXT NOT NULL,
        target_id INTEGER NOT NULL,
        description TEXT,
        ip_address TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (admin_id) REFERENCES users (id)
    )
    ''')
    
    # Create system_settings table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS system_settings (
        id INTEGER PRIMARY KEY,
        setting_key TEXT UNIQUE NOT NULL,
        setting_value TEXT,
        updated_by INTEGER,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (updated_by) REFERENCES users (id)
    )
    ''')
    
    # Create newsletter_subscribers table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS newsletter_subscribers (
        id INTEGER PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        name TEXT,
        subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ip_address TEXT,
        user_agent TEXT,
        status TEXT DEFAULT 'active'
    )
    ''')
    
    conn.commit()
    conn.close()
    print("Authentication tables initialized successfully!")

# Initialize auth tables
init_auth_tables()

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, password_hash):
    """Verify password against hash"""
    return hash_password(password) == password_hash

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/booking')
def booking_page():
    # Pass today's date to the template
    today = date.today().strftime('%Y-%m-%d')
    return render_template('booking.html', today_date=today)

@app.route('/admin')
def admin_page():
    # Check if user is barber
    if session.get('user_type') != 'barber':
        flash('You need to be a barber to access this page', 'danger')
        return redirect(url_for('home'))
    return render_template('barber_admin.html')

@app.route('/login')
def login():
    if session.get('user_id'):
        return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/signup')
def signup():
    if session.get('user_id'):
        return redirect(url_for('home'))
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('home'))

@app.route('/user-dashboard')
def user_dashboard():
    if not session.get('user_id') or session.get('user_type') != 'customer':
        flash('Please log in as a customer to access this page', 'warning')
        return redirect(url_for('login'))
    
    # Get user's bookings
    conn = sqlite3.connect('barbershop.db')
    cursor = conn.cursor()
    
    try:
        # First, check if customer record exists for this user
        cursor.execute("SELECT id FROM customers WHERE user_id = ?", (session['user_id'],))
        customer = cursor.fetchone()
        
        if customer:
            # Customer record exists with user_id
            cursor.execute("""
                SELECT b.id, s.name, b.date, b.start_time, b.end_time, br.name as barber_name, 
                       COALESCE(b.status, 'confirmed') as status
                FROM bookings b
                JOIN services s ON b.service_id = s.id
                JOIN barbers br ON b.barber_id = br.id
                JOIN customers c ON b.customer_id = c.id
                WHERE c.user_id = ?
                ORDER BY b.date DESC, b.start_time DESC
            """, (session['user_id'],))
        else:
            # Try to find customer by email (fallback)
            user_email = session.get('email')
            if user_email:
                cursor.execute("""
                    SELECT b.id, s.name, b.date, b.start_time, b.end_time, br.name as barber_name, 
                           COALESCE(b.status, 'confirmed') as status
                    FROM bookings b
                    JOIN services s ON b.service_id = s.id
                    JOIN barbers br ON b.barber_id = br.id
                    JOIN customers c ON b.customer_id = c.id
                    WHERE c.email = ?
                    ORDER BY b.date DESC, b.start_time DESC
                """, (user_email,))
            else:
                # No bookings found
                bookings = []
                conn.close()
                return render_template('customer_dashboard.html', bookings=bookings)
        
        bookings = cursor.fetchall()
        conn.close()
        
        return render_template('customer_dashboard.html', bookings=bookings)
        
    except Exception as e:
        print(f"Error in user dashboard: {e}")
        conn.close()
        flash('Error loading dashboard', 'error')
        return redirect(url_for('home'))

@app.route('/find-nearby')
def find_nearby():
    """Route for finding nearby barbers"""
    location = request.args.get('location', '')
    return render_template('find_nearby.html', location=location)

@app.route('/profile')
def profile():
    """User profile page"""
    if not session.get('user_id'):
        flash('Please log in to access your profile', 'warning')
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('barbershop.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, email, first_name, last_name, phone, user_type, created_at
        FROM users WHERE id = ?
    """, (session['user_id'],))
    
    user = cursor.fetchone()
    conn.close()
    
    if user:
        user_data = {
            'id': user[0],
            'email': user[1],
            'first_name': user[2],
            'last_name': user[3],
            'phone': user[4],
            'user_type': user[5],
            'created_at': user[6]
        }
        return render_template('profile.html', user=user_data)
    else:
        flash('User not found', 'error')
        return redirect(url_for('logout'))

@app.route('/shop-admin')
def shop_admin():
    """Shop owner admin panel"""
    if session.get('user_type') != 'shop_owner':
        flash('You need to be a shop owner to access this page', 'danger')
        return redirect(url_for('home'))
    return render_template('shop_owner_admin.html')

# Super Admin Routes
@app.route('/super-admin')
def super_admin():
    """Super admin panel"""
    if session.get('user_type') != 'super_admin':
        flash('You need to be a super admin to access this page', 'danger')
        return redirect(url_for('home'))
    
    # Get statistics
    stats = get_admin_stats()
    
    # Get users
    users = User.get_all()
    
    # Get shops
    shops = Shop.get_all()
    
    # Get recent admin actions
    recent_actions = AdminAction.get_recent(20)
    
    # Get system settings
    system_settings = SystemSettings.get_all()
    
    # Get email logs
    email_logs = get_email_logs(50)
    
    return render_template('super_admin.html', 
                         stats=stats,
                         users=users,
                         shops=shops,
                         recent_actions=recent_actions,
                         system_settings=system_settings,
                         email_logs=email_logs)

@app.route('/barber-admin')
def barber_admin():
    """Barber admin panel"""
    if session.get('user_type') != 'barber':
        flash('You need to be a barber to access this page', 'danger')
        return redirect(url_for('home'))
    
    # Get barber's bookings and stats
    barber_stats = get_barber_stats(session.get('user_id'))
    
    return render_template('barber_admin.html', stats=barber_stats)

@app.route('/shop-owner-admin')
def shop_owner_admin():
    """Shop owner admin panel"""
    if session.get('user_type') != 'shop_owner':
        flash('You need to be a shop owner to access this page', 'danger')
        return redirect(url_for('home'))
    
    # Get shop owner's data
    shop_stats = get_shop_owner_stats(session.get('user_id'))
    
    return render_template('shop_owner_admin.html', stats=shop_stats)

# Notifications route
@app.route('/notifications')
def notifications():
    """Notifications page for all users"""
    if not session.get('user_id'):
        flash('Please log in to view notifications', 'warning')
        return redirect(url_for('login'))
    
    user_notifications = Notification.get_by_user(session.get('user_id'))
    unread_count = Notification.get_unread_count(session.get('user_id'))
    
    return render_template('notification.html', 
                         notifications=user_notifications,
                         unread_count=unread_count)

# API Routes
@app.route('/api/book-appointment', methods=['POST'])
def api_book_appointment():
    """Enhanced booking API using algorithms"""
    try:
        booking_data = request.json
        
        if not booking_data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        # Use the enhanced booking service
        from booking_service import booking_service
        result = booking_service.create_booking(booking_data, session.get('user_id'))
        
        if result['success']:
            # Log admin action if user is logged in
            if session.get('user_id'):
                AdminAction.log(
                    admin_id=session.get('user_id'),
                    action_type='create',
                    target_type='booking',
                    target_id=result['booking_id'],
                    description=f"Created booking for {booking_data.get('customer_name')}",
                    ip_address=request.remote_addr
                )
            
            return jsonify({
                "success": True,
                "booking_id": result['booking_id'],
                "assigned_barber": {
                    "name": result.get('barber_name'),
                    "specialization": "Professional Barber"
                },
                "message": "Appointment booked successfully"
            })
        else:
            return jsonify(result), 400
            
    except Exception as e:
        print(f"Error in booking API: {e}")
        return jsonify({"success": False, "message": f"An error occurred: {str(e)}"}), 500

# Authentication API Routes
@app.route('/api/login', methods=['POST'])
def api_login():
    """User login API with better error handling"""
    try:
        # Get JSON data from request
        if request.is_json:
            data = request.get_json()
        else:
            # Fallback for form data
            data = {
                'email': request.form.get('email'),
                'password': request.form.get('password'),
                'user_type': request.form.get('user_type', 'customer'),
                'remember_me': request.form.get('remember_me') == 'on'
            }
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        user_type = data.get('user_type', 'customer')
        
        # Validate input
        if not email or not password:
            return jsonify({
                "success": False, 
                "message": "Email and password are required",
                "error_type": "validation"
            }), 400
        
        # Validate email format
        import re
        email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_pattern, email):
            return jsonify({
                "success": False, 
                "message": "Please enter a valid email address",
                "error_type": "validation"
            }), 400
        
        conn = sqlite3.connect('barbershop.db')
        cursor = conn.cursor()
        
        # Check what columns exist in the users table
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Build query based on available columns
        if 'status' in columns:
            cursor.execute('''
                SELECT id, password_hash, first_name, last_name, user_type, status 
                FROM users 
                WHERE email = ? AND user_type = ?
            ''', (email, user_type))
        else:
            # Fallback if status column doesn't exist
            cursor.execute('''
                SELECT id, password_hash, first_name, last_name, user_type, 'active' as status 
                FROM users 
                WHERE email = ? AND user_type = ?
            ''', (email, user_type))
        
        user = cursor.fetchone()
        
        # Check if user exists
        if not user:
            conn.close()
            return jsonify({
                "success": False, 
                "message": f"No {user_type} account found with this email address",
                "error_type": "user_not_found"
            }), 401
        
        # Check password
        if not verify_password(password, user[1]):
            conn.close()
            return jsonify({
                "success": False, 
                "message": "Incorrect password. Please try again.",
                "error_type": "wrong_password"
            }), 401
        
        # Check if user is active (if status column exists)
        if len(user) > 5 and user[5] != 'active':
            conn.close()
            return jsonify({
                "success": False, 
                "message": "Your account has been deactivated. Please contact support.",
                "error_type": "account_inactive"
            }), 403
        
        # Set session data
        session.permanent = data.get('remember_me', False)
        session['user_id'] = user[0]
        session['user_type'] = user[4]
        session['user_name'] = f"{user[2]} {user[3]}"
        session['email'] = email
        
        # Update last login if column exists
        if 'last_login' in columns:
            try:
                cursor.execute(
                    'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', 
                    (user[0],)
                )
                conn.commit()
            except Exception as e:
                print(f"Error updating last login: {e}")
        
        conn.close()
        
        # Log successful login
        try:
            AdminAction.log(
                admin_id=user[0],
                action_type='login',
                target_type='user',
                target_id=user[0],
                description=f"Successful login as {user_type}",
                ip_address=request.remote_addr
            )
        except Exception as e:
            print(f"Error logging admin action: {e}")
        
        return jsonify({
            "success": True, 
            "message": f"Welcome back, {user[2]}!",
            "user_type": user[4],
            "user_name": f"{user[2]} {user[3]}",
            "redirect": get_dashboard_url(user[4])
        })
            
    except Exception as e:
        print(f"Login API error: {e}")
        return jsonify({
            "success": False, 
            "message": "A technical error occurred. Please try again later.",
            "error_type": "server_error"
        }), 500

@app.route('/api/signup', methods=['POST'])
def api_signup():
    """User signup API"""
    try:
        data = request.form
        
        email = data.get('email')
        password = data.get('password')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        phone = data.get('phone')
        user_type = data.get('user_type', 'customer')
        
        if not all([email, password, first_name, last_name]):
            return jsonify({"success": False, "message": "All fields are required"}), 400
        
        # Check if user already exists
        conn = sqlite3.connect('barbershop.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        if cursor.fetchone():
            conn.close()
            return jsonify({"success": False, "message": "Email already registered"}), 409
        
        # Create user
        password_hash = hash_password(password)
        user_id = User.create(email, password_hash, first_name, last_name, phone, user_type)
        
        # Send welcome email
        try:
            from email_service import email_service
            email_service.send_welcome_email({
                'email': email,
                'first_name': first_name,
                'user_type': user_type
            })
        except Exception as e:
            print(f"Failed to send welcome email: {e}")
        
        conn.close()
        return jsonify({"success": True, "message": "Account created successfully"})
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Registration failed: {str(e)}"}), 500

# Super Admin API Routes
@app.route('/api/super-admin/stats')
def api_super_admin_stats():
    """Get real-time stats for super admin"""
    if session.get('user_type') != 'super_admin':
        return jsonify({"error": "Unauthorized"}), 403
    
    stats = get_admin_stats()
    return jsonify(stats)

@app.route('/api/super-admin/settings', methods=['POST'])
def api_save_settings():
    """Save system settings"""
    if session.get('user_type') != 'super_admin':
        return jsonify({"error": "Unauthorized"}), 403
    
    settings = request.json
    
    try:
        for key, value in settings.items():
            SystemSettings.set(key, value, session.get('user_id'))
        
        # Log action
        AdminAction.log(
            admin_id=session.get('user_id'),
            action_type='update',
            target_type='settings',
            target_id=0,
            description="Updated system settings",
            ip_address=request.remote_addr
        )
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/super-admin/users/<int:user_id>/status', methods=['POST'])
def api_toggle_user_status(user_id):
    """Toggle user status"""
    if session.get('user_type') != 'super_admin':
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.json
    new_status = data.get('status')
    
    try:
        User.update_status(user_id, new_status)
        
        # Log action
        AdminAction.log(
            admin_id=session.get('user_id'),
            action_type='update',
            target_type='user',
            target_id=user_id,
            description=f"Changed user status to {new_status}",
            ip_address=request.remote_addr
        )
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/super-admin/shops/<int:shop_id>/status', methods=['POST'])
def api_toggle_shop_status(shop_id):
    """Toggle shop status"""
    if session.get('user_type') != 'super_admin':
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.json
    new_status = data.get('status')
    
    try:
        Shop.update_status(shop_id, new_status)
        
        # Log action
        AdminAction.log(
            admin_id=session.get('user_id'),
            action_type='update',
            target_type='shop',
            target_id=shop_id,
            description=f"Changed shop status to {new_status}",
            ip_address=request.remote_addr
        )
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/super-admin/test-email', methods=['POST'])
def api_test_email():
    """Send test email"""
    if session.get('user_type') != 'super_admin':
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        # Get admin email
        conn = sqlite3.connect('barbershop.db')
        cursor = conn.cursor()
        cursor.execute('SELECT email FROM users WHERE id = ?', (session.get('user_id'),))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return jsonify({"success": False, "message": "Admin email not found"})
        
        admin_email = result[0]
        
        from email_service import email_service
        success = email_service.send_admin_notification(
            admin_email,
            "Test Email",
            "This is a test email from the BookaBarber system.",
            {"timestamp": datetime.now().isoformat()}
        )
        
        return jsonify({
            "success": success,
            "message": "Test email sent successfully!" if success else "Failed to send test email"
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/super-admin/optimize-db', methods=['POST'])
def api_optimize_database():
    """Optimize database"""
    if session.get('user_type') != 'super_admin':
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        conn = sqlite3.connect('barbershop.db')
        conn.execute('VACUUM')
        conn.close()
        
        # Log action
        AdminAction.log(
            admin_id=session.get('user_id'),
            action_type='system',
            target_type='database',
            target_id=0,
            description="Optimized database",
            ip_address=request.remote_addr
        )
        
        return jsonify({"success": True, "message": "Database optimized successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/super-admin/backup', methods=['POST'])
def api_backup_system():
    """Create system backup"""
    if session.get('user_type') != 'super_admin':
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        import shutil
        backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2('barbershop.db', backup_name)
        
        # Log action
        AdminAction.log(
            admin_id=session.get('user_id'),
            action_type='system',
            target_type='backup',
            target_id=0,
            description=f"Created backup: {backup_name}",
            ip_address=request.remote_addr
        )
        
        return send_file(backup_name, as_attachment=True)
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/notifications/mark-read/<int:notification_id>', methods=['POST'])
def api_mark_notification_read(notification_id):
    """Mark notification as read"""
    if not session.get('user_id'):
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        Notification.mark_as_read(notification_id)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/notifications/preview')
def api_notifications_preview():
    """Get notification preview for navbar"""
    if not session.get('user_id'):
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        notifications = Notification.get_by_user(session.get('user_id'), 5)  # Get latest 5
        unread_count = Notification.get_unread_count(session.get('user_id'))
        
        notification_data = []
        for notification in notifications:
            notification_data.append({
                'id': notification[0],
                'title': notification[2],
                'message': notification[3],
                'type': notification[4],
                'is_read': notification[5],
                'time': notification[7]
            })
        
        return jsonify({
            'notifications': notification_data,
            'unread_count': unread_count
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/available-slots')
def api_available_slots():
    """Get available time slots for a service and date"""
    try:
        service_id = request.args.get('service_id')
        date = request.args.get('date')
        
        if not service_id or not date:
            return jsonify({"success": False, "message": "Service ID and date are required"}), 400
        
        slots = find_available_slots(date, service_id)
        
        return jsonify({
            "success": True,
            "slots": slots
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/services')
def api_services():
    """Get all available services"""
    try:
        services = Service.get_all()
        
        service_list = []
        for service in services:
            service_list.append({
                'id': service[0],
                'name': service[1],
                'duration': service[2],
                'price': service[3],
                'shop_id': service[4],
                'shop_name': service[7] if len(service) > 7 else 'Unknown Shop',
                'description': service[6] if len(service) > 6 else ''
            })
        
        return jsonify({
            "success": True,
            "services": service_list
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/newsletter-subscribe', methods=['POST'])
def api_newsletter_subscribe():
    """Newsletter subscription API with CSV storage"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        name = data.get('name', 'Subscriber').strip()
        
        if not email:
            return jsonify({"success": False, "message": "Email is required"}), 400
        
        # Validate email format
        import re
        email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_pattern, email):
            return jsonify({"success": False, "message": "Invalid email format"}), 400
        
        # Save to CSV file
        import csv
        import os
        from datetime import datetime
        
        csv_file = 'newsletter_subscribers.csv'
        
        # Check if email already exists
        existing_emails = set()
        if os.path.exists(csv_file):
            with open(csv_file, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    existing_emails.add(row.get('email', '').lower())
        
        if email.lower() in existing_emails:
            return jsonify({"success": False, "message": "Email already subscribed"}), 409
        
        # Append to CSV
        file_exists = os.path.exists(csv_file)
        with open(csv_file, 'a', newline='', encoding='utf-8') as file:
            fieldnames = ['email', 'name', 'subscribed_at', 'ip_address', 'user_agent']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            
            # Write header if file is new
            if not file_exists:
                writer.writeheader()
            
            # Write subscriber data
            writer.writerow({
                'email': email,
                'name': name,
                'subscribed_at': datetime.now().isoformat(),
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', '')
            })
        
        # Log to database if needed
        try:
            conn = sqlite3.connect('barbershop.db')
            cursor = conn.cursor()
            
            # Create newsletter table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS newsletter_subscribers (
                    id INTEGER PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    name TEXT,
                    subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    status TEXT DEFAULT 'active'
                )
            ''')
            
            # Insert subscriber
            cursor.execute('''
                INSERT OR IGNORE INTO newsletter_subscribers (email, name, ip_address)
                VALUES (?, ?, ?)
            ''', (email, name, request.remote_addr))
            
            conn.commit()
            conn.close()
        except Exception as db_error:
            print(f"Database error (newsletter): {db_error}")
            # Continue even if database fails, CSV is primary storage
        
        return jsonify({
            "success": True,
            "message": "Successfully subscribed to newsletter"
        })
        
    except Exception as e:
        print(f"Newsletter subscription error: {e}")
        return jsonify({
            "success": False,
            "message": "Subscription failed. Please try again."
        }), 500

# Super Admin route to view newsletter subscribers
@app.route('/api/super-admin/newsletter-subscribers')
def api_get_newsletter_subscribers():
    """Get newsletter subscribers for super admin"""
    if session.get('user_type') != 'super_admin':
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        import csv
        import os
        
        subscribers = []
        csv_file = 'newsletter_subscribers.csv'
        
        if os.path.exists(csv_file):
            with open(csv_file, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    subscribers.append({
                        'email': row.get('email', ''),
                        'name': row.get('name', ''),
                        'subscribed_at': row.get('subscribed_at', ''),
                        'ip_address': row.get('ip_address', '')
                    })
        
        return jsonify({
            "success": True,
            "subscribers": subscribers,
            "total": len(subscribers)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Add these routes to app.py

@app.route('/api/super-admin/newsletter-export')
def api_export_newsletter_subscribers():
    """Export newsletter subscribers as CSV for super admin"""
    if session.get('user_type') != 'super_admin':
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        import io
        import csv
        from flask import make_response
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Email', 'Name', 'Subscribed At', 'IP Address', 'User Agent'])
        
        # Read from CSV file
        csv_file = 'newsletter_subscribers.csv'
        if os.path.exists(csv_file):
            with open(csv_file, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    writer.writerow([
                        row.get('email', ''),
                        row.get('name', ''),
                        row.get('subscribed_at', ''),
                        row.get('ip_address', ''),
                        row.get('user_agent', '')
                    ])
        
        output.seek(0)
        
        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=newsletter_subscribers_{datetime.now().strftime("%Y%m%d")}.csv'
        
        # Log action
        AdminAction.log(
            admin_id=session.get('user_id'),
            action_type='export',
            target_type='newsletter',
            target_id=0,
            description="Exported newsletter subscribers",
            ip_address=request.remote_addr
        )
        
        return response
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/super-admin/newsletter-remove', methods=['POST'])
def api_remove_newsletter_subscriber():
    """Remove newsletter subscriber for super admin"""
    if session.get('user_type') != 'super_admin':
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        data = request.get_json()
        email_to_remove = data.get('email', '').strip().lower()
        
        if not email_to_remove:
            return jsonify({"success": False, "message": "Email is required"}), 400
        
        import csv
        import tempfile
        import shutil
        
        csv_file = 'newsletter_subscribers.csv'
        
        if not os.path.exists(csv_file):
            return jsonify({"success": False, "message": "No subscribers found"}), 404
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, newline='', encoding='utf-8')
        
        removed = False
        with open(csv_file, 'r', newline='', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            fieldnames = reader.fieldnames
            
            writer = csv.DictWriter(temp_file, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in reader:
                if row.get('email', '').lower() != email_to_remove:
                    writer.writerow(row)
                else:
                    removed = True
        
        temp_file.close()
        
        if removed:
            # Replace original file with temp file
            shutil.move(temp_file.name, csv_file)
            
            # Also remove from database if exists
            try:
                conn = sqlite3.connect('barbershop.db')
                cursor = conn.cursor()
                cursor.execute('DELETE FROM newsletter_subscribers WHERE email = ?', (email_to_remove,))
                conn.commit()
                conn.close()
            except Exception as db_error:
                print(f"Database error (newsletter removal): {db_error}")
            
            # Log action
            AdminAction.log(
                admin_id=session.get('user_id'),
                action_type='delete',
                target_type='newsletter',
                target_id=0,
                description=f"Removed newsletter subscriber: {email_to_remove}",
                ip_address=request.remote_addr
            )
            
            return jsonify({"success": True, "message": "Subscriber removed successfully"})
        else:
            os.unlink(temp_file.name)  # Clean up temp file
            return jsonify({"success": False, "message": "Subscriber not found"}), 404
            
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# Helper functions
def get_dashboard_url(user_type):
    """Get the appropriate dashboard URL for user type"""
    dashboard_map = {
        'customer': 'user_dashboard',
        'barber': 'barber_admin',
        'shop_owner': 'shop_owner_admin',
        'super_admin': 'super_admin'
    }
    return url_for(dashboard_map.get(user_type, 'home'))

def get_admin_stats():
    """Get statistics for admin dashboard"""
    conn = sqlite3.connect('barbershop.db')
    cursor = conn.cursor()
    
    # Total shops
    cursor.execute('SELECT COUNT(*) FROM shops')
    total_shops = cursor.fetchone()[0]
    
    # Active shops
    cursor.execute('SELECT COUNT(*) FROM shops WHERE status = "active"')
    active_shops = cursor.fetchone()[0]
    
    # Total users
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    
    # Total customers
    cursor.execute('SELECT COUNT(*) FROM users WHERE user_type = "customer"')
    customers = cursor.fetchone()[0]
    
    # Total bookings
    cursor.execute('SELECT COUNT(*) FROM bookings')
    total_bookings = cursor.fetchone()[0]
    
    # Bookings today
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute('SELECT COUNT(*) FROM bookings WHERE date = ?', (today,))
    bookings_today = cursor.fetchone()[0]
    
    # Revenue (simulated)
    cursor.execute('SELECT SUM(total_price) FROM bookings WHERE status = "completed"')
    total_revenue = cursor.fetchone()[0] or 0
    
    # Revenue this month
    this_month = datetime.now().strftime('%Y-%m')
    cursor.execute('SELECT SUM(total_price) FROM bookings WHERE date LIKE ? AND status = "completed"', (f"{this_month}%",))
    revenue_this_month = cursor.fetchone()[0] or 0
    
    conn.close()
    
    return {
        'total_shops': total_shops,
        'active_shops': active_shops,
        'total_users': total_users,
        'customers': customers,
        'total_bookings': total_bookings,
        'bookings_today': bookings_today,
        'total_revenue': total_revenue,
        'revenue_this_month': revenue_this_month
    }

def get_email_logs(limit=50):
    """Get email logs"""
    conn = sqlite3.connect('barbershop.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM email_logs ORDER BY created_at DESC LIMIT ?', (limit,))
    logs = cursor.fetchall()
    conn.close()
    return logs

def get_barber_stats(user_id):
    """Get statistics for barber dashboard"""
    conn = sqlite3.connect('barbershop.db')
    cursor = conn.cursor()
    
    # Get barber ID from user ID
    cursor.execute('SELECT id FROM barbers WHERE user_id = ?', (user_id,))
    barber_result = cursor.fetchone()
    
    if not barber_result:
        return {}
    
    barber_id = barber_result[0]
    
    # Get today's bookings
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute('SELECT COUNT(*) FROM bookings WHERE barber_id = ? AND date = ?', (barber_id, today))
    today_bookings = cursor.fetchone()[0]
    
    # Get this week's bookings
    cursor.execute('''
        SELECT COUNT(*) FROM bookings 
        WHERE barber_id = ? AND date >= date('now', 'weekday 0', '-6 days')
    ''', (barber_id,))
    week_bookings = cursor.fetchone()[0]
    
    # Get total earnings this month
    this_month = datetime.now().strftime('%Y-%m')
    cursor.execute('''
        SELECT SUM(total_price) FROM bookings 
        WHERE barber_id = ? AND date LIKE ? AND status = 'completed'
    ''', (barber_id, f"{this_month}%"))
    month_earnings = cursor.fetchone()[0] or 0
    
    conn.close()
    
    return {
        'today_bookings': today_bookings,
        'week_bookings': week_bookings,
        'month_earnings': month_earnings
    }

def get_shop_owner_stats(user_id):
    """Get statistics for shop owner dashboard"""
    conn = sqlite3.connect('barbershop.db')
    cursor = conn.cursor()
    
    # Get shop ID from user ID
    cursor.execute('SELECT shop_id FROM users WHERE id = ?', (user_id,))
    shop_result = cursor.fetchone()
    
    if not shop_result or not shop_result[0]:
        return {}
    
    shop_id = shop_result[0]
    
    # Get total barbers
    cursor.execute('SELECT COUNT(*) FROM barbers WHERE shop_id = ?', (shop_id,))
    total_barbers = cursor.fetchone()[0]
    
    # Get today's bookings
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute('SELECT COUNT(*) FROM bookings WHERE shop_id = ? AND date = ?', (shop_id, today))
    today_bookings = cursor.fetchone()[0]
    
    # Get this month's revenue
    this_month = datetime.now().strftime('%Y-%m')
    cursor.execute('''
        SELECT SUM(total_price) FROM bookings 
        WHERE shop_id = ? AND date LIKE ? AND status = 'completed'
    ''', (shop_id, f"{this_month}%"))
    month_revenue = cursor.fetchone()[0] or 0
    
    conn.close()
    
    return {
        'total_barbers': total_barbers,
        'today_bookings': today_bookings,
        'month_revenue': month_revenue
    }

@app.route('/forgot-password')
def forgot_password():
    """Forgot password page"""
    if session.get('user_id'):
        return redirect(url_for('home'))
    return render_template('forgot_password.html')

@app.route('/api/forgot-password', methods=['POST'])
def api_forgot_password():
    """Send password reset email"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({"success": False, "message": "Email is required"}), 400
        
        # Check if user exists
        conn = sqlite3.connect('barbershop.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, first_name, last_name FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            # For security, don't reveal if email exists or not
            return jsonify({
                "success": True, 
                "message": "If an account with this email exists, you will receive a reset link shortly."
            })
        
        user_id, first_name, last_name = user
        
        # Generate reset token (in production, use proper token generation)
        import secrets
        import time
        reset_token = secrets.token_urlsafe(32)
        expires_at = int(time.time()) + 3600  # 1 hour from now
        
        # Store reset token in database
        conn = sqlite3.connect('barbershop.db')
        cursor = conn.cursor()
        
        # Create password_resets table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS password_resets (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                token TEXT NOT NULL,
                expires_at INTEGER NOT NULL,
                used BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Insert reset token
        cursor.execute('''
            INSERT INTO password_resets (user_id, token, expires_at)
            VALUES (?, ?, ?)
        ''', (user_id, reset_token, expires_at))
        
        conn.commit()
        conn.close()
        
        # Send reset email
        try:
            from email_service import email_service
            reset_link = f"{request.host_url}reset-password?token={reset_token}"
            
            success = email_service.send_password_reset_email({
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'reset_link': reset_link
            })
            
            if success:
                # Log admin action
                AdminAction.log(
                    admin_id=0,  # System action
                    action_type='password_reset',
                    target_type='user',
                    target_id=user_id,
                    description=f"Password reset requested for {email}",
                    ip_address=request.remote_addr
                )
                
                return jsonify({
                    "success": True,
                    "message": "Password reset email sent successfully!"
                })
            else:
                return jsonify({
                    "success": False,
                    "message": "Failed to send email. Please try again later."
                }), 500
                
        except Exception as email_error:
            print(f"Email sending error: {email_error}")
            return jsonify({
                "success": False,
                "message": "Failed to send email. Please try again later."
            }), 500
            
    except Exception as e:
        print(f"Forgot password error: {e}")
        return jsonify({
            "success": False,
            "message": "An error occurred. Please try again."
        }), 500

@app.route('/reset-password')
def reset_password():
    """Reset password page with token"""
    token = request.args.get('token')
    
    if not token:
        flash('Invalid reset link', 'error')
        return redirect(url_for('forgot_password'))
    
    # Verify token
    conn = sqlite3.connect('barbershop.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT pr.id, pr.user_id, pr.expires_at, pr.used, u.email, u.first_name
        FROM password_resets pr
        JOIN users u ON pr.user_id = u.id
        WHERE pr.token = ?
    ''', (token,))
    
    reset_data = cursor.fetchone()
    conn.close()
    
    if not reset_data:
        flash('Invalid reset link', 'error')
        return redirect(url_for('forgot_password'))
    
    reset_id, user_id, expires_at, used, email, first_name = reset_data
    
    # Check if token is expired
    import time
    if int(time.time()) > expires_at:
        flash('Reset link has expired. Please request a new one.', 'error')
        return redirect(url_for('forgot_password'))
    
    # Check if token is already used
    if used:
        flash('Reset link has already been used. Please request a new one.', 'error')
        return redirect(url_for('forgot_password'))
    
    return render_template('reset_password.html', 
                         token=token, 
                         email=email, 
                         first_name=first_name)

@app.route('/api/reset-password', methods=['POST'])
def api_reset_password():
    """Reset password with token"""
    try:
        data = request.get_json()
        token = data.get('token')
        new_password = data.get('password')
        confirm_password = data.get('confirm_password')
        
        if not all([token, new_password, confirm_password]):
            return jsonify({"success": False, "message": "All fields are required"}), 400
        
        if new_password != confirm_password:
            return jsonify({"success": False, "message": "Passwords do not match"}), 400
        
        if len(new_password) < 6:
            return jsonify({"success": False, "message": "Password must be at least 6 characters long"}), 400
        
        # Verify token
        conn = sqlite3.connect('barbershop.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT pr.id, pr.user_id, pr.expires_at, pr.used
            FROM password_resets pr
            WHERE pr.token = ?
        ''', (token,))
        
        reset_data = cursor.fetchone()
        
        if not reset_data:
            conn.close()
            return jsonify({"success": False, "message": "Invalid reset token"}), 400
        
        reset_id, user_id, expires_at, used = reset_data
        
        # Check if token is expired
        import time
        if int(time.time()) > expires_at:
            conn.close()
            return jsonify({"success": False, "message": "Reset token has expired"}), 400
        
        # Check if token is already used
        if used:
            conn.close()
            return jsonify({"success": False, "message": "Reset token has already been used"}), 400
        
        # Update password
        password_hash = hash_password(new_password)
        cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?', (password_hash, user_id))
        
        # Mark token as used
        cursor.execute('UPDATE password_resets SET used = TRUE WHERE id = ?', (reset_id,))
        
        conn.commit()
        conn.close()
        
        # Log admin action
        AdminAction.log(
            admin_id=user_id,
            action_type='password_change',
            target_type='user',
            target_id=user_id,
            description="Password reset completed",
            ip_address=request.remote_addr
        )
        
        return jsonify({
            "success": True,
            "message": "Password reset successfully! You can now log in with your new password."
        })
        
    except Exception as e:
        print(f"Reset password error: {e}")
        return jsonify({
            "success": False,
            "message": "An error occurred. Please try again."
        }), 500

@app.before_request
def check_session():
    """Check session validity before each request"""
    # Skip session check for static files and auth routes
    if (request.endpoint and 
        (request.endpoint.startswith('static') or 
         request.endpoint in ['login', 'signup', 'home', 'api_login', 'api_signup', 'forgot_password', 'reset_password'])):
        return
    
    # Check if user session is valid
    if session.get('user_id'):
        try:
            conn = sqlite3.connect('barbershop.db')
            cursor = conn.cursor()
            cursor.execute('SELECT status FROM users WHERE id = ?', (session.get('user_id'),))
            user = cursor.fetchone()
            conn.close()
            
            if not user or user[0] != 'active':
                session.clear()
                flash('Your session has expired. Please log in again.', 'warning')
                return redirect(url_for('login'))
        except Exception as e:
            print(f"Session check error: {e}")
            session.clear()
            return redirect(url_for('login'))

@app.route('/api/location-services')
def api_location_services():
    """Get available location services and fallback options"""
    try:
        # You can add multiple geocoding services as fallback
        services = [
            {
                'name': 'OpenStreetMap',
                'status': 'active',
                'url': 'https://nominatim.openstreetmap.org'
            }
        ]
        
        return jsonify({
            "success": True,
            "services": services,
            "fallback_enabled": True
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/nearby-barbers')
def api_nearby_barbers():
    """Get nearby barbers based on location"""
    try:
        location = request.args.get('location', '')
        radius = request.args.get('radius', '10')
        
        # For demo purposes, return sample data
        # In a real app, you'd geocode the location and find actual nearby barbers
        sample_barbers = [
            {
                'id': 1,
                'name': 'John Smith',
                'shop_name': 'Elite Cuts',
                'rating': 4.8,
                'distance': '0.5 km',
                'specialization': 'Classic Cuts, Beard Styling',
                'price_range': '$15-30',
                'available_today': True,
                'address': '123 Main St',
                'phone': '+1-234-567-8900'
            },
            {
                'id': 2,
                'name': 'Mike Johnson',
                'shop_name': 'The Barber Shop',
                'rating': 4.6,
                'distance': '1.2 km',
                'specialization': 'Modern Styles, Fades',
                'price_range': '$20-35',
                'available_today': True,
                'address': '456 Oak Ave',
                'phone': '+1-234-567-8901'
            },
            {
                'id': 3,
                'name': 'David Wilson',
                'shop_name': 'Gentleman\'s Choice',
                'rating': 4.9,
                'distance': '2.1 km',
                'specialization': 'Traditional Shaves, Mustache',
                'price_range': '$25-40',
                'available_today': False,
                'address': '789 Pine St',
                'phone': '+1-234-567-8902'
            }
        ]
        
        return jsonify(sample_barbers)
        
    except Exception as e:
        print(f"Error finding nearby barbers: {e}")
        return jsonify([]), 500

@app.route('/api/reverse-geocode')
def api_reverse_geocode():
    """Reverse geocoding proxy to avoid CORS issues"""
    try:
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        
        if not lat or not lon:
            return jsonify({"error": "Latitude and longitude are required"}), 400
        
        # Use OpenStreetMap Nominatim API
        url = f"https://nominatim.openstreetmap.org/reverse"
        params = {
            'format': 'json',
            'lat': lat,
            'lon': lon,
            'zoom': 14,
            'addressdetails': 1
        }
        
        headers = {
            'User-Agent': 'BookaBarber/1.0 (barbershop-booking-system)'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Format the address nicely
            if 'display_name' in data:
                address_parts = data['display_name'].split(',')
                # Take first 3-4 meaningful parts
                short_address = ', '.join(address_parts[:3]).strip()
                
                return jsonify({
                    "success": True,
                    "address": short_address,
                    "full_address": data['display_name'],
                    "city": data.get('address', {}).get('city', ''),
                    "country": data.get('address', {}).get('country', '')
                })
            else:
                return jsonify({
                    "success": True,
                    "address": f"{lat}, {lon}",
                    "full_address": f"{lat}, {lon}",
                    "city": "",
                    "country": ""
                })
        else:
            return jsonify({"error": "Geocoding service unavailable"}), 503
            
    except requests.exceptions.Timeout:
        return jsonify({"error": "Geocoding request timed out"}), 504
    except requests.exceptions.RequestException as e:
        print(f"Geocoding error: {e}")
        return jsonify({"error": "Geocoding service error"}), 503
    except Exception as e:
        print(f"Reverse geocoding error: {e}")
        return jsonify({"error": "Internal server error"}), 500

def update_users_table():
    """Update users table to add missing columns"""
    conn = sqlite3.connect('barbershop.db')
    cursor = conn.cursor()
    
    try:
        # Check if status column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'status' not in columns:
            print("Adding status column to users table...")
            cursor.execute('ALTER TABLE users ADD COLUMN status TEXT DEFAULT "active"')
            print("Status column added successfully!")
        
        # Check if last_login column exists
        if 'last_login' not in columns:
            print("Adding last_login column to users table...")
            cursor.execute('ALTER TABLE users ADD COLUMN last_login TIMESTAMP')
            print("Last_login column added successfully!")
        
        # Update existing users to have active status
        cursor.execute('UPDATE users SET status = "active" WHERE status IS NULL OR status = ""')
        
        conn.commit()
        print("Users table updated successfully!")
        
    except Exception as e:
        print(f"Error updating users table: {e}")
        conn.rollback()
    finally:
        conn.close()

def update_bookings_table():
    """Update bookings table to add missing columns"""
    conn = sqlite3.connect('barbershop.db')
    cursor = conn.cursor()
    
    try:
        # Check if status column exists in bookings table
        cursor.execute("PRAGMA table_info(bookings)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'status' not in columns:
            print("Adding status column to bookings table...")
            cursor.execute('ALTER TABLE bookings ADD COLUMN status TEXT DEFAULT "pending"')
            print("Status column added successfully!")
        
        # Update existing bookings to have pending status
        cursor.execute('UPDATE bookings SET status = "pending" WHERE status IS NULL OR status = ""')
        
        conn.commit()
        print("Bookings table updated successfully!")
        
    except Exception as e:
        print(f"Error updating bookings table: {e}")
        conn.rollback()
    finally:
        conn.close()

def update_database_schema():
    """Update database schema to add all missing columns"""
    conn = sqlite3.connect('barbershop.db')
    cursor = conn.cursor()
    
    try:
        print("Updating database schema...")
        
        # Update users table
        cursor.execute("PRAGMA table_info(users)")
        user_columns = [column[1] for column in cursor.fetchall()]
        
        if 'status' not in user_columns:
            print("Adding status column to users table...")
            cursor.execute('ALTER TABLE users ADD COLUMN status TEXT DEFAULT "active"')
        
        if 'last_login' not in user_columns:
            print("Adding last_login column to users table...")
            cursor.execute('ALTER TABLE users ADD COLUMN last_login TIMESTAMP')
        
        # Update bookings table
        cursor.execute("PRAGMA table_info(bookings)")
        booking_columns = [column[1] for column in cursor.fetchall()]
        
        if 'status' not in booking_columns:
            print("Adding status column to bookings table...")
            cursor.execute('ALTER TABLE bookings ADD COLUMN status TEXT DEFAULT "confirmed"')
        
        # Update customers table
        cursor.execute("PRAGMA table_info(customers)")
        customer_columns = [column[1] for column in cursor.fetchall()]
        
        if 'user_id' not in customer_columns:
            print("Adding user_id column to customers table...")
            cursor.execute('ALTER TABLE customers ADD COLUMN user_id INTEGER')
            # Note: SQLite doesn't support adding foreign key constraints to existing tables
        
        # Update admin_actions table
        cursor.execute("PRAGMA table_info(admin_actions)")
        admin_columns = [column[1] for column in cursor.fetchall()]
        
        if 'ip_address' not in admin_columns:
            print("Adding ip_address column to admin_actions table...")
            cursor.execute('ALTER TABLE admin_actions ADD COLUMN ip_address TEXT')
        
        # Update existing records with default values
        cursor.execute('UPDATE users SET status = "active" WHERE status IS NULL OR status = ""')
        cursor.execute('UPDATE bookings SET status = "confirmed" WHERE status IS NULL OR status = ""')
        
        conn.commit()
        print("Database schema updated successfully!")
        
    except Exception as e:
        print(f"Error updating database schema: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

# Call this function after init_auth_tables()
update_database_schema()

@app.route('/help-center')
def help_center():
    return render_template('helpcenter.html')

@app.route('/contact-us')
def contact_us():
    return render_template('contactus.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy_policy.html')

@app.route('/terms-of-service')
def terms_of_service():
    return render_template('terms_of_service.html')

if __name__ == '__main__':
    app.run(debug=True)