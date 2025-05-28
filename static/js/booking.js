document.addEventListener('DOMContentLoaded', function() {
    const dateInput = document.getElementById('appointment-date');
    const serviceInputs = document.querySelectorAll('input[name="service"]');
    const timeSlotContainer = document.getElementById('time-slots');
    const bookBtn = document.getElementById('book-btn');
    const customerInfoSection = document.getElementById('customer-info');
    const customerName = document.getElementById('customer-name');
    const customerPhone = document.getElementById('customer-phone');
    const customerEmail = document.getElementById('customer-email');
    const customerNotes = document.getElementById('customer-notes');
    
    // Modal elements
    const summaryService = document.getElementById('summary-service');
    const summaryDate = document.getElementById('summary-date');
    const summaryTime = document.getElementById('summary-time');
    const summaryPrice = document.getElementById('summary-price');
    const confirmBookingBtn = document.getElementById('confirm-booking');
    
    // Service prices and durations
    const services = {
        "1": { name: "Haircut", price: 25, duration: 30 },
        "2": { name: "Haircut + Beard Trim", price: 35, duration: 45 },
        "3": { name: "Beard Trim", price: 15, duration: 15 },
        "4": { name: "Premium Package", price: 50, duration: 60 }
    };
    
    // Variables to store user selection
    let selectedDate = null;
    let selectedService = null;
    let selectedSlot = null;
    
    // Set minimum date to today
    const today = new Date();
    const yyyy = today.getFullYear();
    const mm = String(today.getMonth() + 1).padStart(2, '0');
    const dd = String(today.getDate()).padStart(2, '0');
    const todayFormatted = `${yyyy}-${mm}-${dd}`;
    dateInput.setAttribute('min', todayFormatted);
    
    // Check if we can enable the book button
    function updateBookButton() {
        const isTimeSelected = selectedDate && selectedService && selectedSlot;
        
        // Show customer info section if time is selected
        if (isTimeSelected) {
            customerInfoSection.classList.remove('d-none');
            
            // Enable button only if customer info is provided
            bookBtn.disabled = !(customerName.value && customerPhone.value && customerEmail.value);
        } else {
            customerInfoSection.classList.add('d-none');
            bookBtn.disabled = true;
        }
    }
    
    // Format date for display
    function formatDateForDisplay(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
        });
    }
    
    // Fetch available slots when date or service changes
    async function fetchAvailableSlots() {
        if (!selectedDate || !selectedService) return;
        
        // Show loading indicator
        timeSlotContainer.innerHTML = '<div class="text-center py-5"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        
        try {
            const response = await fetch(`/api/slots?date=${selectedDate}&service_id=${selectedService}`);
            const slots = await response.json();
            
            renderTimeSlots(slots);
        } catch (error) {
            console.error('Error fetching time slots:', error);
            timeSlotContainer.innerHTML = '<div class="alert alert-danger">Error loading time slots. Please try again.</div>';
        }
    }
    
    // Render time slots in the UI
    function renderTimeSlots(slots) {
        if (!slots || slots.length === 0) {
            timeSlotContainer.innerHTML = '<div class="text-center py-5 text-muted"><i class="fas fa-calendar-times fa-3x mb-3"></i><p>No available slots for this date. Please try another date.</p></div>';
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
    
    // Event listeners for customer info fields
    [customerName, customerPhone, customerEmail].forEach(input => {
        input.addEventListener('input', updateBookButton);
    });
    
    // Event listeners for date and service selection
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
    
    // Book button opens modal with summary
    bookBtn.addEventListener('click', function() {
        if (!selectedDate || !selectedService || !selectedSlot) return;
        
        // Populate summary
        const serviceDetails = services[selectedService];
        summaryService.textContent = serviceDetails.name;
        summaryDate.textContent = formatDateForDisplay(selectedDate);
        summaryTime.textContent = selectedSlot.time;
        summaryPrice.textContent = `$${serviceDetails.price}`;
        
        // Show modal
        const bookingModal = new bootstrap.Modal(document.getElementById('bookingModal'));
        bookingModal.show();
    });
    
    // Confirm booking button in modal
    confirmBookingBtn.addEventListener('click', async function() {
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
                    time: selectedSlot.time,
                    customer: {
                        name: customerName.value,
                        email: customerEmail.value,
                        phone: customerPhone.value,
                        notes: customerNotes.value
                    }
                })
            });
            
            const result = await response.json();
            
            // Hide modal
            bootstrap.Modal.getInstance(document.getElementById('bookingModal')).hide();
            
            if (result.success) {
                // Show success message
                timeSlotContainer.innerHTML = `
                    <div class="text-center py-5">
                        <div class="alert alert-success mb-4">
                            <i class="fas fa-check-circle fa-3x d-block mb-3"></i>
                            <h4>Booking Confirmed!</h4>
                            <p>Your appointment has been successfully booked.</p>
                            <p>A confirmation email has been sent to ${customerEmail.value}</p>
                        </div>
                        <a href="{{ url_for('home') }}" class="btn btn-primary">Return to Home</a>
                    </div>
                `;
                
                // Hide customer info and book button
                customerInfoSection.classList.add('d-none');
                bookBtn.classList.add('d-none');
            } else {
                alert('Failed to book appointment: ' + result.message);
            }
        } catch (error) {
            console.error('Error booking appointment:', error);
            alert('An error occurred while booking. Please try again.');
        }
    });
});