import sqlite3
from datetime import datetime, timedelta

def find_available_slots(date, service_id, shop_hours={"start": "10:00", "end": "16:00"}):
    """
    Algorithm 1: Find available time slots for a given date and service
    - Takes into account service duration
    - Checks barbers' schedules
    - Ensures slots are within shop hours (10 AM - 4 PM)
    """
    conn = sqlite3.connect('barbershop.db')
    cursor = conn.cursor()
    
    # Get service duration
    cursor.execute("SELECT duration FROM services WHERE id = ?", (service_id,))
    service = cursor.fetchone()
    if not service:
        return []
    
    service_duration = service[0]  # Duration in minutes
    
    # Get all barbers
    cursor.execute("SELECT id FROM barbers")
    barbers = cursor.fetchall()
    
    available_slots = []
    
    # For each barber, find available time slots
    for barber in barbers:
        barber_id = barber[0]
        
        # Get barber's bookings for the day
        cursor.execute(
            "SELECT start_time, end_time FROM bookings WHERE barber_id = ? AND date = ?", 
            (barber_id, date)
        )
        bookings = cursor.fetchall()
        
        # Calculate available slots
        slots = calculate_available_slots(bookings, service_duration, shop_hours)
        
        for slot in slots:
            available_slots.append({
                "barber_id": barber_id,
                "time": slot
            })
    
    conn.close()
    return available_slots

def calculate_available_slots(bookings, service_duration, shop_hours):
    """
    Algorithm 2: Calculate available time slots given existing bookings
    - Uses a time slot approach rather than relying on library functions
    - Ensures no overlapping appointments
    """
    # Convert shop hours to minutes since midnight for easier calculation
    shop_start = time_to_minutes(shop_hours["start"])
    shop_end = time_to_minutes(shop_hours["end"])
    
    # Create an array to represent all possible time slots by discretizing time
    # Each array element represents a 15-minute interval
    slot_interval = 15  # in minutes
    total_slots = (shop_end - shop_start) // slot_interval
    
    # Initialize all slots as available (True)
    availability = [True] * total_slots
    
    # Mark booked slots as unavailable (False)
    for booking in bookings:
        start_time = time_to_minutes(booking[0]) - shop_start
        end_time = time_to_minutes(booking[1]) - shop_start
        
        # Convert to slot indices
        start_slot = start_time // slot_interval
        end_slot = end_time // slot_interval
        
        # Mark all slots in this booking range as unavailable
        for i in range(start_slot, end_slot):
            if 0 <= i < len(availability):
                availability[i] = False
    
    # Find contiguous available slots that can fit the service
    required_slots = (service_duration + slot_interval - 1) // slot_interval  # Round up
    available_times = []
    
    for i in range(len(availability) - required_slots + 1):
        # Check if we have enough consecutive available slots
        if all(availability[i:i+required_slots]):
            # Convert back to time string
            start_minutes = shop_start + (i * slot_interval)
            time_str = minutes_to_time(start_minutes)
            available_times.append(time_str)
    
    return available_times

def time_to_minutes(time_str):
    """Convert a time string (HH:MM) to minutes since midnight"""
    hours, minutes = map(int, time_str.split(':'))
    return hours * 60 + minutes

def minutes_to_time(minutes):
    """Convert minutes since midnight to time string (HH:MM)"""
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"

def optimize_barber_schedule(date):
    """
    Algorithm 3: Optimize barber schedules to minimize idle time
    - Can be used by admin to optimize barber assignments
    """
    conn = sqlite3.connect('barbershop.db')
    cursor = conn.cursor()
    
    # Get all barbers
    cursor.execute("SELECT id FROM barbers")
    barbers = cursor.fetchall()
    
    # Get all bookings for the date
    cursor.execute("""
        SELECT b.id, b.customer_id, b.service_id, b.start_time, b.end_time, s.duration 
        FROM bookings b
        JOIN services s ON b.service_id = s.id
        WHERE b.date = ?
        ORDER BY b.start_time
    """, (date,))
    bookings = cursor.fetchall()
    
    # Simple greedy algorithm: assign each booking to the barber with 
    # the earliest availability
    
    # Track each barber's last assigned time
    barber_availability = {barber[0]: time_to_minutes("10:00") for barber in barbers}
    
    # For each booking
    for booking in bookings:
        booking_id, _, _, start_time, _, duration = booking
        
        # Find barber with earliest availability
        best_barber = min(barber_availability, key=barber_availability.get)
        
        # Assign booking to this barber
        cursor.execute("""
            UPDATE bookings SET barber_id = ? WHERE id = ?
        """, (best_barber, booking_id))
        
        # Update barber availability
        start_minutes = time_to_minutes(start_time)
        barber_availability[best_barber] = start_minutes + duration
    
    conn.commit()
    conn.close()