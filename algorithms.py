import sqlite3
from datetime import datetime, timedelta

def find_available_slots(date, service_id, shop_hours={"start": "09:00", "end": "18:00"}):
    """
    Algorithm 1: Find available time slots for a given date and service
    - Takes into account service duration
    - Checks barbers' schedules
    - Ensures slots are within shop hours
    """
    conn = sqlite3.connect('barbershop.db')
    cursor = conn.cursor()
    
    # Get service duration
    cursor.execute("SELECT duration FROM services WHERE id = ?", (service_id,))
    service = cursor.fetchone()
    if not service:
        return []
    
    service_duration = service[0]  # Duration in minutes
    
    # Get all active barbers
    cursor.execute("SELECT id FROM barbers WHERE status = 'active'")
    barbers = cursor.fetchall()
    
    available_slots = []
    
    # For each barber, find available time slots
    for barber in barbers:
        barber_id = barber[0]
        
        # Get barber's bookings for the day
        cursor.execute(
            "SELECT start_time, end_time FROM bookings WHERE barber_id = ? AND date = ? AND status != 'cancelled'", 
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
    - Uses a time slot approach without external libraries
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
    try:
        hours, minutes = map(int, time_str.split(':'))
        return hours * 60 + minutes
    except:
        return 0

def minutes_to_time(minutes):
    """Convert minutes since midnight to time string (HH:MM)"""
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"

def optimize_barber_schedule(date):
    """
    Algorithm 3: Optimize barber schedules to minimize idle time
    """
    conn = sqlite3.connect('barbershop.db')
    cursor = conn.cursor()
    
    # Get all barbers
    cursor.execute("SELECT id FROM barbers WHERE status = 'active'")
    barbers = cursor.fetchall()
    
    # Get all bookings for the date
    cursor.execute("""
        SELECT b.id, b.customer_id, b.service_id, b.start_time, b.end_time, s.duration 
        FROM bookings b
        JOIN services s ON b.service_id = s.id
        WHERE b.date = ? AND b.status != 'cancelled'
        ORDER BY b.start_time
    """, (date,))
    bookings = cursor.fetchall()
    
    # Track each barber's last assigned time
    barber_availability = {barber[0]: time_to_minutes("09:00") for barber in barbers}
    
    # For each booking, assign to barber with earliest availability
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

def smart_barber_assignment(service_id, date, time):
    """
    Algorithm 4: Smart barber assignment based on multiple factors
    - Barber rating and experience
    - Service specialization match
    - Workload distribution
    """
    conn = sqlite3.connect('barbershop.db')
    cursor = conn.cursor()
    
    # Get available barbers for the time slot
    available_slots = find_available_slots(date, service_id)
    suitable_barbers = [slot for slot in available_slots if slot['time'] == time]
    
    if not suitable_barbers:
        conn.close()
        return None
    
    # Get service details
    cursor.execute("SELECT name FROM services WHERE id = ?", (service_id,))
    service = cursor.fetchone()
    service_name = service[0] if service else ""
    
    best_barber = None
    best_score = -1
    
    for barber_slot in suitable_barbers:
        barber_id = barber_slot['barber_id']
        
        # Get barber details
        cursor.execute("""
            SELECT rating, total_bookings, specialties, experience_years 
            FROM barbers WHERE id = ?
        """, (barber_id,))
        barber_data = cursor.fetchone()
        
        if barber_data:
            rating, total_bookings, specialties, experience = barber_data
            
            # Calculate specialty match score
            specialty_score = 0
            if specialties and service_name:
                specialty_words = service_name.lower().split()
                for word in specialty_words:
                    if word in specialties.lower():
                        specialty_score += 1
            
            # Calculate workload score (prefer less busy barbers)
            today_bookings = get_barber_daily_bookings(barber_id, date)
            workload_score = max(0, 10 - today_bookings)  # Inverse relationship
            
            # Calculate final score
            score = (rating or 4.0) * 2 + specialty_score * 1.5 + workload_score * 0.5 + (experience or 1) * 0.1
            
            if score > best_score:
                best_score = score
                best_barber = barber_slot
    
    conn.close()
    return best_barber

def get_barber_daily_bookings(barber_id, date):
    """Get number of bookings for a barber on a specific date"""
    conn = sqlite3.connect('barbershop.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COUNT(*) FROM bookings 
        WHERE barber_id = ? AND date = ? AND status != 'cancelled'
    """, (barber_id, date))
    
    count = cursor.fetchone()[0]
    conn.close()
    return count

def predict_busy_hours(shop_id, date):
    """
    Algorithm 5: Predict busy hours based on historical data
    """
    conn = sqlite3.connect('barbershop.db')
    cursor = conn.cursor()
    
    # Get day of week
    date_obj = datetime.strptime(date, '%Y-%m-%d')
    day_of_week = date_obj.strftime('%A')
    
    # Get historical bookings for the same day of week
    cursor.execute("""
        SELECT start_time, COUNT(*) as booking_count
        FROM bookings b
        JOIN barbers br ON b.barber_id = br.id
        WHERE br.shop_id = ? AND strftime('%w', b.date) = strftime('%w', ?)
        AND b.status != 'cancelled'
        GROUP BY start_time
        ORDER BY booking_count DESC
    """, (shop_id, date))
    
    busy_hours = cursor.fetchall()
    conn.close()
    
    return busy_hours[:5]  # Return top 5 busy hours

def optimize_daily_schedule(shop_id, date):
    """
    Algorithm 6: Optimize daily schedule for maximum efficiency
    """
    conn = sqlite3.connect('barbershop.db')
    cursor = conn.cursor()
    
    # Get all bookings for the day
    cursor.execute("""
        SELECT b.*, s.duration, br.id as barber_id
        FROM bookings b
        JOIN services s ON b.service_id = s.id
        JOIN barbers br ON b.barber_id = br.id
        WHERE br.shop_id = ? AND b.date = ? AND b.status != 'cancelled'
        ORDER BY b.start_time
    """, (shop_id, date))
    
    bookings = cursor.fetchall()
    
    # Implement a simple greedy algorithm to minimize gaps
    optimized_schedule = []
    current_time = time_to_minutes("09:00")
    
    for booking in bookings:
        booking_start = time_to_minutes(booking[5])  # start_time
        duration = booking[-2]  # service duration
        
        # If there's a gap, try to fill it
        if booking_start > current_time:
            gap_duration = booking_start - current_time
            # Check if we can move this booking earlier
            if gap_duration >= 15:  # 15-minute minimum gap
                new_start = max(current_time, booking_start - gap_duration)
                optimized_schedule.append({
                    'booking_id': booking[0],
                    'original_start': minutes_to_time(booking_start),
                    'optimized_start': minutes_to_time(new_start),
                    'duration': duration
                })
        
        current_time = booking_start + duration
    
    conn.close()
    return optimized_schedule