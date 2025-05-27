document.addEventListener('DOMContentLoaded', function() {
    const dateInput = document.getElementById('appointment-date');
    const serviceInputs = document.querySelectorAll('input[name="service"]');
    const timeSlotContainer = document.getElementById('time-slots');
    const bookBtn = document.getElementById('book-btn');
    
    // Variables to store user selection
    let selectedDate = null;
    let selectedService = null;
    let selectedSlot = null;
    
    // Check if we can enable the book button
    function updateBookButton() {
        bookBtn.disabled = !(selectedDate && selectedService && selectedSlot);
    }
    
    // Fetch available slots when date or service changes
    async function fetchAvailableSlots() {
        if (!selectedDate || !selectedService) return;
        
        try {
            const response = await fetch(`/api/slots?date=${selectedDate}&service_id=${selectedService}`);
            const slots = await response.json();
            
            renderTimeSlots(slots);
        } catch (error) {
            console.error('Error fetching time slots:', error);
            timeSlotContainer.innerHTML = 'Error loading time slots. Please try again.';
        }
    }
    
    // Render time slots in the UI
    function renderTimeSlots(slots) {
        if (!slots || slots.length === 0) {
            timeSlotContainer.innerHTML = 'No available slots for this date.';
            return;
        }
        
        const html = slots.map(slot => `
            <div class="time-slot" data-barber="${slot.barber_id}" data-time="${slot.time}">
                ${slot.time}
            </div>
        `).join('');
        
        timeSlotContainer.innerHTML = html;
        
        // Add event listeners to the new time slot elements
        document.querySelectorAll('.time-slot').forEach(el => {
            el.addEventListener('click', function() {
                // Remove selection from all slots
                document.querySelectorAll('.time-slot').forEach(s => s.classList.remove('selected'));
                
                // Select this slot
                this.classList.add('selected');
                selectedSlot = {
                    barber_id: this.dataset.barber,
                    time: this.dataset.time
                };
                
                updateBookButton();
            });
        });
    }
    
    // Event listeners
    dateInput.addEventListener('change', function() {
        selectedDate = this.value;
        fetchAvailableSlots();
        updateBookButton();
    });
    
    serviceInputs.forEach(input => {
        input.addEventListener('change', function() {
            selectedService = this.value;
            fetchAvailableSlots();
            updateBookButton();
        });
    });
    
    bookBtn.addEventListener('click', async function() {
        if (!selectedDate || !selectedService || !selectedSlot) return;
        
        try {
            const response = await fetch('/api/book', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    date: selectedDate,
                    service_id: selectedService,
                    barber_id: selectedSlot.barber_id,
                    time: selectedSlot.time
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                alert('Appointment booked successfully!');
                // Reset form or redirect
            } else {
                alert('Failed to book appointment: ' + result.message);
            }
        } catch (error) {
            console.error('Error booking appointment:', error);
            alert('An error occurred while booking. Please try again.');
        }
    });
});