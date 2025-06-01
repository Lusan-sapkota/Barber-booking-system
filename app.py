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

def ensure_required_columns():
    """Ensure all required columns exist in database tables"""
    conn = sqlite3.connect('barbershop.db')
    cursor = conn.cursor()
    
    # Helper function to add column if it doesn't exist
    def add_column_if_not_exists(table, column, definition):
        try:
            # Check if column exists
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [info[1] for info in cursor.fetchall()]
            
            if column not in columns:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
                print(f"Added missing column {column} to {table}")
                conn.commit()
        except Exception as e:
            print(f"Error adding column {column} to {table}: {e}")
    
    # Add missing columns to barbers table
    add_column_if_not_exists('barbers', 'status', 'TEXT DEFAULT "active"')
    add_column_if_not_exists('barbers', 'rating', 'REAL DEFAULT 4.5')
    add_column_if_not_exists('barbers', 'total_bookings', 'INTEGER DEFAULT 0')
    add_column_if_not_exists('barbers', 'specialties', 'TEXT')
    
    # Add missing columns to other tables as needed
    add_column_if_not_exists('bookings', 'status', 'TEXT DEFAULT "confirmed"')
    add_column_if_not_exists('services', 'status', 'TEXT DEFAULT "active"')
    add_column_if_not_exists('shops', 'status', 'TEXT DEFAULT "active"')
    
    conn.close()

# Call the function to ensure columns exist
ensure_required_columns()

