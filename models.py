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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
        status TEXT DEFAULT 'active',
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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (admin_id) REFERENCES users (id)
    )
    ''')
    
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
        cursor.execute('SELECT * FROM shops ORDER BY created_at DESC')
        shops = cursor.fetchall()
        conn.close()
        return shops
    
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

class AdminAction:
    @staticmethod
    def log(admin_id, action_type, target_type, target_id, description):
        conn = sqlite3.connect('barbershop.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO admin_actions (admin_id, action_type, target_type, target_id, description)
            VALUES (?, ?, ?, ?, ?)
        ''', (admin_id, action_type, target_type, target_id, description))
        
        conn.commit()
        conn.close()

# Keep your existing classes
class Booking:
    pass

class Barber:
    pass

class Customer:
    pass

class Service:
    pass