from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import sqlite3
from datetime import datetime, date
import hashlib
from models import init_db, Booking, Barber, Customer, Service
from algorithms import find_available_slots, optimize_barber_schedule
import os
import requests
import json
import random
from typing import Tuple, Optional
import math

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-default-secret-key')

# Initialize database
init_db()

# Add user authentication tables
def init_auth_tables():
    conn = sqlite3.connect('barbershop.db')
    cursor = conn.cursor()
    
    # Create users table for authentication
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        phone TEXT,
        user_type TEXT NOT NULL,
        shop_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize auth tables
init_auth_tables()

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, password_hash):
    """Verify password against hash"""
    return hash_password(password) == password_hash

# # Seed some initial data if needed
# def seed_data():
#     conn = sqlite3.connect('barbershop.db')
#     cursor = conn.cursor()
    
#     # Check if we already have data
#     cursor.execute("SELECT COUNT(*) FROM services")
#     if cursor.fetchone()[0] > 0:
#         conn.close()
#         return
    
#     # Add some shops first
#     shops_data = [
#         ("Downtown Cuts", "123 Main St, Downtown", "+1-555-0101", "downtown@cuts.com", 1),
#         ("Style Studio", "456 Oak Ave, Midtown", "+1-555-0102", "info@stylestudio.com", 1),
#         ("Classic Barber Shop", "789 Pine Rd, Uptown", "+1-555-0103", "classic@barber.com", 1),
#         ("Modern Cuts", "321 Elm St, Eastside", "+1-555-0104", "modern@cuts.com", 1),
#     ]
    
#     for shop in shops_data:
#         cursor.execute("""
#             INSERT INTO shops (name, address, phone, email, owner_id)
#             VALUES (?, ?, ?, ?, ?)
#         """, shop)
    
#     # Add services
#     services_data = [
#         ("Haircut", 30, 25.00, 1),
#         ("Haircut + Beard Trim", 45, 35.00, 1),
#         ("Beard Trim Only", 20, 15.00, 1),
#         ("Premium Package", 60, 50.00, 1),
#         ("Kids Haircut", 25, 20.00, 1),
#         ("Senior Haircut", 30, 20.00, 1)
#     ]
    
#     for service in services_data:
#         cursor.execute("""
#             INSERT INTO services (name, duration, price, shop_id)
#             VALUES (?, ?, ?, ?)
#         """, service)
    
#     # Add barbers
#     barbers_data = [
#         ("Mike Johnson", 1, "Haircuts, Beard styling"),
#         ("Sarah Wilson", 1, "Modern cuts, Color"),
#         ("David Brown", 2, "Classic cuts, Straight razor"),
#         ("Lisa Garcia", 2, "Trendy styles, Beard art"),
#         ("Tom Miller", 3, "Traditional cuts, Hot towel"),
#         ("Anna Davis", 3, "Creative styles, Fades"),
#         ("Chris Lee", 4, "Precision cuts, Styling"),
#         ("Maria Rodriguez", 4, "Hair design, Treatments")
#     ]
    
#     for barber in barbers_data:
#         cursor.execute("""
#             INSERT INTO barbers (name, shop_id, specialties)
#             VALUES (?, ?, ?)
#         """, barber)
    
#     conn.commit()
#     conn.close()
#     print("Sample data seeded successfully!")

# # Call seed data function when app starts
# seed_data()

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
    return render_template('admin.html')

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
    
    cursor.execute("""
        SELECT b.id, s.name, b.date, b.start_time, b.end_time, br.name as barber_name
        FROM bookings b
        JOIN services s ON b.service_id = s.id
        JOIN barbers br ON b.barber_id = br.id
        JOIN users u ON b.customer_id = u.id
        WHERE u.id = ?
        ORDER BY b.date DESC, b.start_time DESC
    """, (session['user_id'],))
    
    bookings = cursor.fetchall()
    conn.close()
    
    return render_template('user_dashboard.html', bookings=bookings)

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
    return render_template('shop_admin.html')

