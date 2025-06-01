document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const serviceInputs = document.querySelectorAll('input[name="service"]');
    const appointmentDate = document.getElementById('appointment-date');
    const timeSlotsContainer = document.getElementById('time-slots');
    const customerInfoSection = document.getElementById('customer-info');
    const bookingSummaryCard = document.getElementById('booking-summary-card');
    const bookBtn = document.getElementById('book-btn');
    
    // Summary elements
    const summaryServiceName = document.getElementById('summary-service-name');
    const summaryDate = document.getElementById('summary-date');
    const summaryTime = document.getElementById('summary-time');
    const summaryDuration = document.getElementById('summary-duration');
    const summaryTotal = document.getElementById('summary-total');
    
    // Customer info elements
    const customerName = document.getElementById('customer-name');
    const customerPhone = document.getElementById('customer-phone');
    const customerEmail = document.getElementById('customer-email');
    const customerNotes = document.getElementById('customer-notes');
    const customerLocation = document.getElementById('customer-location');
    
    // Modal elements
    const bookingModal = new bootstrap.Modal(document.getElementById('bookingModal'));
    const confirmBookingBtn = document.getElementById('confirm-booking');
    
    // State variables
    let selectedService = null;
    let selectedDate = null;
    let selectedTime = null;
    let selectedTimeSlot = null;

    // Initialize
    init();

    function init() {
        // Set minimum date to today
        const today = new Date().toISOString().split('T')[0];
        appointmentDate.setAttribute('min', today);
        
        // Add event listeners
        serviceInputs.forEach(input => {
            input.addEventListener('change', handleServiceSelection);
        });
        
        appointmentDate.addEventListener('change', handleDateSelection);
        bookBtn.addEventListener('click', showBookingModal);
        confirmBookingBtn.addEventListener('click', confirmBooking);
        
        // Initialize customer info validation
        setupFormValidation();
        
        // Handle current location button click
        document.getElementById('use-current-location').addEventListener('click', function() {
            if (!navigator.geolocation) {
                showErrorMessage('Geolocation is not supported by your browser');
                return;
            }
            
            // Show loading state
            this.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Getting location...';
            this.disabled = true;
            
            navigator.geolocation.getCurrentPosition(
                async function(position) {
                    const lat = position.coords.latitude;
                    const lng = position.coords.longitude;
                    
                    try {
                        // Use backend proxy or a geocoding service
                        const response = await fetch(`/api/reverse-geocode?lat=${lat}&lon=${lng}`);
                        const data = await response.json();
                        
                        if (data.success && data.address) {
                            customerLocation.value = data.address;
                        } else {
                            customerLocation.value = `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
                        }
                    } catch (error) {
                        console.log('Geocoding failed, using coordinates:', error);
                        customerLocation.value = `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
                    }
                    
                    // Reset button
                    this.innerHTML = '<i class="fas fa-crosshairs me-1"></i>Use My Current Location';
                    this.disabled = false;
                    
                    // Validate form
                    validateForm();
                },
                function(error) {
                    console.error('Geolocation error:', error);
                    showErrorMessage('Unable to get your location. Please enter it manually.');
                    
                    // Reset button
                    this.innerHTML = '<i class="fas fa-crosshairs me-1"></i>Use My Current Location';
                    this.disabled = false;
                }.bind(this),
                {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 300000
                }
            );
        });
    }

    function handleServiceSelection(event) {
        const selectedInput = event.target;
        selectedService = {
            id: selectedInput.value,
            name: selectedInput.closest('.service-option').querySelector('.service-name').textContent,
            price: parseInt(selectedInput.dataset.price),
            duration: parseInt(selectedInput.dataset.duration)
        };
        
        console.log('Service selected:', selectedService);
        
        // Update summary
        updateSummary();
        
        // Mark step as completed
        markStepCompleted(1);
        
        // Generate time slots if date is also selected
        if (selectedDate) {
            generateTimeSlots();
        }
        
        // Show next step indicator
        highlightCurrentStep(2);
    }

    function handleDateSelection(event) {
        selectedDate = event.target.value;
        
        console.log('Date selected:', selectedDate);
        
        // Validate if selected date is a business day (Monday-Friday)
        const selectedDateObj = new Date(selectedDate);
        const dayOfWeek = selectedDateObj.getDay(); // 0 = Sunday, 1 = Monday, ..., 6 = Saturday
        
        if (dayOfWeek === 0 || dayOfWeek === 6) {
            // Weekend selected
            showErrorMessage('Please select a business day (Monday to Friday). We are closed on weekends.');
            appointmentDate.value = '';
            selectedDate = null;
            return;
        }
        
        // Update summary
        updateSummary();
        
        // Mark step as completed
        markStepCompleted(2);
        
        // Generate time slots if service is also selected
        if (selectedService) {
            generateTimeSlots();
        }
        
        // Show next step indicator
        highlightCurrentStep(3);
    }

    function generateTimeSlots() {
        if (!selectedService || !selectedDate) {
            console.log('Service or date not selected');
            return;
        }
        
        console.log('Generating time slots for:', selectedService.name, 'on', selectedDate);
        
        // Clear previous slots
        timeSlotsContainer.innerHTML = '';
        
        // Generate time slots (10 AM to 4 PM, excluding lunch 12-1 PM)
        const timeSlots = [
            { time: '10:00 AM', value: '10:00' },
            { time: '10:30 AM', value: '10:30' },
            { time: '11:00 AM', value: '11:00' },
            { time: '11:30 AM', value: '11:30' },
            { time: '1:00 PM', value: '13:00' },
            { time: '1:30 PM', value: '13:30' },
            { time: '2:00 PM', value: '14:00' },
            { time: '2:30 PM', value: '14:30' },
            { time: '3:00 PM', value: '15:00' },
            { time: '3:30 PM', value: '15:30' },
            { time: '4:00 PM', value: '16:00' }
        ];
        
        // Add header message
        const headerMessage = document.createElement('div');
        headerMessage.className = 'time-slots-header text-center mb-4';
        headerMessage.innerHTML = `
            <div class="d-flex align-items-center justify-content-center mb-3">
                <i class="fas fa-clock text-primary me-2"></i>
                <h6 class="mb-0 text-primary fw-bold">Available Time Slots</h6>
            </div>
            <div class="alert alert-info py-2 mb-0">
                <i class="fas fa-info-circle me-2"></i>
                <small>All time slots are available! We'll automatically assign the best barber for your selected time.</small>
            </div>
        `;
        timeSlotsContainer.appendChild(headerMessage);
        
        // Create time slots grid container
        const slotsGrid = document.createElement('div');
        slotsGrid.className = 'time-slots-grid';
        slotsGrid.style.cssText = `
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        `;
        
        // Create time slot elements - all available
        timeSlots.forEach(slot => {
            const timeSlot = document.createElement('div');
            timeSlot.className = 'time-slot available';
            timeSlot.textContent = slot.time;
            timeSlot.dataset.time = slot.time;
            timeSlot.dataset.value = slot.value;
            
            // Add available indicator
            timeSlot.innerHTML = `
                <div class="slot-time">${slot.time}</div>
                <div class="slot-status">
                    <i class="fas fa-check-circle text-success"></i>
                    <small>Available</small>
                </div>
            `;
            
            timeSlot.addEventListener('click', handleTimeSlotSelection);
            slotsGrid.appendChild(timeSlot);
        });
        
        timeSlotsContainer.appendChild(slotsGrid);
        
        // Add footer message
        const footerMessage = document.createElement('div');
        footerMessage.className = 'time-slots-footer text-center mt-4';
        footerMessage.innerHTML = `
            <div class="alert alert-primary py-2 mb-0">
                <i class="fas fa-users me-2"></i>
                <small><strong>Smart Assignment:</strong> Our system will automatically assign an available barber based on your selected time and service requirements.</small>
            </div>
        `;
        timeSlotsContainer.appendChild(footerMessage);
        
        console.log('Time slots generated - all available');
    }

    function handleTimeSlotSelection(event) {
        // Remove previous selection
        document.querySelectorAll('.time-slot.selected').forEach(slot => {
            slot.classList.remove('selected');
        });
        
        // Select new slot
        selectedTimeSlot = event.currentTarget;
        selectedTimeSlot.classList.add('selected');
        selectedTime = selectedTimeSlot.dataset.time;
        
        console.log('Time slot selected:', selectedTime);
        
        // Update summary
        updateSummary();
        
        // Mark step as completed
        markStepCompleted(3);
        
        // Show customer info section
        showCustomerInfo();
        
        // Show next step indicator
        highlightCurrentStep(4);
    }

    function showCustomerInfo() {
        console.log('Showing customer info section');
        customerInfoSection.classList.remove('d-none');
        customerInfoSection.classList.add('show');
        
        // Scroll to customer info section
        customerInfoSection.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'start' 
        });
        
        // Focus on first input
        setTimeout(() => {
            customerName.focus();
        }, 500);
    }

    function updateSummary() {
        console.log('Updating summary');
        
        // Update service
        if (selectedService) {
            summaryServiceName.textContent = selectedService.name;
            summaryDuration.textContent = `${selectedService.duration} minutes`;
            summaryTotal.textContent = `$${selectedService.price}`;
        }
        
        // Update date
        if (selectedDate) {
            const date = new Date(selectedDate);
            summaryDate.textContent = date.toLocaleDateString('en-US', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
        }
        
        // Update time
        if (selectedTime) {
            summaryTime.textContent = selectedTime;
        }
        
        // Show booking summary if we have service, date, and time
        if (selectedService && selectedDate && selectedTime) {
            bookingSummaryCard.style.display = 'block';
            bookingSummaryCard.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'start' 
            });
        }
    }

    function setupFormValidation() {
        const inputs = [customerName, customerPhone, customerEmail];
        
        inputs.forEach(input => {
            input.addEventListener('input', validateForm);
            input.addEventListener('blur', validateForm);
        });
    }

    function validateForm() {
        const isNameValid = customerName.value.trim().length >= 2;
        const isPhoneValid = customerPhone.value.trim().length >= 10;
        const isEmailValid = customerEmail.value.includes('@') && customerEmail.value.includes('.');
        const isLocationValid = customerLocation.value.trim().length >= 5;
        
        const isFormValid = isNameValid && isPhoneValid && isEmailValid && isLocationValid && 
                           selectedService && selectedDate && selectedTime;
        
        bookBtn.disabled = !isFormValid;
        
        // Add visual feedback
        customerName.classList.toggle('is-valid', isNameValid && customerName.value.trim().length > 0);
        customerName.classList.toggle('is-invalid', !isNameValid && customerName.value.trim().length > 0);
        
        customerPhone.classList.toggle('is-valid', isPhoneValid && customerPhone.value.trim().length > 0);
        customerPhone.classList.toggle('is-invalid', !isPhoneValid && customerPhone.value.trim().length > 0);
        
        customerEmail.classList.toggle('is-valid', isEmailValid && customerEmail.value.trim().length > 0);
        customerEmail.classList.toggle('is-invalid', !isEmailValid && customerEmail.value.trim().length > 0);
        
        // Add location validation visual feedback
        customerLocation.classList.toggle('is-valid', isLocationValid && customerLocation.value.trim().length > 0);
        customerLocation.classList.toggle('is-invalid', !isLocationValid && customerLocation.value.trim().length > 0);
        
        if (isFormValid) {
            markStepCompleted(4);
        }
        
        console.log('Form validation:', {
            isNameValid,
            isPhoneValid,
            isEmailValid,
            isFormValid
        });
    }

    function markStepCompleted(stepNumber) {
        const stepCard = document.querySelector(`.card:nth-of-type(${stepNumber + 2})`); // +2 because notifications come first
        if (stepCard) {
            stepCard.classList.add('step-completed');
            stepCard.classList.remove('step-current');
        }
    }

    function highlightCurrentStep(stepNumber) {
        // Remove current class from all steps
        document.querySelectorAll('.card').forEach(card => {
            card.classList.remove('step-current');
        });
        
        // Add current class to current step
        const currentStepCard = document.querySelector(`.card:nth-of-type(${stepNumber + 2})`);
        if (currentStepCard) {
            currentStepCard.classList.add('step-current');
        }
    }

    function showBookingModal() {
        console.log('Showing booking modal');
        
        // Update to include location
        document.getElementById('modal-service').textContent = selectedService.name;
        document.getElementById('modal-date').textContent = summaryDate.textContent;
        document.getElementById('modal-time').textContent = selectedTime;
        document.getElementById('modal-duration').textContent = `${selectedService.duration} minutes`;
        document.getElementById('modal-customer-name').textContent = customerName.value;
        document.getElementById('modal-customer-phone').textContent = customerPhone.value;
        document.getElementById('modal-customer-email').textContent = customerEmail.value;
        document.getElementById('modal-customer-location').textContent = customerLocation.value;
        document.getElementById('modal-total').textContent = `$${selectedService.price}`;
        
        // Show modal
        bookingModal.show();
    }

    function confirmBooking() {
        console.log('Confirming booking...');
        
        const bookingData = {
            service_id: selectedService.id,
            service_name: selectedService.name,
            appointment_date: selectedDate,
            appointment_time: selectedTime,
            customer_name: customerName.value,
            customer_phone: customerPhone.value,
            customer_email: customerEmail.value,
            customer_location: customerLocation.value,
            customer_notes: customerNotes.value,
            total_price: selectedService.price,
            duration: selectedService.duration
        };
        
        // Disable confirm button and show loading
        confirmBookingBtn.disabled = true;
        confirmBookingBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
        
        // Simulate API call
        fetch('/api/book-appointment', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(bookingData)
        })
        .then(response => response.json())
        .then(data => {
            console.log('Booking response:', data);
            
            if (data.success) {
                // Hide modal
                bookingModal.hide();
                
                // Show success message with barber assignment
                showSuccessMessage(data.booking_id, data.assigned_barber);
                
                // Reset form
                resetForm();
            } else {
                throw new Error(data.message || 'Booking failed');
            }
        })
        .catch(error => {
            console.error('Booking error:', error);
            showErrorMessage(error.message);
        })
        .finally(() => {
            // Reset button
            confirmBookingBtn.disabled = false;
            confirmBookingBtn.innerHTML = '<i class="fas fa-check me-2"></i>Confirm Booking';
        });
    }

    function showSuccessMessage(bookingId, assignedBarber = null) {
        const successAlert = document.createElement('div');
        successAlert.className = 'alert alert-success alert-dismissible fade show';
        successAlert.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas fa-check-circle fa-3x me-3 text-success"></i>
                <div>
                    <h4 class="alert-heading mb-2">Booking Confirmed!</h4>
                    <p class="mb-2">Your appointment has been successfully booked and confirmed.</p>
                    <div class="booking-details mb-3">
                        <div class="row">
                            <div class="col-sm-6">
                                <small><strong>Booking ID:</strong> ${bookingId}</small>
                            </div>
                            <div class="col-sm-6">
                                <small><strong>Service:</strong> ${selectedService.name}</small>
                            </div>
                            <div class="col-sm-6">
                                <small><strong>Date & Time:</strong> ${summaryDate.textContent} at ${selectedTime}</small>
                            </div>
                            <div class="col-sm-6">
                                <small><strong>Total:</strong> $${selectedService.price}</small>
                            </div>
                        </div>
                    </div>
                    ${assignedBarber ? `
                        <div class="assigned-barber alert alert-info py-2 mb-2">
                            <i class="fas fa-user-tie me-2"></i>
                            <strong>Assigned Barber:</strong> ${assignedBarber.name} (${assignedBarber.specialization})
                        </div>
                    ` : `
                        <div class="auto-assignment alert alert-info py-2 mb-2">
                            <i class="fas fa-magic me-2"></i>
                            <strong>Auto-Assignment:</strong> We'll assign the best available barber and notify you shortly.
                        </div>
                    `}
                    <p class="mb-0">
                        <i class="fas fa-envelope me-1"></i>
                        <small>Confirmation email sent to <strong>${customerEmail.value}</strong></small>
                    </p>
                </div>
            </div>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Insert at top of container
        const container = document.querySelector('.booking-page .container');
        container.insertBefore(successAlert, container.firstChild);
        
        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function showErrorMessage(message) {
        const errorAlert = document.createElement('div');
        errorAlert.className = 'alert alert-danger alert-dismissible fade show';
        errorAlert.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas fa-exclamation-triangle fa-2x me-3 text-danger"></i>
                <div>
                    <h5 class="alert-heading mb-1">Booking Failed</h5>
                    <p class="mb-0">${message}</p>
                    <small class="text-muted">Please try again or contact support if the problem persists.</small>
                </div>
            </div>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Insert at top of container
        const container = document.querySelector('.booking-page .container');
        container.insertBefore(errorAlert, container.firstChild);
        
        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
        
        // Auto dismiss after 10 seconds
        setTimeout(() => {
            if (errorAlert.parentNode) {
                errorAlert.remove();
            }
        }, 10000);
    }

    function resetForm() {
        // Reset all selections
        selectedService = null;
        selectedDate = null;
        selectedTime = null;
        selectedTimeSlot = null;
        
        // Reset form inputs
        serviceInputs.forEach(input => input.checked = false);
        appointmentDate.value = '';
        customerName.value = '';
        customerPhone.value = '';
        customerEmail.value = '';
        customerNotes.value = '';
        customerLocation.value = '';
        
        // Remove validation classes
        [customerName, customerPhone, customerEmail].forEach(input => {
            input.classList.remove('is-valid', 'is-invalid');
        });
        
        // Hide sections
        customerInfoSection.classList.add('d-none');
        customerInfoSection.classList.remove('show');
        bookingSummaryCard.style.display = 'none';
        
        // Reset time slots
        timeSlotsContainer.innerHTML = `
            <div class="text-center py-5 text-muted">
                <i class="fas fa-calendar-day fa-3x mb-3"></i>
                <h5>Select a Service and Date</h5>
                <p class="mb-0">Please choose your preferred service and date to view available time slots</p>
            </div>
        `;
        
        // Reset step states
        document.querySelectorAll('.card').forEach(card => {
            card.classList.remove('step-completed', 'step-current');
        });
        
        // Disable book button
        bookBtn.disabled = true;
        
        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // Utility function for debugging
    window.bookingDebug = {
        selectedService,
        selectedDate,
        selectedTime,
        generateTimeSlots,
        showCustomerInfo,
        updateSummary,
        resetForm
    };
});