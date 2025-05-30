import sqlite3
import datetime

def init_db():
    conn = sqlite3.connect('barbershop.db')
    cursor = conn.cursor()
    
    # Create shops table first
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS shops (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        address TEXT NOT NULL,
        phone TEXT,
        email TEXT,
        owner_id INTEGER,
        status TEXT DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        working_days TEXT DEFAULT 'Monday-Friday',
        opening_time TEXT DEFAULT '10:00',
        closing_time TEXT DEFAULT '16:00'
    )
    ''')
    
    # Create users table with enhanced roles
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
        status TEXT DEFAULT 'active',
        last_login TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (shop_id) REFERENCES shops (id)
    )
    ''')
    
    # Create barbers table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS barbers (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        name TEXT NOT NULL,
        shop_id INTEGER NOT NULL,
        specialties TEXT,
        experience_years INTEGER DEFAULT 0,
        status TEXT DEFAULT 'active',
        working_days TEXT DEFAULT 'Monday-Friday',
        start_time TEXT DEFAULT '10:00',
        end_time TEXT DEFAULT '16:00',
        rating REAL DEFAULT 0.0,
        total_bookings INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (shop_id) REFERENCES shops (id)
    )
    ''')
    
    # Create services table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS services (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        duration INTEGER NOT NULL,
        price REAL NOT NULL,
        shop_id INTEGER,
        status TEXT DEFAULT 'active',
        description TEXT,
        FOREIGN KEY (shop_id) REFERENCES shops (id)
    )
    ''')
    
    # Create bookings table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL,
        barber_id INTEGER NOT NULL,
        service_id INTEGER NOT NULL,
        shop_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        status TEXT DEFAULT 'confirmed',
        notes TEXT,
        total_price REAL,
        payment_status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES users (id),
        FOREIGN KEY (barber_id) REFERENCES barbers (id),
        FOREIGN KEY (service_id) REFERENCES services (id),
        FOREIGN KEY (shop_id) REFERENCES shops (id)
    )
    ''')
    
    # Create customers table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT,
        status TEXT DEFAULT 'active',
        total_bookings INTEGER DEFAULT 0,
        total_spent REAL DEFAULT 0.0,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Create notifications table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        type TEXT DEFAULT 'info',
        is_read BOOLEAN DEFAULT FALSE,
        action_url TEXT,
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
    
    # Create email_logs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS email_logs (
        id INTEGER PRIMARY KEY,
        recipient_email TEXT NOT NULL,
        subject TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        error_message TEXT,
        sent_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create system_settings table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS system_settings (
        id INTEGER PRIMARY KEY,
        key TEXT UNIQUE NOT NULL,
        value TEXT NOT NULL,
        description TEXT,
        updated_by INTEGER,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (updated_by) REFERENCES users (id)
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
        cursor.execute('''
            INSERT OR IGNORE INTO system_settings (key, value, description)
            VALUES (?, ?, ?)
        ''', setting)
    
    conn.commit()
    conn.close()

class Shop:
    @staticmethod
    def create(name, address, phone, email, owner_id):
        conn = sqlite3.connect('barbershop.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO shops (name, address, phone, email, owner_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, address, phone, email, owner_id))
        
        shop_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return shop_id
    
    @staticmethod
    def get_all():
        conn = sqlite3.connect('barbershop.db')
        cursor = conn.cursor()
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
        conn = sqlite3.connect('barbershop.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM shops WHERE id = ?', (shop_id,))
        shop = cursor.fetchone()
        conn.close()
        return shop
    
    @staticmethod
    def update_status(shop_id, status):
        conn = sqlite3.connect('barbershop.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE shops SET status = ? WHERE id = ?', (status, shop_id))
        conn.commit()
        conn.close()

class User:
    @staticmethod
    def create(email, password_hash, first_name, last_name, phone, user_type, shop_id=None):
        conn = sqlite3.connect('barbershop.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO users (email, password_hash, first_name, last_name, phone, user_type, shop_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (email, password_hash, first_name, last_name, phone, user_type, shop_id))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return user_id
    
    @staticmethod
    def get_all():
        conn = sqlite3.connect('barbershop.db')
        cursor = conn.cursor()
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
        conn = sqlite3.connect('barbershop.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE shop_id = ? ORDER BY created_at DESC', (shop_id,))
        users = cursor.fetchall()
        conn.close()
        return users
    
    @staticmethod
    def update_status(user_id, status):
        conn = sqlite3.connect('barbershop.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET status = ? WHERE id = ?', (status, user_id))
        conn.commit()
        conn.close()
    
    @staticmethod
    def update_last_login(user_id):
        conn = sqlite3.connect('barbershop.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()

class Notification:
    @staticmethod
    def create(user_id, title, message, notification_type='info', action_url=None):
        conn = sqlite3.connect('barbershop.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO notifications (user_id, title, message, type, action_url)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, title, message, notification_type, action_url))
        
        notification_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return notification_id
    
    @staticmethod
    def get_by_user(user_id, limit=50):
        conn = sqlite3.connect('barbershop.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM notifications 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (user_id, limit))
        notifications = cursor.fetchall()
        conn.close()
        return notifications
    
    @staticmethod
    def mark_as_read(notification_id):
        conn = sqlite3.connect('barbershop.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE notifications SET is_read = TRUE WHERE id = ?', (notification_id,))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_unread_count(user_id):
        conn = sqlite3.connect('barbershop.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = FALSE', (user_id,))
        count = cursor.fetchone()[0]
        conn.close()
        return count

class AdminAction:
    @staticmethod
    def log(admin_id, action_type, target_type, target_id, description, ip_address=None):
        conn = sqlite3.connect('barbershop.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO admin_actions (admin_id, action_type, target_type, target_id, description, ip_address)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (admin_id, action_type, target_type, target_id, description, ip_address))
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_recent(limit=100):
        conn = sqlite3.connect('barbershop.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT aa.*, u.first_name, u.last_name, u.user_type
            FROM admin_actions aa
            JOIN users u ON aa.admin_id = u.id
            ORDER BY aa.created_at DESC
            LIMIT ?
        ''', (limit,))
        actions = cursor.fetchall()
        conn.close()
        return actions

# Keep your existing classes
class Booking:
    @staticmethod
    def get_all():
        conn = sqlite3.connect('barbershop.db')
        cursor = conn.cursor()
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
        conn = sqlite3.connect('barbershop.db')
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE bookings SET status = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (status, booking_id))
        conn.commit()
        conn.close()

class Barber:
    @staticmethod
    def get_all():
        conn = sqlite3.connect('barbershop.db')
        cursor = conn.cursor()
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
        conn = sqlite3.connect('barbershop.db')
        cursor = conn.cursor()
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
        conn = sqlite3.connect('barbershop.db')
        cursor = conn.cursor()
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
        conn = sqlite3.connect('barbershop.db')
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM system_settings WHERE key = ?', (key,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    @staticmethod
    def set(key, value, updated_by):
        conn = sqlite3.connect('barbershop.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO system_settings (key, value, updated_by, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (key, value, updated_by))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_all():
        conn = sqlite3.connect('barbershop.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM system_settings ORDER BY key')
        settings = cursor.fetchall()
        conn.close()
        return settings