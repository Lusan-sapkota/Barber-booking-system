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

def calculate_available_slots(bookings, duration, shop_hours):
    """
    Algorithm 2: Calculate available time slots given existing bookings
    - Uses a time slot approach rather than relying on library functions
    - Ensures no overlapping appointments
    """
    # Implementation details here
    pass

def optimize_barber_schedule(date):
    """
    Algorithm 3: Optimize barber schedules to minimize idle time
    - Can be used by admin to optimize barber assignments
    """
    # Implementation details here
    pass