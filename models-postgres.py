import psycopg2
import psycopg2.extras
import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# PostgreSQL connection parameters
DB_CONFIG = {
    'host': os.environ.get('POSTGRES_HOST', 'localhost'),
    'database': os.environ.get('POSTGRES_DB', 'barbershop'),
    'user': os.environ.get('POSTGRES_USER', 'postgres'),
    'password': os.environ.get('POSTGRES_PASSWORD', 'password'),
    'port': os.environ.get('POSTGRES_PORT', '5432')
}

def get_connection():
    """Get PostgreSQL connection with dictionary cursor"""
    conn = psycopg2.connect(**DB_CONFIG)
    # Enable automatic transactions
    conn.autocommit = False
    # Return cursor that returns results as dictionaries
    return conn

def init_db():
    """Initialize database with all tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create shops table first
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS shops (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        address TEXT NOT NULL,
        phone VARCHAR(20),
        email VARCHAR(100),
        owner_id INTEGER,
        status VARCHAR(20) DEFAULT 'active',
        description TEXT DEFAULT 'Premium barbershop services',
        logo_url TEXT DEFAULT '/static/image/demo-avatars/shop_owner.jpg',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        working_days VARCHAR(100) DEFAULT 'Monday-Friday',
        opening_time VARCHAR(10) DEFAULT '10:00',
        closing_time VARCHAR(10) DEFAULT '16:00'
    )
    ''')
    
    # Create users table with enhanced roles
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email VARCHAR(100) UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        first_name VARCHAR(50) NOT NULL,
        last_name VARCHAR(50) NOT NULL,
        phone VARCHAR(20),
        user_type VARCHAR(20) NOT NULL,
        shop_id INTEGER,
        status VARCHAR(20) DEFAULT 'active',
        home_location TEXT,
        last_login TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (shop_id) REFERENCES shops (id)
    )
    ''')
    
    # Add foreign key to shops for owner_id
    try:
        cursor.execute('ALTER TABLE shops ADD CONSTRAINT fk_shop_owner FOREIGN KEY (owner_id) REFERENCES users (id)')
    except psycopg2.errors.DuplicateObject:
        # Constraint already exists
        pass
    
    # Create barbers table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS barbers (
        id SERIAL PRIMARY KEY,
        user_id INTEGER,
        name VARCHAR(100) NOT NULL,
        shop_id INTEGER NOT NULL,
        specialties TEXT,
        experience_years INTEGER DEFAULT 0,
        role VARCHAR(50) DEFAULT 'Barber',
        status VARCHAR(20) DEFAULT 'active',
        working_days VARCHAR(100) DEFAULT 'Monday-Friday',
        start_time VARCHAR(10) DEFAULT '10:00',
        end_time VARCHAR(10) DEFAULT '16:00',
        rating REAL DEFAULT 0.0,
        total_bookings INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (shop_id) REFERENCES shops (id)
    )
    ''')
    
    # Create services table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS services (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        duration INTEGER NOT NULL,
        price REAL NOT NULL,
        shop_id INTEGER,
        status VARCHAR(20) DEFAULT 'active',
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (shop_id) REFERENCES shops (id)
    )
    ''')
    
    # Create customers table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS customers (
        id SERIAL PRIMARY KEY,
        user_id INTEGER,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(100) NOT NULL,
        phone VARCHAR(20),
        status VARCHAR(20) DEFAULT 'active',
        total_bookings INTEGER DEFAULT 0,
        total_spent REAL DEFAULT 0.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Create bookings table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bookings (
        id SERIAL PRIMARY KEY,
        customer_id INTEGER NOT NULL,
        barber_id INTEGER NOT NULL,
        service_id INTEGER NOT NULL,
        shop_id INTEGER NOT NULL,
        date DATE NOT NULL,
        start_time VARCHAR(10) NOT NULL,
        end_time VARCHAR(10) NOT NULL,
        status VARCHAR(20) DEFAULT 'confirmed',
        notes TEXT,
        total_price REAL,
        payment_status VARCHAR(20) DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES customers (id),
        FOREIGN KEY (barber_id) REFERENCES barbers (id),
        FOREIGN KEY (service_id) REFERENCES services (id),
        FOREIGN KEY (shop_id) REFERENCES shops (id)
    )
    ''')
    
    # Create notifications table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notifications (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL,
        title VARCHAR(100) NOT NULL,
        message TEXT NOT NULL,
        type VARCHAR(20) DEFAULT 'info',
        is_read BOOLEAN DEFAULT FALSE,
        action_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Create admin_actions table for logging
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS admin_actions (
        id SERIAL PRIMARY KEY,
        admin_id INTEGER NOT NULL,
        action_type VARCHAR(50) NOT NULL,
        target_type VARCHAR(50) NOT NULL,
        target_id INTEGER NOT NULL,
        description TEXT,
        ip_address VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (admin_id) REFERENCES users (id)
    )
    ''')
    
    # Create email_logs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS email_logs (
        id SERIAL PRIMARY KEY,
        recipient_email VARCHAR(100) NOT NULL,
        subject VARCHAR(200) NOT NULL,
        status VARCHAR(20) DEFAULT 'pending',
        error_message TEXT,
        sent_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create system_settings table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS system_settings (
        id SERIAL PRIMARY KEY,
        key VARCHAR(100) UNIQUE NOT NULL,
        value TEXT NOT NULL,
        description TEXT,
        updated_by INTEGER,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (updated_by) REFERENCES users (id)
    )
    ''')
    
    # Add shop_hours table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS shop_hours (
        id SERIAL PRIMARY KEY,
        shop_id INTEGER NOT NULL,
        day VARCHAR(20) NOT NULL,
        open_time VARCHAR(10),
        close_time VARCHAR(10),
        is_closed BOOLEAN DEFAULT FALSE,
        day_order INTEGER DEFAULT 0,
        FOREIGN KEY (shop_id) REFERENCES shops (id)
    )
    ''')
    
    # Add shop_special_days table for holidays and special hours
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS shop_special_days (
        id SERIAL PRIMARY KEY,
        shop_id INTEGER NOT NULL,
        date DATE NOT NULL,
        description TEXT,
        is_closed BOOLEAN DEFAULT FALSE,
        open_time VARCHAR(10),
        close_time VARCHAR(10),
        FOREIGN KEY (shop_id) REFERENCES shops (id)
    )
    ''')
    
    # Add reviews table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reviews (
        id SERIAL PRIMARY KEY,
        shop_id INTEGER NOT NULL,
        barber_id INTEGER,
        customer_id INTEGER NOT NULL,
        service_id INTEGER,
        booking_id INTEGER,
        rating INTEGER NOT NULL,
        review_text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        response_text TEXT,
        response_at TIMESTAMP,
        FOREIGN KEY (shop_id) REFERENCES shops (id),
        FOREIGN KEY (barber_id) REFERENCES barbers (id),
        FOREIGN KEY (customer_id) REFERENCES customers (id),
        FOREIGN KEY (service_id) REFERENCES services (id),
        FOREIGN KEY (booking_id) REFERENCES bookings (id)
    )
    ''')
    
    # Add inventory table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inventory (
        id SERIAL PRIMARY KEY,
        shop_id INTEGER NOT NULL,
        item_name VARCHAR(100) NOT NULL,
        category VARCHAR(50),
        quantity INTEGER DEFAULT 0,
        low_stock_threshold INTEGER DEFAULT 5,
        unit_price REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (shop_id) REFERENCES shops (id)
    )
    ''')
    
    # Create newsletter_subscribers table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS newsletter_subscribers (
        id SERIAL PRIMARY KEY,
        email VARCHAR(100) UNIQUE NOT NULL,
        name VARCHAR(100),
        subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ip_address VARCHAR(50),
        status VARCHAR(20) DEFAULT 'active'
    )
    ''')
    
    # Insert default system settings
    default_settings = [
        ('site_name', 'BookaBarber', 'Website name'),
        ('site_email', 'noreply@bookabarber.com', 'Default email address'),
        ('booking_advance_days', '30', 'How many days in advance customers can book'),
        ('default_shop_hours_start', '10:00', 'Default shop opening time'),
        ('default_shop_hours_end', '16:00', 'Default shop closing time'),
        ('email_notifications_enabled', 'true', 'Enable email notifications'),
        ('auto_assign_barbers', 'true', 'Auto assign barbers to bookings'),
        ('max_bookings_per_day', '20', 'Maximum bookings per barber per day')
    ]
    
    for setting in default_settings:
        try:
            cursor.execute('''
                INSERT INTO system_settings (key, value, description)
                VALUES (%s, %s, %s)
                ON CONFLICT (key) DO NOTHING
            ''', setting)
        except psycopg2.Error as e:
            print(f"Error inserting system setting: {e}")
    
    conn.commit()
    conn.close()

class Shop:
    @staticmethod
    def create(name, address, phone=None, email=None, owner_id=None, description=None, logo_path=None, working_days="Monday-Friday", opening_time="10:00", closing_time="18:00"):
        """Create a new shop with extended information"""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO shops (
                name, address, phone, email, owner_id, description, logo_url,
                working_days, opening_time, closing_time, created_at, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, 'active')
            RETURNING id
        ''', (name, address, phone, email, owner_id, description, logo_path, 
              working_days, opening_time, closing_time))
        
        shop_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        return shop_id

    @staticmethod
    def update(shop_id, **kwargs):
        """Update shop information with any provided fields"""
        if not kwargs:
            return False
            
        conn = get_connection()
        cursor = conn.cursor()
        
        # Build the update query dynamically based on provided fields
        set_clause = ", ".join([f"{key} = %s" for key in kwargs.keys()])
        query = f"UPDATE shops SET {set_clause} WHERE id = %s"
        
        # Extract values and add shop_id as the last parameter
        values = list(kwargs.values())
        values.append(shop_id)
        
        cursor.execute(query, values)
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success

    @staticmethod
    def get_working_hours(shop_id):
        """Get the working hours for a shop"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT day, open_time, close_time, is_closed FROM shop_hours 
            WHERE shop_id = %s ORDER BY day_order
        ''', (shop_id,))
        hours = cursor.fetchall()
        conn.close()
        return hours

    @staticmethod
    def set_working_hours(shop_id, hours_data):
        """Set working hours for a shop"""
        conn = get_connection()
        cursor = conn.cursor()
        
        # Delete existing hours
        cursor.execute('DELETE FROM shop_hours WHERE shop_id = %s', (shop_id,))
        
        # Insert new hours
        day_mapping = {
            'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3,
            'Friday': 4, 'Saturday': 5, 'Sunday': 6
        }
        
        for hours in hours_data:
            day = hours.get('day')
            is_closed = hours.get('closed', False)
            
            if day in day_mapping:
                cursor.execute('''
                    INSERT INTO shop_hours (shop_id, day, open_time, close_time, is_closed, day_order)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (
                    shop_id, 
                    day, 
                    hours.get('open_time', '09:00') if not is_closed else None,
                    hours.get('close_time', '18:00') if not is_closed else None,
                    is_closed,
                    day_mapping[day]
                ))
        
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def get_stats(shop_id):
        """Get statistics for a shop dashboard"""
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get month revenue
        first_day_of_month = datetime.datetime.now().replace(day=1).strftime('%Y-%m-%d')
        cursor.execute('''
            SELECT COALESCE(SUM(total_price), 0) AS month_revenue FROM bookings 
            WHERE shop_id = %s AND date >= %s AND status != 'cancelled'
        ''', (shop_id, first_day_of_month))
        result = cursor.fetchone()
        month_revenue = result['month_revenue'] if result else 0
        
        # Get today's bookings count
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            SELECT COUNT(*) AS today_bookings FROM bookings 
            WHERE shop_id = %s AND date = %s
        ''', (shop_id, today))
        result = cursor.fetchone()
        today_bookings = result['today_bookings'] if result else 0
        
        # Get total active barbers
        cursor.execute('''
            SELECT COUNT(*) AS total_barbers FROM barbers 
            WHERE shop_id = %s AND status = 'active'
        ''', (shop_id,))
        result = cursor.fetchone()
        total_barbers = result['total_barbers'] if result else 0
        
        # Get average rating
        cursor.execute('''
            SELECT COALESCE(AVG(rating), 0) AS avg_rating FROM reviews 
            WHERE shop_id = %s
        ''', (shop_id,))
        result = cursor.fetchone()
        avg_rating = round(result['avg_rating'] if result else 0, 1)
        
        # Get recent bookings
        cursor.execute('''
            SELECT b.id, b.date, b.start_time, b.status, b.total_price,
                   s.name as service_name, br.name as barber_name, c.name as customer_name
            FROM bookings b
            JOIN services s ON b.service_id = s.id
            JOIN barbers br ON b.barber_id = br.id
            JOIN customers c ON b.customer_id = c.id
            WHERE b.shop_id = %s
            ORDER BY b.date DESC, b.start_time DESC
            LIMIT 10
        ''', (shop_id,))
        recent_bookings = cursor.fetchall()
        
        # Get barber performance
        cursor.execute('''
            SELECT b.id, b.name, 
                   (SELECT COALESCE(AVG(r.rating), 4.5) FROM reviews r WHERE r.barber_id = b.id) as avg_rating,
                   (SELECT COUNT(*) FROM bookings bk WHERE bk.barber_id = b.id AND bk.date = %s) as today_bookings,
                   b.specialties,
                   (SELECT COUNT(*) FROM bookings bk WHERE bk.barber_id = b.id AND bk.date = %s 
                    AND bk.start_time > to_char(CURRENT_TIME, 'HH24:MI')) as upcoming_today
            FROM barbers b
            WHERE b.shop_id = %s AND b.status = 'active'
            ORDER BY today_bookings DESC
        ''', (today, today, shop_id))
        barber_performance = cursor.fetchall()
        
        conn.close()
        
        return {
            'month_revenue': round(month_revenue, 2),
            'today_bookings': today_bookings,
            'total_barbers': total_barbers,
            'avg_rating': avg_rating,
            'recent_bookings': recent_bookings,
            'barber_performance': barber_performance
        }

    @staticmethod
    def get_all():
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('''
            SELECT s.*, u.first_name, u.last_name 
            FROM shops s
            LEFT JOIN users u ON s.owner_id = u.id
            ORDER BY s.created_at DESC
        ''')
        shops = cursor.fetchall()
        conn.close()
        return shops

    @staticmethod
    def get_by_id(shop_id):
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('SELECT * FROM shops WHERE id = %s', (shop_id,))
        shop = cursor.fetchone()
        conn.close()
        return shop

    @staticmethod
    def update_status(shop_id, status):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE shops SET status = %s WHERE id = %s', (status, shop_id))
        conn.commit()
        conn.close()

class User:
    @staticmethod
    def create(email, password_hash, first_name, last_name, phone, user_type, shop_id=None):
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO users (email, password_hash, first_name, last_name, phone, user_type, shop_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (email, password_hash, first_name, last_name, phone, user_type, shop_id))
        
        user_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        return user_id

    @staticmethod
    def get_all():
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('''
            SELECT u.*, s.name as shop_name 
            FROM users u
            LEFT JOIN shops s ON u.shop_id = s.id
            ORDER BY u.created_at DESC
        ''')
        users = cursor.fetchall()
        conn.close()
        return users

    @staticmethod
    def get_by_shop(shop_id):
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('SELECT * FROM users WHERE shop_id = %s ORDER BY created_at DESC', (shop_id,))
        users = cursor.fetchall()
        conn.close()
        return users

    @staticmethod
    def update_status(user_id, status):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET status = %s WHERE id = %s', (status, user_id))
        conn.commit()
        conn.close()

    @staticmethod
    def update_last_login(user_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s', (user_id,))
        conn.commit()
        conn.close()

class Notification:
    @staticmethod
    def create(user_id, title, message, notification_type='info', action_url=None):
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO notifications (user_id, title, message, type, action_url)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        ''', (user_id, title, message, notification_type, action_url))
        
        notification_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        return notification_id

    @staticmethod
    def get_by_user(user_id, limit=50):
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('''
            SELECT * FROM notifications 
            WHERE user_id = %s 
            ORDER BY created_at DESC 
            LIMIT %s
        ''', (user_id, limit))
        notifications = cursor.fetchall()
        conn.close()
        return notifications

    @staticmethod
    def mark_as_read(notification_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE notifications SET is_read = TRUE WHERE id = %s', (notification_id,))
        conn.commit()
        conn.close()

    @staticmethod
    def get_unread_count(user_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM notifications WHERE user_id = %s AND is_read = FALSE', (user_id,))
        count = cursor.fetchone()[0]
        conn.close()
        return count

class AdminAction:
    @staticmethod
    def log(admin_id, action_type, target_type, target_id, description, ip_address=None):
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO admin_actions (admin_id, action_type, target_type, target_id, description, ip_address)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (admin_id, action_type, target_type, target_id, description, ip_address))
        
        action_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        return action_id

    @staticmethod
    def get_recent(limit=100):
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('''
            SELECT aa.*, u.first_name, u.last_name, u.user_type
            FROM admin_actions aa
            JOIN users u ON aa.admin_id = u.id
            ORDER BY aa.created_at DESC
            LIMIT %s
        ''', (limit,))
        actions = cursor.fetchall()
        conn.close()
        return actions

class Booking:
    @staticmethod
    def get_all():
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('''
            SELECT b.*, s.name as service_name, br.name as barber_name, 
                   c.name as customer_name, sh.name as shop_name
            FROM bookings b
            JOIN services s ON b.service_id = s.id
            JOIN barbers br ON b.barber_id = br.id
            JOIN customers c ON b.customer_id = c.id
            JOIN shops sh ON b.shop_id = sh.id
            ORDER BY b.created_at DESC
        ''')
        bookings = cursor.fetchall()
        conn.close()
        return bookings

    @staticmethod
    def update_status(booking_id, status):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE bookings 
            SET status = %s, updated_at = CURRENT_TIMESTAMP 
            WHERE id = %s
        ''', (status, booking_id))
        conn.commit()
        conn.close()

class Barber:
    @staticmethod
    def get_all():
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('''
            SELECT b.*, s.name as shop_name, u.email
            FROM barbers b
            JOIN shops s ON b.shop_id = s.id
            LEFT JOIN users u ON b.user_id = u.id
            ORDER BY b.created_at DESC
        ''')
        barbers = cursor.fetchall()
        conn.close()
        return barbers

class Customer:
    @staticmethod
    def get_all():
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('''
            SELECT c.*, u.user_type
            FROM customers c
            LEFT JOIN users u ON c.user_id = u.id
            ORDER BY c.total_spent DESC
        ''')
        customers = cursor.fetchall()
        conn.close()
        return customers

class Service:
    @staticmethod
    def get_all():
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('''
            SELECT s.*, sh.name as shop_name
            FROM services s
            JOIN shops sh ON s.shop_id = sh.id
            ORDER BY s.created_at DESC
        ''')
        services = cursor.fetchall()
        conn.close()
        return services

class SystemSettings:
    @staticmethod
    def get(key):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM system_settings WHERE key = %s', (key,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    @staticmethod
    def set(key, value, updated_by):
        conn = get_connection()
        cursor = conn.cursor()
        
        # Using upsert (INSERT ... ON CONFLICT) for PostgreSQL
        cursor.execute('''
            INSERT INTO system_settings (key, value, updated_by, updated_at)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (key) 
            DO UPDATE SET 
                value = EXCLUDED.value,
                updated_by = EXCLUDED.updated_by,
                updated_at = CURRENT_TIMESTAMP
        ''', (key, value, updated_by))
        
        conn.commit()
        conn.close()

    @staticmethod
    def get_all():
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('SELECT * FROM system_settings ORDER BY key')
        settings = cursor.fetchall()
        conn.close()
        return settings

class Review:
    @staticmethod
    def create(shop_id, customer_id, rating, review_text, barber_id=None, service_id=None, booking_id=None):
        """Create a new review"""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO reviews (shop_id, customer_id, barber_id, service_id, booking_id, 
                               rating, review_text, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            RETURNING id
        ''', (shop_id, customer_id, barber_id, service_id, booking_id, rating, review_text))
        
        review_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        return review_id

    @staticmethod
    def add_response(review_id, response_text):
        """Add a response to a review"""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE reviews 
            SET response_text = %s, response_at = CURRENT_TIMESTAMP 
            WHERE id = %s
        ''', (response_text, review_id))
        
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def get_by_shop(shop_id, filter_by=None, sort_by=None):
        """Get reviews for a shop with optional filtering and sorting"""
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        query = '''
            SELECT r.*, c.name as customer_name, b.name as barber_name,
                   s.name as service_name, r.created_at as date
            FROM reviews r
            JOIN customers c ON r.customer_id = c.id
            LEFT JOIN barbers b ON r.barber_id = b.id
            LEFT JOIN services s ON r.service_id = s.id
            WHERE r.shop_id = %s
        '''
        params = [shop_id]
        
        # Apply filters
        if filter_by == 'positive':
            query += ' AND r.rating >= 4'
        elif filter_by == 'neutral':
            query += ' AND r.rating = 3'
        elif filter_by == 'negative':
            query += ' AND r.rating <= 2'
        
        # Apply sorting
        if sort_by == 'newest':
            query += ' ORDER BY r.created_at DESC'
        elif sort_by == 'highest':
            query += ' ORDER BY r.rating DESC'
        elif sort_by == 'lowest':
            query += ' ORDER BY r.rating ASC'
        else:
            query += ' ORDER BY r.created_at DESC'
        
        cursor.execute(query, params)
        reviews = cursor.fetchall()
        conn.close()
        return reviews

class Inventory:
    @staticmethod
    def add_item(shop_id, item_name, category, quantity, low_stock_threshold, unit_price=None):
        """Add a new inventory item"""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO inventory (shop_id, item_name, category, quantity, 
                                 low_stock_threshold, unit_price)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (shop_id, item_name, category, quantity, low_stock_threshold, unit_price))
        
        item_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        return item_id
    
    @staticmethod
    def update_quantity(item_id, quantity_change):
        """Update inventory quantity"""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE inventory 
            SET quantity = quantity + %s, updated_at = CURRENT_TIMESTAMP 
            WHERE id = %s
        ''', (quantity_change, item_id))
        
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def get_by_shop(shop_id):
        """Get inventory items for a shop"""
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        cursor.execute('''
            SELECT * FROM inventory 
            WHERE shop_id = %s 
            ORDER BY category, item_name
        ''', (shop_id,))
        
        items = cursor.fetchall()
        conn.close()
        return items