@app.route('/super-admin')
def super_admin():
    """Super admin panel"""
    if session.get('user_type') != 'super_admin':
        flash('You need to be a super admin to access this page', 'danger')
        return redirect(url_for('home'))
    return render_template('super_admin.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        email = request.form.get('email')
        password = request.form.get('password')
        user_type = request.form.get('user_type')
        
        if not all([email, password, user_type]):
            return jsonify({"success": False, "message": "All fields are required"}), 400
        
        # Verify user credentials
        conn = sqlite3.connect('barbershop.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, password_hash, first_name, last_name, user_type, shop_id
            FROM users WHERE email = ? AND user_type = ?
        """, (email, user_type))
        
        user = cursor.fetchone()
        conn.close()
        
        if user and verify_password(password, user[1]):
            # Set session data
            session['user_id'] = user[0]
            session['user_name'] = f"{user[2]} {user[3]}"
            session['user_type'] = user[4]
            session['shop_id'] = user[5]
            
            return jsonify({
                "success": True, 
                "message": "Login successful",
                "user_type": user[4]
            })
        else:
            return jsonify({"success": False, "message": "Invalid credentials"}), 401
            
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({"success": False, "message": "An error occurred during login"}), 500

@app.route('/api/slots', methods=['GET'])
def get_available_slots():
    date = request.args.get('date')
    service_id = request.args.get('service_id')
    
    # Validate inputs
    if not date or not service_id:
        return jsonify({"error": "Date and service_id are required"}), 400
    
    try:
        # Use our custom algorithm to find available slots
        slots = find_available_slots(date, service_id)
        return jsonify(slots)
    except Exception as e:
        print(f"Error finding slots: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/book', methods=['POST'])
def book_appointment():
    try:
        # Get data from request
        booking_data = request.json
        
        if not booking_data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        # Extract booking details
        date = booking_data.get('date')
        service_id = booking_data.get('service_id')
        barber_id = booking_data.get('barber_id')
        start_time = booking_data.get('time')
        customer_data = booking_data.get('customer', {})
        
        # Validate required fields
        if not all([date, service_id, barber_id, start_time, customer_data]):
            return jsonify({"success": False, "message": "Missing required booking information"}), 400
        
        # Connect to database
        conn = sqlite3.connect('barbershop.db')
        cursor = conn.cursor()
        
        # Check if the time slot is still available
        cursor.execute("""
            SELECT COUNT(*) FROM bookings 
            WHERE date = ? AND barber_id = ? AND start_time = ?
        """, (date, barber_id, start_time))
        
        if cursor.fetchone()[0] > 0:
            return jsonify({"success": False, "message": "This time slot is no longer available"}), 409
        
        # Get service duration to calculate end time
        cursor.execute("SELECT duration FROM services WHERE id = ?", (service_id,))
        service = cursor.fetchone()
        
        if not service:
            return jsonify({"success": False, "message": "Invalid service selected"}), 400
            
        service_duration = service[0] # Duration in minutes
        
        # Calculate end time
        from algorithms import time_to_minutes, minutes_to_time
        start_minutes = time_to_minutes(start_time)
        end_minutes = start_minutes + service_duration
        end_time = minutes_to_time(end_minutes)
        
        # Create or get customer
        customer_name = customer_data.get('name')
        customer_email = customer_data.get('email')
        customer_phone = customer_data.get('phone')
        
        cursor.execute("""
            SELECT id FROM customers WHERE email = ?
        """, (customer_email,))
        
        customer_result = cursor.fetchone()
        
        if customer_result:
            customer_id = customer_result[0]
            # Update customer info
            cursor.execute("""
                UPDATE customers SET name = ?, phone = ? WHERE id = ?
            """, (customer_name, customer_phone, customer_id))
        else:
            # Insert new customer
            cursor.execute("""
                INSERT INTO customers (name, email, phone) VALUES (?, ?, ?)
            """, (customer_name, customer_email, customer_phone))
            customer_id = cursor.lastrowid
        
        # Create booking
        cursor.execute("""
            INSERT INTO bookings (customer_id, barber_id, service_id, date, start_time, end_time)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (customer_id, barber_id, service_id, date, start_time, end_time))
        
        booking_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        # You could send confirmation email here
        
        return jsonify({
            "success": True, 
            "booking_id": booking_id,
            "message": "Appointment booked successfully"
        })
        
    except Exception as e:
        print(f"Error booking appointment: {e}")
        return jsonify({"success": False, "message": f"An error occurred: {str(e)}"}), 500

@app.route('/api/shops', methods=['GET'])
def get_shops():
    """API endpoint to get all active shops"""
    try:
        conn = sqlite3.connect('barbershop.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, address, phone, email 
            FROM shops 
            WHERE status = 'active'
            ORDER BY name
        """)
        
        shops = []
        for row in cursor.fetchall():
            shops.append({
                'id': row[0],
                'name': row[1],
                'address': row[2],
                'phone': row[3],
                'email': row[4]
            })
        
        conn.close()
        return jsonify(shops)
        
    except Exception as e:
        print(f"Error fetching shops: {e}")
        return jsonify({"error": "Failed to fetch shops"}), 500

@app.route('/api/geocode', methods=['POST'])
def geocode_address():
    """Convert address to coordinates using OpenStreetMap Nominatim API"""
    try:
        address = request.json.get('address')
        if not address:
            return jsonify({"success": False, "message": "Address is required"}), 400
        
        # Use OpenStreetMap Nominatim API (free)
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': address,
            'format': 'json',
            'limit': 1,
            'addressdetails': 1
        }
        headers = {
            'User-Agent': 'BookaBarber/1.0 (contact@bookabarber.com)'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=5)
        data = response.json()
        
        if data:
            location = data[0]
            return jsonify({
                "success": True,
                "coordinates": {
                    "lat": float(location['lat']),
                    "lng": float(location['lon'])
                },
                "formatted_address": location['display_name'],
                "city": location.get('address', {}).get('city', ''),
                "state": location.get('address', {}).get('state', ''),
                "country": location.get('address', {}).get('country', '')
            })
        else:
            return jsonify({"success": False, "message": "Location not found"}), 404
            
    except Exception as e:
        print(f"Geocoding error: {e}")
        return jsonify({"success": False, "message": "Geocoding service unavailable"}), 500

@app.route('/api/reverse-geocode', methods=['POST'])
def reverse_geocode():
    """Convert coordinates to address using OpenStreetMap Nominatim API"""
    try:
        data = request.json
        lat = data.get('lat')
        lng = data.get('lng')
        
        if not lat or not lng:
            return jsonify({"success": False, "message": "Coordinates are required"}), 400
        
        # Use OpenStreetMap Nominatim API (free)
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            'lat': lat,
            'lon': lng,
            'format': 'json',
            'addressdetails': 1
        }
        headers = {
            'User-Agent': 'BookaBarber/1.0 (contact@bookabarber.com)'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=5)
        data = response.json()
        
        if 'address' in data:
            address = data['address']
            city = address.get('city') or address.get('town') or address.get('village', '')
            state = address.get('state', '')
            
            return jsonify({
                "success": True,
                "formatted_address": data['display_name'],
                "city": city,
                "state": state,
                "country": address.get('country', ''),
                "coordinates": {
                    "lat": float(lat),
                    "lng": float(lng)
                }
            })
        else:
            return jsonify({"success": False, "message": "Address not found"}), 404
            
    except Exception as e:
        print(f"Reverse geocoding error: {e}")
        return jsonify({"success": False, "message": "Reverse geocoding service unavailable"}), 500

def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance between two points using Haversine formula"""
    # Convert latitude and longitude from degrees to radians
    lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlng = lat2 - lng1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in kilometers
    r = 6371
    
    return c * r

@app.route('/api/nearby-barbers-advanced', methods=['POST'])
def get_nearby_barbers_advanced():
    """Get nearby barbers with real distance calculation"""
    try:
        data = request.json
        user_lat = data.get('lat')
        user_lng = data.get('lng')
        radius = float(data.get('radius', 10))  # Default 10km
        service_type = data.get('service_type', '')
        min_rating = float(data.get('min_rating', 0))
        
        if not user_lat or not user_lng:
            return jsonify({"success": False, "message": "Coordinates are required"}), 400
        
        conn = sqlite3.connect('barbershop.db')
        cursor = conn.cursor()
        
        # Get all active barbers with shop info
        cursor.execute("""
            SELECT b.id, b.name, s.name as shop_name, s.address, b.specialties,
                   s.latitude, s.longitude, b.experience_years, b.working_days,
                   b.start_time, b.end_time
            FROM barbers b
            JOIN shops s ON b.shop_id = s.id
            WHERE b.status = 'active' AND s.status = 'active'
            ORDER BY s.name, b.name
        """)
        
        barbers = []
        for row in cursor.fetchall():
            # For now, generate random coordinates near the user for demo
            # In production, you'd have real shop coordinates
            shop_lat = user_lat + (random.uniform(-0.1, 0.1))
            shop_lng = user_lng + (random.uniform(-0.1, 0.1))
            
            distance = calculate_distance(user_lat, user_lng, shop_lat, shop_lng)
            
            # Filter by radius
            if distance <= radius:
                # Apply filters
                specialties = row[4] or ''
                if service_type and service_type.lower() not in specialties.lower():
                    continue
                
                # Generate rating (in production, this would come from reviews)
                rating = 4.0 + (row[0] % 10) * 0.1
                if rating < min_rating:
                    continue
                
                barbers.append({
                    'id': row[0],
                    'name': row[1],
                    'shop_name': row[2],
                    'address': row[3],
                    'specialties': specialties,
                    'distance': round(distance, 1),
                    'rating': round(rating, 1),
                    'experience_years': row[7],
                    'working_days': row[8],
                    'working_hours': f"{row[9]} - {row[10]}" if row[9] and row[10] else "Not specified",
                    'coordinates': {'lat': shop_lat, 'lng': shop_lng},
                    'available_today': random.choice([True, False])  # Simulate availability
                })
        
        # Sort by distance
        barbers.sort(key=lambda x: x['distance'])
        
        conn.close()
        
        return jsonify({
            "success": True,
            "barbers": barbers,
            "total_found": len(barbers),
            "search_radius": radius,
            "user_location": {"lat": user_lat, "lng": user_lng}
        })
        
    except Exception as e:
        print(f"Error finding nearby barbers: {e}")
        return jsonify({"success": False, "message": "Failed to find nearby barbers"}), 500

# Update the existing API endpoints to include shop owner in login
@app.route('/api/signup', methods=['POST'])
def api_signup():
    try:
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone')
        user_type = request.form.get('user_type')
        location = request.form.get('location')
        
        # Additional fields for professionals
        shop_id = request.form.get('shop_id') if user_type == 'barber' else None
        shop_name = request.form.get('shop_name') if user_type == 'shop_owner' else None
        shop_address = request.form.get('shop_address') if user_type == 'shop_owner' else None
        working_days = request.form.get('working_days', '')
        specialties = request.form.get('specialties', '') if user_type == 'barber' else None
        experience_years = request.form.get('experience_years') if user_type == 'barber' else None
        start_time = request.form.get('barber_start_time') if user_type == 'barber' else request.form.get('opening_time')
        end_time = request.form.get('barber_end_time') if user_type == 'barber' else request.form.get('closing_time')
        
        # Validation
        if not all([email, password, confirm_password, first_name, last_name, phone, user_type, location]):
            return jsonify({"success": False, "message": "All required fields must be filled"}), 400
        
        if password != confirm_password:
            return jsonify({"success": False, "message": "Passwords do not match"}), 400
        
        if len(password) < 6:
            return jsonify({"success": False, "message": "Password must be at least 6 characters"}), 400
        
        if user_type == 'barber' and not shop_id:
            return jsonify({"success": False, "message": "Barbers must select a shop"}), 400
            
        if user_type == 'shop_owner' and not shop_name:
            return jsonify({"success": False, "message": "Shop owners must provide shop name"}), 400
        
        conn = sqlite3.connect('barbershop.db')
        cursor = conn.cursor()
        
        # Check if user already exists
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return jsonify({"success": False, "message": "Email already registered"}), 409
        
        # Create new user
        password_hash = hash_password(password)
        cursor.execute("""
            INSERT INTO users (email, password_hash, first_name, last_name, phone, user_type, location)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (email, password_hash, first_name, last_name, phone, user_type, location))
        
        user_id = cursor.lastrowid
        
        # Handle shop owner registration
        if user_type == 'shop_owner':
            cursor.execute("""
                INSERT INTO shops (name, address, phone, email, owner_id, working_days, opening_time, closing_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (shop_name, shop_address, phone, email, user_id, working_days, start_time, end_time))
            shop_id = cursor.lastrowid
            
            # Update user with shop_id
            cursor.execute("UPDATE users SET shop_id = ? WHERE id = ?", (shop_id, user_id))
        
        # Handle barber registration
        elif user_type == 'barber':
            cursor.execute("""
                INSERT INTO barbers (name, shop_id, specialties, experience_years, working_days, start_time, end_time, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (f"{first_name} {last_name}", shop_id, specialties, experience_years, working_days, start_time, end_time, user_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True, 
            "message": "Account created successfully",
            "user_id": user_id,
            "user_type": user_type
        })
        
    except Exception as e:
        print(f"Signup error: {e}")
        return jsonify({"success": False, "message": "An error occurred during signup"}), 500

# Add database migration for new fields
def migrate_database():
    """Add new columns to existing tables"""
    conn = sqlite3.connect('barbershop.db')
    cursor = conn.cursor()
    
    try:
        # Add location to users table
        cursor.execute("ALTER TABLE users ADD COLUMN location TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        # Add coordinates to shops table
        cursor.execute("ALTER TABLE shops ADD COLUMN latitude REAL")
        cursor.execute("ALTER TABLE shops ADD COLUMN longitude REAL")
        cursor.execute("ALTER TABLE shops ADD COLUMN working_days TEXT")
        cursor.execute("ALTER TABLE shops ADD COLUMN opening_time TEXT")
        cursor.execute("ALTER TABLE shops ADD COLUMN closing_time TEXT")
    except sqlite3.OperationalError:
        pass  # Columns already exist
    
    try:
        # Add more fields to barbers table
        cursor.execute("ALTER TABLE barbers ADD COLUMN experience_years TEXT")
        cursor.execute("ALTER TABLE barbers ADD COLUMN working_days TEXT")
        cursor.execute("ALTER TABLE barbers ADD COLUMN start_time TEXT")
        cursor.execute("ALTER TABLE barbers ADD COLUMN end_time TEXT")
        cursor.execute("ALTER TABLE barbers ADD COLUMN user_id INTEGER")
    except sqlite3.OperationalError:
        pass  # Columns already exist
    
    conn.commit()
    conn.close()

# Run migration on app start
if __name__ == '__main__':
    init_db()
    migrate_database()
    # seed_data()
    app.run(debug=True)