# Define password functions first
def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, password_hash):
    """Verify password against hash"""
    return hash_password(password) == password_hash

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
    
    # Check and add missing columns to existing tables
    def add_column_if_not_exists(table_name, column_name, column_definition):
        """Add column to table if it doesn't exist"""
        try:
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [column[1] for column in cursor.fetchall()]
            
            if column_name not in columns:
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")
                print(f"Added column {column_name} to {table_name} table")
        except sqlite3.OperationalError as e:
            print(f"Note: Could not add column {column_name} to {table_name}: {e}")
    
    # Add missing columns to barbers table
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='barbers'")
        if cursor.fetchone():
            # Table exists, check for missing columns
            add_column_if_not_exists('barbers', 'specialties', 'TEXT')
            add_column_if_not_exists('barbers', 'experience_years', 'INTEGER DEFAULT 0')
            add_column_if_not_exists('barbers', 'working_days', 'TEXT DEFAULT "Monday-Friday"')
            add_column_if_not_exists('barbers', 'start_time', 'TEXT DEFAULT "10:00"')
            add_column_if_not_exists('barbers', 'end_time', 'TEXT DEFAULT "16:00"')
            add_column_if_not_exists('barbers', 'rating', 'REAL DEFAULT 0.0')
            add_column_if_not_exists('barbers', 'total_bookings', 'INTEGER DEFAULT 0')
            add_column_if_not_exists('barbers', 'user_id', 'INTEGER')
    except sqlite3.OperationalError:
        pass
    
    # Add missing columns to services table
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='services'")
        if cursor.fetchone():
            add_column_if_not_exists('services', 'shop_id', 'INTEGER')
            add_column_if_not_exists('services', 'status', 'TEXT DEFAULT "active"')
            add_column_if_not_exists('services', 'description', 'TEXT')
    except sqlite3.OperationalError:
        pass
    
    # Add missing columns to shops table
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='shops'")
        if cursor.fetchone():
            add_column_if_not_exists('shops', 'owner_id', 'INTEGER')
            add_column_if_not_exists('shops', 'status', 'TEXT DEFAULT "active"')
    except sqlite3.OperationalError:
        pass
    
    # Add missing columns to bookings table
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bookings'")
        if cursor.fetchone():
            add_column_if_not_exists('bookings', 'shop_id', 'INTEGER')
            add_column_if_not_exists('bookings', 'total_price', 'REAL')
            add_column_if_not_exists('bookings', 'notes', 'TEXT')
    except sqlite3.OperationalError:
        pass
    
    # Insert demo users if they don't exist
    demo_users = [
        ('customer@demo.com', hash_password('password'), 'John', 'Customer', '+1-555-0123', 'customer', None),
        ('barber@demo.com', hash_password('password'), 'Mike', 'Barber', '+1-555-0124', 'barber', 1),
        ('owner@demo.com', hash_password('password'), 'Sarah', 'Owner', '+1-555-0125', 'shop_owner', 1),
        ('admin@demo.com', hash_password('password'), 'Admin', 'User', '+1-555-0126', 'super_admin', None)
    ]
    
    for user_data in demo_users:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO users (email, password_hash, first_name, last_name, phone, user_type, shop_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', user_data)
        except sqlite3.IntegrityError:
            pass  # User already exists
    
    # Create demo shop if it doesn't exist
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO shops (id, name, address, phone, email, owner_id, status)
            VALUES (1, 'Elite Barber Shop', '123 Main Street, Downtown', '+1-555-SHOP', 'info@elitebarbershop.com', 
                    (SELECT id FROM users WHERE email = 'owner@demo.com'), 'active')
        ''')
    except sqlite3.OperationalError:
        # Fallback if owner_id column doesn't exist yet
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO shops (id, name, address, phone, email)
                VALUES (1, 'Elite Barber Shop', '123 Main Street, Downtown', '+1-555-SHOP', 'info@elitebarbershop.com')
            ''')
        except sqlite3.IntegrityError:
            pass
    
    # Create demo barbers if they don't exist - with flexible column handling
    demo_barbers = [
        {
            'id': 1,
            'name': 'Mike Johnson',
            'shop_id': 1,
            'specialties': 'Classic cuts, Beard styling, Straight razor',
            'experience_years': 5,
            'status': 'active',
            'working_days': 'Monday-Saturday',
            'start_time': '09:00',
            'end_time': '18:00',
            'rating': 4.8,
            'total_bookings': 150
        },
        {
            'id': 2,
            'name': 'David Wilson',
            'shop_id': 1,
            'specialties': 'Modern cuts, Hair washing, Styling',
            'experience_years': 3,
            'status': 'active',
            'working_days': 'Tuesday-Sunday',
            'start_time': '10:00',
            'end_time': '17:00',
            'rating': 4.7,
            'total_bookings': 120
        },
        {
            'id': 3,
            'name': 'Alex Thompson',
            'shop_id': 1,
            'specialties': 'Trendy styles, Color treatments, Beard art',
            'experience_years': 4,
            'status': 'active',
            'working_days': 'Monday-Friday',
            'start_time': '08:00',
            'end_time': '16:00',
            'rating': 4.9,
            'total_bookings': 180
        }
    ]
    
    for barber_data in demo_barbers:
        try:
            # Check what columns exist in barbers table
            cursor.execute("PRAGMA table_info(barbers)")
            barber_columns = [column[1] for column in cursor.fetchall()]
            
            # Build INSERT query based on available columns
            available_fields = []
            values = []
            placeholders = []
            
            for field, value in barber_data.items():
                if field in barber_columns:
                    available_fields.append(field)
                    values.append(value)
                    placeholders.append('?')
            
            if available_fields:
                query = f'''
                    INSERT OR IGNORE INTO barbers ({', '.join(available_fields)})
                    VALUES ({', '.join(placeholders)})
                '''
                cursor.execute(query, values)
        except sqlite3.OperationalError as e:
            print(f"Note: Could not insert barber data: {e}")
    
    # Update barber user associations
    try:
        cursor.execute('UPDATE users SET shop_id = 1 WHERE email = "barber@demo.com"')
        cursor.execute('UPDATE barbers SET user_id = (SELECT id FROM users WHERE email = "barber@demo.com") WHERE id = 1')
    except sqlite3.OperationalError:
        pass
    
    # Create demo services if they don't exist
    demo_services = [
        {
            'id': 1,
            'name': 'Classic Haircut',
            'duration': 45,
            'price': 25.00,
            'shop_id': 1,
            'status': 'active',
            'description': 'Traditional haircut with scissors and clipper'
        },
        {
            'id': 2,
            'name': 'Premium Haircut & Wash',
            'duration': 60,
            'price': 35.00,
            'shop_id': 1,
            'status': 'active',
            'description': 'Haircut with premium shampoo and styling'
        },
        {
            'id': 3,
            'name': 'Beard Trim & Style',
            'duration': 30,
            'price': 20.00,
            'shop_id': 1,
            'status': 'active',
            'description': 'Professional beard trimming and styling'
        },
        {
            'id': 4,
            'name': 'Full Service Package',
            'duration': 90,
            'price': 50.00,
            'shop_id': 1,
            'status': 'active',
            'description': 'Haircut, beard trim, wash, and hot towel treatment'
        }
    ]
    
    for service_data in demo_services:
        try:
            # Check what columns exist in services table
            cursor.execute("PRAGMA table_info(services)")
            service_columns = [column[1] for column in cursor.fetchall()]
            
            # Build INSERT query based on available columns
            available_fields = []
            values = []
            placeholders = []
            
            for field, value in service_data.items():
                if field in service_columns:
                    available_fields.append(field)
                    values.append(value)
                    placeholders.append('?')
            
            if available_fields:
                query = f'''
                    INSERT OR IGNORE INTO services ({', '.join(available_fields)})
                    VALUES ({', '.join(placeholders)})
                '''
                cursor.execute(query, values)
        except sqlite3.OperationalError as e:
            print(f"Note: Could not insert service data: {e}")
    
    conn.commit()
    conn.close()
    print("Authentication tables initialized successfully!")

