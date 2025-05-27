from flask import Flask, render_template, request, jsonify, session
import sqlite3
from models import init_db, Booking, Barber, Customer, Service
from algorithms import find_available_slots, optimize_barber_schedule

app = Flask(__name__)
app.secret_key = "your-secret-key"

# Initialize database
init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/booking')
def booking_page():
    return render_template('booking.html')

@app.route('/admin')
def admin_page():
    return render_template('admin.html')

@app.route('/api/slots', methods=['GET'])
def get_available_slots():
    date = request.args.get('date')
    service_id = request.args.get('service_id')
    
    # Use our custom algorithm to find available slots
    slots = find_available_slots(date, service_id)
    
    return jsonify(slots)

@app.route('/api/book', methods=['POST'])
def book_appointment():
    # Process booking data
    # Implement validation and confirmation
    pass

if __name__ == '__main__':
    app.run(debug=True)