# Initialize auth tables
init_auth_tables()

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
    
    # Get shop owner's data
    shop_stats = get_shop_owner_stats(session.get('user_id'))
    today = datetime.now().strftime('%Y-%m-%d')
    
    return render_template('shop_owner_admin.html', stats=shop_stats, today=today)

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
    today = datetime.now().strftime('%Y-%m-%d')
    
    return render_template('shop_owner_admin.html', stats=shop_stats, today=today)

@app.route('/services')
def services():
    """Services page listing all available services"""
    conn = sqlite3.connect('barbershop.db')
    cursor = conn.cursor()
    
    # Get all services with categories
    cursor.execute('''
        SELECT id, name, duration, price, description, 
               CASE 
                   WHEN name LIKE '%haircut%' THEN 'Haircut'
                   WHEN name LIKE '%beard%' THEN 'Beard'
                   WHEN name LIKE '%facial%' OR name LIKE '%treatment%' THEN 'Treatment'
                   WHEN name LIKE '%color%' OR name LIKE '%dye%' THEN 'Coloring'
                   WHEN name LIKE '%package%' OR name LIKE '%premium%' THEN 'Package'
                   ELSE 'Other'
               END as category
        FROM services
        WHERE status = 'active'
        ORDER BY category, price
    ''')
    
    all_services = cursor.fetchall()
    conn.close()
    
    # Group by category
    service_categories = {}
    for service in all_services:
        category = service[5]
        if category not in service_categories:
            service_categories[category] = []
        service_categories[category].append({
            'id': service[0],
            'name': service[1],
            'duration': service[2],
            'price': service[3],
            'description': service[4]
        })
    
    return render_template('services.html', service_categories=service_categories)

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
    """Mark a notification as read"""
    if not session.get('user_id'):
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        user_id = session.get('user_id')
        
        # Make sure the notification belongs to this user
        conn = sqlite3.connect('barbershop.db')
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT id FROM notifications WHERE id = ? AND user_id = ?', 
            (notification_id, user_id)
        )
        
        if not cursor.fetchone():
            conn.close()
            return jsonify({"error": "Notification not found"}), 404
        
        # Update the notification
        cursor.execute(
            'UPDATE notifications SET is_read = 1 WHERE id = ?',
            (notification_id,)
        )
        
        conn.commit()
        conn.close()
        
        # Get updated unread count
        unread_count = Notification.get_unread_count(user_id)
        
        return jsonify({
            'success': True,
            'message': 'Notification marked as read',
            'unread_count': unread_count
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/notifications/get')
def api_get_notifications():
    """Get all notifications for current user"""
    if not session.get('user_id'):
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        user_id = session.get('user_id')
        notifications = Notification.get_by_user(user_id)
        unread_count = Notification.get_unread_count(user_id)
        
        notification_list = []
        for notification in notifications:
            notification_list.append({
                'id': notification[0],
                'user_id': notification[1],
                'title': notification[2],
                'message': notification[3],
                'action_url': notification[4],
                'type': notification[5],
                'is_read': notification[6],
                'created_at': notification[7]
            })
        
        return jsonify({
            'success': True,
            'notifications': notification_list,
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
        # If no shop_id, try to find shop owned by this user
        cursor.execute('SELECT id FROM shops WHERE owner_id = ?', (user_id,))
        owner_shop = cursor.fetchone()
        shop_id = owner_shop[0] if owner_shop else 1  # Default to shop 1
    else:
        shop_id = shop_result[0]
    
    # Get total barbers - check if status column exists
    try:
        cursor.execute('SELECT COUNT(*) FROM barbers WHERE shop_id = ? AND status = "active"', (shop_id,))
        total_barbers = cursor.fetchone()[0]
    except sqlite3.OperationalError:
        # Fallback if status column doesn't exist
        cursor.execute('SELECT COUNT(*) FROM barbers WHERE shop_id = ?', (shop_id,))
        total_barbers = cursor.fetchone()[0]
    
    # Get today's bookings
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute('''
        SELECT COUNT(*) FROM bookings b 
        JOIN barbers br ON b.barber_id = br.id 
        WHERE br.shop_id = ? AND b.date = ?
    ''', (shop_id, today))
    today_bookings = cursor.fetchone()[0]
    
    # Get this month's revenue
    this_month = datetime.now().strftime('%Y-%m')
    cursor.execute('''
        SELECT SUM(b.total_price) FROM bookings b
        JOIN barbers br ON b.barber_id = br.id
        WHERE br.shop_id = ? AND b.date LIKE ?
    ''', (shop_id, f"{this_month}%"))
    month_revenue = cursor.fetchone()[0] or 0
    
    # Get average rating - check if rating column exists
    try:
        cursor.execute('SELECT AVG(rating) FROM barbers WHERE shop_id = ?', (shop_id,))
        avg_rating = cursor.fetchone()[0] or 4.5
    except sqlite3.OperationalError:
        avg_rating = 4.5  # Default value if rating column doesn't exist
    
    # Get recent bookings
    cursor.execute('''
        SELECT b.*, s.name as service_name, br.name as barber_name, c.name as customer_name
        FROM bookings b
        JOIN services s ON b.service_id = s.id
        JOIN barbers br ON b.barber_id = br.id
        JOIN customers c ON b.customer_id = c.id
        WHERE br.shop_id = ? AND b.date >= date('now')
        ORDER BY b.date ASC, b.start_time ASC
        LIMIT 10
    ''', (shop_id,))
    recent_bookings = cursor.fetchall()
    
    # Get barber performance data - safely handle status column
    try:
        cursor.execute('''
            SELECT br.id, br.name, br.rating, br.total_bookings, br.specialties,
                   COUNT(b.id) as today_appointments
            FROM barbers br
            LEFT JOIN bookings b ON br.id = b.barber_id AND b.date = ?
            WHERE br.shop_id = ? AND br.status = "active"
            GROUP BY br.id
        ''', (today, shop_id))
    except sqlite3.OperationalError:
        # Fallback if status column doesn't exist
        cursor.execute('''
            SELECT br.id, br.name, COALESCE(br.rating, 4.5) as rating, 
                   COALESCE(br.total_bookings, 0) as total_bookings, 
                   COALESCE(br.specialties, 'General Services') as specialties,
                   COUNT(b.id) as today_appointments
            FROM barbers br
            LEFT JOIN bookings b ON br.id = b.barber_id AND b.date = ?
            WHERE br.shop_id = ?
            GROUP BY br.id
        ''', (today, shop_id))
    
    barber_performance = cursor.fetchall()
    
    conn.close()
    
    return {
        'shop_id': shop_id,
        'total_barbers': total_barbers,
        'today_bookings': today_bookings,
        'month_revenue': round(month_revenue, 2),
        'avg_rating': round(avg_rating, 1),
        'recent_bookings': recent_bookings,
        'barber_performance': barber_performance
    }

# Add new API endpoints for shop owner dashboard
@app.route('/api/shop-owner/recent-bookings')
def api_shop_owner_recent_bookings():
    """Get recent bookings for shop owner"""
    if session.get('user_type') != 'shop_owner':
        return jsonify({"error": "Unauthorized"}), 403
    
    stats = get_shop_owner_stats(session.get('user_id'))
    return jsonify({"bookings": stats.get('recent_bookings', [])})

@app.route('/api/shop-owner/barber-performance')
def api_shop_owner_barber_performance():
    """Get barber performance data"""
    if session.get('user_type') != 'shop_owner':
        return jsonify({"error": "Unauthorized"}), 403
    
    stats = get_shop_owner_stats(session.get('user_id'))
    return jsonify({"barbers": stats.get('barber_performance', [])})

@app.route('/api/shop-owner/update-barber-status', methods=['POST'])
def api_update_barber_status():
    """Update barber status"""
    if session.get('user_type') != 'shop_owner':
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.json
    barber_id = data.get('barber_id')
    new_status = data.get('status')
    
    try:
        conn = sqlite3.connect('barbershop.db')
        cursor = conn.cursor()
        
        # Verify barber belongs to shop owner's shop
        user_id = session.get('user_id')
        cursor.execute('''
            SELECT b.id FROM barbers b
            JOIN shops s ON b.shop_id = s.id
            WHERE b.id = ? AND s.owner_id = ?
        ''', (barber_id, user_id))
        
        if cursor.fetchone():
            cursor.execute('UPDATE barbers SET status = ? WHERE id = ?', (new_status, barber_id))
            conn.commit()
            
            # Log action
            AdminAction.log(
                admin_id=user_id,
                action_type='update',
                target_type='barber',
                target_id=barber_id,
                description=f"Updated barber status to {new_status}",
                ip_address=request.remote_addr
            )
            
            conn.close()
            return jsonify({"success": True})
        else:
            conn.close()
            return jsonify({"error": "Barber not found"}), 404
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Add these routes for additional pages
@app.route('/contactus')
def contactus():
    """Contact us page"""
    return render_template('contactus.html')

@app.route('/faq')
def faq():
    """FAQ page"""
    return render_template('faq.html')

@app.route('/helpcenter')
def helpcenter():
    """Help center page"""
    return render_template('helpcenter.html')

@app.route('/forgot-password')
def forgot_password():
    """Forgot password page"""
    return render_template('forgot_password.html')

@app.route('/reset-password')
def reset_password():
    """Reset password page"""
    return render_template('reset_password.html')

# Add these routes for basic pages
@app.route('/privacy-policy')
def privacy_policy():
    """Privacy policy page"""
    return render_template('privacy_policy.html')

@app.route('/terms-of-service')
def terms_of_service():
    """Terms of service page"""
    return render_template('terms_of_service.html')

@app.route('/about')
def about():
    """About us page"""
    return render_template('about.html')

@app.route('/cookie-policy')
def cookie_policy():
    """Cookie policy page"""
    return render_template('cookie_policy.html')

@app.route('/placeholder')
def placeholder():
    """Placeholder page for features in development"""
    return render_template('placeholder.html', page_name="Coming Soon")

# API route for nearby barbers search
@app.route('/api/nearby-barbers')
def api_nearby_barbers():
    """Get nearby barbers based on location"""
    try:
        location = request.args.get('location', '')
        radius = request.args.get('radius', '10')
        
        conn = sqlite3.connect('barbershop.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT b.id, b.name, b.specialties, b.rating, b.total_bookings, 
                   b.working_days, b.start_time, b.end_time, s.name as shop_name,
                   s.address, s.phone
            FROM barbers b
            JOIN shops s ON b.shop_id = s.id
            WHERE b.status = 'active'
            ORDER BY b.rating DESC
        ''')
        
        barbers = cursor.fetchall()
        conn.close()
        
        # Format barber data
        barber_list = []
        for barber in barbers:
            barber_list.append({
                'id': barber[0],
                'name': barber[1],
                'specialties': barber[2] or 'General Services',
                'rating': barber[3] or 4.5,
                'total_bookings': barber[4] or 0,
                'working_days': barber[5] or 'Monday-Friday',
                'hours': f"{barber[6] or '10:00'} - {barber[7] or '16:00'}",
                'shop_name': barber[8] or 'Elite Barber Shop',
                'address': barber[9] or '123 Main Street',
                'phone': barber[10] or '+1-555-SHOP',
                'distance': f"{random.uniform(0.5, 15.0):.1f} km",  # Simulated distance
                'availability': 'Available' if random.random() > 0.3 else 'Busy'
            })
        
        return jsonify(barber_list)
        
    except Exception as e:
        print(f"Error in nearby barbers API: {e}")
        return jsonify([]), 500

# Geo reverse coding API (for location services)
@app.route('/api/reverse-geocode')
def api_reverse_geocode():
    """Convert latitude/longitude to human-readable address"""
    try:
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        
        if not lat or not lon:
            return jsonify({"success": False, "message": "Missing coordinates"}), 400
        
        # For demo purposes, we'll return a mock address
        # In production, you would use a real geocoding service
        mock_addresses = [
            "123 Main St, Anytown",
            "456 Elm Avenue, Springfield",
            "789 Oak Boulevard, Riverdale",
            "101 Pine Street, Lakeside",
            "202 Maple Drive, Hillcrest"
        ]
        
        selected_address = random.choice(mock_addresses)
        full_address = f"{selected_address}, USA"
        
        return jsonify({
            "success": True,
            "address": selected_address,
            "full_address": full_address,
            "lat": lat,
            "lon": lon
        })
        
    except Exception as e:
        print(f"Error in reverse geocode API: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

# SEO and utility routes
@app.route('/robots.txt')
def robots_txt():
    """Robots.txt for search engines"""
    return """User-agent: *
Disallow: /admin
Disallow: /super-admin
Disallow: /barber-admin
Disallow: /shop-admin
Disallow: /api/
Disallow: /user-dashboard
Allow: /

Sitemap: {}sitemap.xml""".format(request.host_url), 200, {'Content-Type': 'text/plain'}

@app.route('/sitemap.xml')
def sitemap_xml():
    """XML sitemap for SEO"""
    from urllib.parse import urljoin
    
    pages = [
        ('home', 1.0, 'daily'),
        ('booking_page', 0.9, 'daily'),
        ('find_nearby', 0.9, 'daily'),
        ('contactus', 0.7, 'monthly'),
        ('faq', 0.8, 'monthly'),
        ('helpcenter', 0.8, 'monthly'),
        ('about', 0.6, 'yearly'),
        ('privacy_policy', 0.5, 'yearly'),
        ('terms_of_service', 0.5, 'yearly'),
        ('cookie_policy', 0.4, 'yearly'),
    ]
    
    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    
    for page, priority, changefreq in pages:
        try:
            url = urljoin(request.host_url, url_for(page))
            xml.append(f'  <url>')
            xml.append(f'    <loc>{url}</loc>')
            xml.append(f'    <priority>{priority}</priority>')
            xml.append(f'    <changefreq>{changefreq}</changefreq>')
            xml.append(f'  </url>')
        except:
            continue  # Skip if route doesn't exist
    
    xml.append('</urlset>')
    
    return '\n'.join(xml), 200, {'Content-Type': 'application/xml'}

# Utility route for handling template creation
def ensure_template_exists(template_name, default_content=""):
    """Ensure that a template file exists, creating it with default content if needed"""
    template_path = os.path.join('templates', template_name)
    if not os.path.exists(template_path):
        os.makedirs(os.path.dirname(template_path), exist_ok=True)
        with open(template_path, 'w') as f:
            f.write(default_content)
        print(f"Created missing template: {template_name}")
    return True

# Dashboard/bookings redirect for logged-in users
@app.route('/dashboard')
def dashboard_redirect():
    """Redirect to appropriate dashboard based on user type"""
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    user_type = session.get('user_type')
    if user_type == 'customer':
        return redirect(url_for('user_dashboard'))
    elif user_type == 'barber':
        return redirect(url_for('barber_admin'))
    elif user_type == 'shop_owner':
        return redirect(url_for('shop_owner_admin'))
    elif user_type == 'super_admin':
        return redirect(url_for('super_admin'))
    else:
        return redirect(url_for('home'))


# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    try:
        return render_template('error.html', 
                             error_code=404, 
                             error_message="Page not found"), 404
    except:
        # Fallback if error template fails
        return '''
        <html>
        <head><title>404 - Page Not Found</title></head>
        <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
            <h1>404 - Page Not Found</h1>
            <p>The page you're looking for doesn't exist.</p>
            <a href="/" style="color: #007bff;">Go Home</a>
        </body>
        </html>
        ''', 404

@app.errorhandler(500)
def internal_server_error(e):
    """Handle 500 errors"""
    try:
        return render_template('error.html', 
                             error_code=500, 
                             error_message="Internal server error"), 500
    except:
        # Fallback if error template fails
        return '''
        <html>
        <head><title>500 - Server Error</title></head>
        <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
            <h1>500 - Server Error</h1>
            <p>Something went wrong on our end. Please try again later.</p>
            <a href="/" style="color: #007bff;">Go Home</a>
        </body>
        </html>
        ''', 500

@app.errorhandler(403)
def forbidden(e):
    """Handle 403 errors"""
    try:
        return render_template('error.html', 
                             error_code=403, 
                             error_message="Access forbidden"), 403
    except:
        # Fallback if error template fails
        return '''
        <html>
        <head><title>403 - Access Forbidden</title></head>
        <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
            <h1>403 - Access Forbidden</h1>
            <p>You don't have permission to access this resource.</p>
            <a href="/" style="color: #007bff;">Go Home</a>
        </body>
        </html>
        ''', 403

# Context processor for global template variables
@app.context_processor
def inject_global_vars():
    """Inject global variables into all templates"""
    return {
        'current_year': datetime.now().year,
        'app_name': 'BookaBarber',
        'app_version': '1.0.0'
    }

# Before request handler for session management
@app.before_request
def before_request():
    """Handle session and authentication before each request"""
    # Make session permanent if user is logged in
    if session.get('user_id'):
        session.permanent = True
    
    # Add CSRF protection for state-changing requests
    if request.method in ['POST', 'PUT', 'DELETE']:
        # Basic CSRF protection (you might want to implement proper CSRF tokens)
        pass

# After request handler for security headers
@app.after_request
def after_request(response):
    """Add security headers to all responses"""
    # Security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Cache control for static files
    if request.endpoint == 'static':
        response.headers['Cache-Control'] = 'public, max-age=31536000'
    
    return response

# Main application entry point
if __name__ == '__main__':
    # Development settings
    debug_mode = os.environ.get('FLASK_DEBUG', 'True').lower() in ['true', '1', 'yes']
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '127.0.0.1')
    
    print(f"🚀 Starting BookaBarber application...")
    print(f"📍 Server: http://{host}:{port}")
    print(f"🔧 Debug Mode: {debug_mode}")
    print(f"📊 Database: barbershop.db")
    print("\n🎯 Demo Accounts:")
    print("   Customer: customer@demo.com / password")
    print("   Barber: barber@demo.com / password") 
    print("   Shop Owner: owner@demo.com / password")
    print("   Super Admin: admin@demo.com / password")
    print("\n✨ Happy booking!")
    
    # Run the Flask application
    app.run(
        host=host,
        port=port,
        debug=debug_mode,
        threaded=True
    )