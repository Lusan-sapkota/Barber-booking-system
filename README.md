![BookaBarber Logo](./static/image/logo/logo.png)

A comprehensive web application for booking barber services, connecting customers with skilled barbers in their area. BookaBarber streamlines appointment scheduling while providing powerful management tools for barbers and shop owners.

## 📋 Table of Contents
- Features
- Technology Stack
- System Architecture
- Installation
- Configuration
- Algorithms & Technical Implementation
- Database Schema
- Usage Guide
- API Documentation
- Testing
- Security Considerations
- Performance Optimization
- Deployment
- Troubleshooting
- Contributing
- Roadmap
- License

## ✨ Features

### Customer Features
- **User Profile Management**
  - Personal information storage with secure data handling
  - Profile photo upload with image optimization
  - Preference settings for notifications and communications
  - Service history tracking and analytics
  - Favorite barbers list for quick booking
  
- **Location-Based Services**
  - Geolocation API integration for current location detection
  - Radius-based search with adjustable parameters
  - Map view with interactive barber shop pins
  - Route generation to selected barber shop
  - Location-based recommendations

- **Service Selection & Booking**
  - Categorized service menu with detailed descriptions
  - Visual gallery of hairstyle options
  - Custom service requests with pricing estimates
  - Multiple service selection for combination bookings
  - Quick rebooking from service history
  
- **Appointment Management**
  - Interactive calendar with availability highlighting
  - Time slot selection with duration indicators
  - Real-time booking confirmation
  - Appointment modification with business rules enforcement
  - Cancellation system with configurable policies
  
- **User Experience**
  - Dark/light theme with system preference detection
  - Responsive design for all device types
  - Accessibility features (WCAG compliance)
  - Multi-language support with auto-detection
  - Advanced search with filters and sorting options

### Barber/Shop Features
- **Business Profile Management**
  - Customizable shop profile with rich media gallery
  - Staff management with individual barber profiles
  - Service catalog with pricing tier options
  - Operating hours with exception date handling
  - Business analytics dashboard
  
- **Scheduling & Calendar Management**
  - Multi-view calendar (day, week, month)
  - Resource allocation for multiple barbers
  - Buffer time configuration between appointments
  - Vacation and time-off planning
  - Recurring booking handling
  
- **Customer Relationship Management**
  - Customer database with service history
  - Notes and preferences tracking
  - Communication tools for direct messaging
  - Customer segmentation for targeted promotions
  - Loyalty program management
  
- **Financial Tools**
  - Revenue tracking and reporting
  - Service-based performance analytics
  - Commission calculation for barbers
  - Tax report generation
  - Payment reconciliation tools

### Admin Features
- **System Management**
  - User account administration with role-based access
  - Global settings configuration
  - System health monitoring
  - Database maintenance tools
  - Activity logging and audit trails
  
- **Content Management**
  - News and announcements publication
  - FAQ and help documentation editor
  - Email template customization
  - Marketing campaign management
  - Terms of service and policy administration
  
- **Analytics & Reporting**
  - Cross-shop performance comparisons
  - Trend analysis and forecasting
  - Custom report generation
  - Data export in multiple formats
  - Real-time dashboard with KPIs

## 🛠️ Technology Stack

### Frontend
- **Core Technologies**
  - HTML5 with semantic markup
  - CSS3 with Flexbox and Grid layouts
  - JavaScript (ES6+) with async/await patterns
  - Bootstrap 5 framework for responsive design
  
- **UI/UX Enhancements**
  - FontAwesome 6 for vector icons
  - Custom CSS animations and transitions
  - Interactive charts with Chart.js
  - Image lazy loading and optimization
  - Progressive Web App capabilities

### Backend
- **Core Framework**
  - Python 3.8+ with type hints
  - Flask web framework with Blueprints architecture
  - SQLAlchemy ORM for database interactions
  - Jinja2 templating engine
  - RESTful API design principles
  
- **Authentication & Security**
  - JWT (JSON Web Tokens) for stateless authentication
  - Role-based access control (RBAC)
  - Password hashing with bcrypt
  - CSRF protection
  - Rate limiting for API endpoints

### Database
- **Primary Database**
  - SQLite for development
  - PostgreSQL recommended for production
  - Database migration management with Alembic
  - Connection pooling
  - Query optimization

### Services
- **Email System**
  - SMTP integration with failover
  - Template-based email generation
  - Queue-based sending for reliability
  - Delivery status tracking
  - Bounce handling
  
- **Geolocation Services**
  - OpenStreetMap integration
  - Geocoding and reverse geocoding
  - Distance calculation algorithms
  - Location data caching
  - Boundary detection for service areas
  
- **Analytics & Monitoring**
  - Custom event tracking
  - User behavior analysis
  - Performance metric collection
  - Error logging and alerting
  - A/B testing framework

## 💻 System Architecture

### MVC Pattern Implementation
- **Model Layer**: Data structures and business logic
- **View Layer**: Template-based UI rendering
- **Controller Layer**: Request handling and response generation

### Service Oriented Architecture
- Decoupled services with clear interfaces
- Microservices approach for core functions:
  - Booking Service
  - Notification Service
  - User Management Service
  - Analytics Service

### Request Flow
```
Client Request → Routing → Authentication → Authorization → Controller → Service Layer → 
Data Access Layer → Database → Response Generation → Client
```

### Caching Strategy
- Multi-level caching:
  - Browser-level caching
  - Application-level memory cache
  - Redis-based distributed cache
- Invalidation policies for data consistency

### Asynchronous Processing
- Task queue implementation with Celery
- Background job processing for:
  - Email sending
  - Notification delivery
  - Report generation
  - Data synchronization

## 📦 Installation

### System Requirements
- **Operating System**: Linux, macOS, or Windows
- **CPU**: Dual-core 2.0 GHz or higher
- **RAM**: Minimum 4GB (8GB recommended)
- **Storage**: 1GB available space for application
- **Network**: Broadband internet connection

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Git
- Node.js and npm (for frontend asset management)
- Redis (optional, for advanced caching)

### Clone Repository
```bash
# Clone the repository
git clone https://github.com/Lusan-sapkota/Barber-booking-system.git

# Navigate to project directory
cd Barber-shop-booking-system
```

### Setup Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies (optional)
npm install
```

### Initialize Database
```bash
# Initialize SQLite database with schema
python -c "from models import db; db.create_all()"

# Run database migrations
python manage.py db upgrade

# Seed initial data (optional)
python manage.py seed
```

### Verify Installation
```bash
# Run tests to verify setup
python -m pytest

# Start development server
python app.py
```

## ⚙️ Configuration

### Environment Variables
Create a .env file in the root directory with the following variables:

```
# Application Settings
APP_NAME=BookaBarber
ENVIRONMENT=development  # development, testing, production
DEBUG=True
LOG_LEVEL=DEBUG

# Database Configuration
DATABASE_URL=sqlite:///barbershop.db
POOL_SIZE=10
MAX_OVERFLOW=20
POOL_TIMEOUT=30
POOL_RECYCLE=1800

# Security Settings
SECRET_KEY=your_secret_key
JWT_SECRET_KEY=your_jwt_secret
JWT_ACCESS_TOKEN_EXPIRES=3600  # seconds
PASSWORD_SALT=your_password_salt
ALLOWED_HOSTS=localhost,127.0.0.1

# Email Configuration
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USERNAME=your_email@example.com
MAIL_PASSWORD=your_password
MAIL_USE_TLS=True
MAIL_DEFAULT_SENDER=noreply@bookabarber.com
MAIL_MAX_EMAILS=100

# Redis Configuration (Optional)
REDIS_URL=redis://localhost:6379/0
CACHE_TYPE=redis
CACHE_REDIS_URL=redis://localhost:6379/1

# Location Services
MAPS_API_KEY=your_maps_api_key
DEFAULT_SEARCH_RADIUS=10  # km
GEOCODING_CACHE_TIMEOUT=86400  # seconds

# Feature Flags
ENABLE_SOCIAL_LOGIN=True
ENABLE_DYNAMIC_PRICING=True
ENABLE_NOTIFICATIONS=True
ENABLE_ANALYTICS=True
```

### Configuration Files
- **config.py**: Core configuration file with environment-specific settings
- **logging.ini**: Logging configuration
- **gunicorn.conf.py**: Production server settings

### Email Configuration

For development, you can use sandbox environments:

#### Mailtrap
```
MAIL_SERVER=smtp.mailtrap.io
MAIL_PORT=2525
MAIL_USERNAME=your_mailtrap_username
MAIL_PASSWORD=your_mailtrap_password
MAIL_USE_TLS=True
```

#### Local Testing with Mailhog
```
MAIL_SERVER=localhost
MAIL_PORT=1025
MAIL_USERNAME=
MAIL_PASSWORD=
```

#### SendGrid (Production)
```
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USERNAME=apikey
MAIL_PASSWORD=your_sendgrid_api_key
MAIL_USE_TLS=True
```

### Third-Party Integrations

#### Payment Processors
- Stripe configuration:
  ```
  STRIPE_PUBLIC_KEY=pk_test_...
  STRIPE_SECRET_KEY=sk_test_...
  STRIPE_WEBHOOK_SECRET=whsec_...
  ```
- PayPal configuration:
  ```
  PAYPAL_CLIENT_ID=client_id...
  PAYPAL_CLIENT_SECRET=client_secret...
  PAYPAL_MODE=sandbox  # or 'live'
  ```

#### Social Authentication
- Google OAuth:
  ```
  GOOGLE_CLIENT_ID=your_client_id
  GOOGLE_CLIENT_SECRET=your_client_secret
  GOOGLE_DISCOVERY_URL=https://accounts.google.com/.well-known/openid-configuration
  ```
- Facebook OAuth:
  ```
  FACEBOOK_CLIENT_ID=your_app_id
  FACEBOOK_CLIENT_SECRET=your_app_secret
  ```

## 🧠 Algorithms & Technical Implementation

### Appointment Scheduling Algorithm
- **Implementation**: algorithms.py - `SchedulingAlgorithm` class
- **Core Algorithm**: Priority queue-based resource allocation with time complexity O(n log n)
- **Technical Details**:
  ```python
  def allocate_time_slots(barbers, service_duration, preferred_time):
      # Create a priority queue ordered by availability and rating
      available_barbers = PriorityQueue()
      
      for barber in barbers:
          if barber.is_available_at(preferred_time, service_duration):
              # Calculate priority score based on rating and distance
              score = calculate_barber_score(barber)
              available_barbers.put((-score, barber))  # Negative for max heap
              
      # Allocate optimal slots
      allocations = []
      while not available_barbers.empty() and len(allocations) < MAX_SUGGESTIONS:
          score, barber = available_barbers.get()
          slot = find_optimal_slot(barber, preferred_time, service_duration)
          allocations.append((barber, slot))
          
      return allocations
  ```
- **Constraints Handling**:
  - Barber availability windows
  - Service duration requirements
  - Travel time between appointments
  - Barber specialization matching
  - Client preferences

- **Optimization Techniques**:
  - Caching of availability data
  - Pre-computation of time slots
  - Incremental updates on booking changes
  - Parallel processing for large datasets

### Barber Recommendation Engine
- **Implementation**: algorithms.py - `RecommendationEngine` class
- **Core Algorithm**: Multi-factor weighted scoring with geographic filtering
- **Technical Details**:
  ```python
  def recommend_barbers(customer, service_type, location, time_preference):
      # Step 1: Geographic filtering using quadtree for efficient spatial queries
      nearby_barbers = spatial_index.query_radius(location, max_distance=5000)
      
      # Step 2: Calculate Haversine distance for precise ordering
      for barber in nearby_barbers:
          barber.distance = haversine_distance(location, barber.location)
      
      # Step 3: Apply weighted scoring algorithm
      scored_barbers = []
      for barber in nearby_barbers:
          if service_type in barber.services:
              # Base score components
              distance_score = calculate_distance_score(barber.distance)
              rating_score = barber.average_rating * 0.3
              specialization_score = calculate_specialty_match(barber, service_type)
              availability_score = calculate_availability_score(barber, time_preference)
              price_score = calculate_price_value(barber, service_type)
              
              # Historical and personalization factors
              history_score = calculate_history_score(customer, barber)
              trend_score = calculate_popularity_trend(barber)
              
              # Combined weighted score
              total_score = (distance_score * 0.25 +
                            rating_score * 0.2 +
                            specialization_score * 0.15 +
                            availability_score * 0.15 +
                            price_score * 0.1 + 
                            history_score * 0.1 +
                            trend_score * 0.05)
              
              scored_barbers.append((barber, total_score))
      
      # Sort by score and return top recommendations
      scored_barbers.sort(key=lambda x: x[1], reverse=True)
      return scored_barbers[:10]  # Return top 10 recommendations
  ```

- **Features Used in Scoring**:
  - Geographic proximity using Haversine formula
  - Service-specific expertise and specialization
  - Rating trends and review sentiment analysis
  - Historical booking patterns and customer affinity
  - Availability matching with time preference
  - Price-to-quality ratio assessment

- **Machine Learning Integration**:
  - Collaborative filtering for personalized recommendations
  - Progressive learning from booking outcomes
  - Seasonal trend detection and adaptation
  - A/B testing framework for algorithm variants

### Smart Notification System
- **Implementation**: email_service.py - `NotificationManager` class
- **Core Algorithm**: Time-based event triggering with priority queueing
- **Technical Details**:
  ```python
  class NotificationQueue:
      def __init__(self):
          self.high_priority = Queue()
          self.medium_priority = Queue()
          self.low_priority = Queue()
          self.scheduled = SortedDict()  # Ordered by delivery time
          
      def schedule_notification(self, notification, delivery_time, priority='medium'):
          # Add to scheduled notifications
          if delivery_time not in self.scheduled:
              self.scheduled[delivery_time] = []
          self.scheduled[delivery_time].append((priority, notification))
          
      def process_due_notifications(self, current_time):
          # Process all due notifications
          due_times = [time for time in self.scheduled.keys() if time <= current_time]
          for time in due_times:
              notifications = self.scheduled.pop(time)
              for priority, notification in notifications:
                  if priority == 'high':
                      self.high_priority.put(notification)
                  elif priority == 'medium':
                      self.medium_priority.put(notification)
                  else:
                      self.low_priority.put(notification)
                      
      def get_next_notification(self):
          # Process from highest priority to lowest
          if not self.high_priority.empty():
              return self.high_priority.get()
          if not self.medium_priority.empty():
              return self.medium_priority.get()
          if not self.low_priority.empty():
              return self.low_priority.get()
          return None
  ```

- **Notification Strategies**:
  - Progressive notification sequence (email → SMS → push)
  - Smart retry mechanism with exponential backoff
  - Delivery time optimization based on user engagement patterns
  - Batching for efficiency with urgency exceptions
  - Template personalization based on user preferences

- **Delivery Channels**:
  - Email with HTML and plain text fallback
  - SMS through Twilio integration
  - Web push notifications
  - In-app notification center
  - WhatsApp integration (optional)

### Dynamic Pricing Model
- **Implementation**: algorithms.py - `DynamicPricingEngine` class
- **Core Algorithm**: Multi-variable regression with seasonal adjustment
- **Technical Details**:
  ```python
  def calculate_dynamic_price(base_price, service_type, barber, date_time, demand_factor):
      # Base components
      time_multiplier = calculate_time_multiplier(date_time)
      experience_multiplier = calculate_experience_multiplier(barber)
      demand_multiplier = calculate_demand_multiplier(service_type, date_time, demand_factor)
      
      # Special case handling
      if is_peak_hour(date_time):
          demand_multiplier *= 1.2
      
      if is_weekend(date_time):
          time_multiplier *= 1.1
          
      # Loyalty discount
      loyalty_discount = calculate_loyalty_discount(customer)
      
      # Apply seasonal promotions
      promotion_discount = get_applicable_promotion(service_type, date_time)
      
      # Calculate final price with constraints
      adjusted_price = base_price * time_multiplier * experience_multiplier * demand_multiplier
      final_price = adjusted_price * (1 - loyalty_discount) * (1 - promotion_discount)
      
      # Ensure price constraints
      final_price = max(base_price * 0.8, min(final_price, base_price * 1.5))
      
      return round(final_price, 2)
  ```

- **Pricing Factors**:
  - Time-based adjustments (peak hours, weekends)
  - Barber experience and popularity metrics
  - Historical demand patterns by time slot
  - Seasonal adjustments (holidays, special events)
  - Loyalty program integration with tiered discounts
  - Promotional campaigns and flash sales

- **Market Analysis Components**:
  - Competitor price monitoring
  - Elasticity modeling for price sensitivity
  - A/B testing for price point optimization
  - Profitability analysis with cost modeling
  - Yield management techniques from hospitality industry

### Graph-Based Service Recommendation
- **Implementation**: algorithms.py - `ServiceGraph` class
- **Core Algorithm**: Association rule mining with graph traversal
- **Technical Details**:
  ```python
  class ServiceGraph:
      def __init__(self):
          self.graph = {}  # Adjacency list representation
          self.service_weights = {}  # Edge weights
          
      def build_from_transactions(self, transactions):
          # Build graph from historical booking data
          for transaction in transactions:
              services = transaction.get_services()
              
              # Update connections between all service pairs
              for i in range(len(services)):
                  for j in range(i+1, len(services)):
                      self._add_edge(services[i], services[j])
      
      def _add_edge(self, service1, service2):
          # Add bidirectional edge
          if service1 not in self.graph:
              self.graph[service1] = {}
          if service2 not in self.graph:
              self.graph[service2] = {}
              
          # Increment weight if edge exists, otherwise create with weight 1
          edge_key = (service1, service2)
          self.service_weights[edge_key] = self.service_weights.get(edge_key, 0) + 1
          
          # Update adjacency lists
          self.graph[service1][service2] = self.service_weights[edge_key]
          self.graph[service2][service1] = self.service_weights[edge_key]
          
      def recommend_services(self, selected_service, limit=3):
          if selected_service not in self.graph:
              return []
              
          # Get connected services sorted by weight
          connected_services = [(service, self.graph[selected_service][service]) 
                              for service in self.graph[selected_service]]
          connected_services.sort(key=lambda x: x[1], reverse=True)
          
          # Return top recommendations
          return [service for service, weight in connected_services[:limit]]
  ```

- **Application Areas**:
  - Bundle recommendations for service packages
  - Upselling opportunities identification
  - Personalized service discovery
  - Seasonal package optimization

## 📊 Database Schema

### Core Tables
- **Users**
  - Authentication credentials
  - Profile information
  - Account settings
  - Role assignments

- **Customers**
  - Personal information
  - Contact details
  - Preference settings
  - Service history

- **Barbers**
  - Professional information
  - Skills and specializations
  - Availability schedule
  - Performance metrics

- **Shops**
  - Business information
  - Location data
  - Operating hours
  - Staff associations

- **Services**
  - Service definitions
  - Pricing information
  - Duration estimates
  - Category classifications

- **Bookings**
  - Appointment details
  - Status tracking
  - Payment information
  - Related services

### Relationship Diagram
```
User ─┬── Customer ──┬── Booking ───── Service
      └── Barber ────┘     │
                           │
                      Shop ─┘
```

### Indexes and Optimizations
- Composite indexes for frequent query patterns
- Full-text search indexes for name and location searches
- Temporal partitioning for historical booking data
- Spatial indexing for location-based queries

## 🚀 Usage Guide

### Running the Application

```bash
# Development mode
python app.py

# Production mode with gunicorn
gunicorn "app:create_app()" --bind 0.0.0.0:5000 --workers=4 --threads=2
```

Then open your browser and navigate to `http://127.0.0.1:5000`

### Customer Flow

1. **Create Account / Sign In**
   - Register with email or social login
   - Verify email for account activation
   - Complete profile with preferences
   - Set notification preferences

2. **Find a Barber**
   - Use location-based search to find nearby barbers
   - Filter by service type, rating, availability
   - View barber profiles with portfolios and reviews
   - Compare multiple barbers side-by-side
   - View real-time availability calendar

3. **Book an Appointment**
   - Select desired service from the menu
   - Choose add-on services (optional)
   - Select available date and time slot
   - Add special instructions or preferences
   - Review booking summary with price breakdown
   - Select payment method
   - Confirm booking and receive confirmation

4. **Manage Bookings**
   - View upcoming and past appointments
   - Receive timely reminders (24h and 1h before appointment)
   - Reschedule or cancel bookings within policy limits
   - Get directions to the shop
   - Leave reviews after service completion
   - Easily rebook previous services

### Barber/Shop Flow

1. **Professional Registration**
   - Create professional account with credentials verification
   - Set up shop profile with services, location, photos
   - Add portfolio items with before/after photos
   - Define working hours and exceptions
   - Configure service menu with pricing

2. **Manage Calendar**
   - View daily, weekly and monthly appointment schedule
   - Set regular working hours and break times
   - Block off unavailable times for personal needs
   - Set buffer times between appointments
   - Handle walk-in appointments
   - Synchronize with external calendars (Google, Outlook)

3. **Process Appointments**
   - Receive notifications for new bookings
   - Send check-in confirmation to waiting customers
   - Mark appointments as completed
   - Register additional services performed
   - Track earnings and performance
   - Receive instant feedback from customers

4. **Business Management**
   - Track revenue with detailed reporting
   - Analyze performance metrics and trends
   - Manage customer database
   - Create and manage promotions
   - Configure automatic reminder settings
   - Export data for accounting purposes

### Admin Flow

1. **System Management**
   - Monitor system health and performance
   - Manage user accounts and roles
   - Configure global system settings
   - Review and approve new shops
   - Moderate reviews and content

2. **Content Management**
   - Update homepage features and announcements
   - Edit static content pages
   - Manage FAQ and help documentation
   - Configure email templates
   - Set up system-wide promotions

3. **Analytics & Reporting**
   - View comprehensive system dashboard
   - Generate custom reports
   - Track key performance indicators
   - Monitor user engagement metrics
   - Analyze booking trends and patterns

## 📚 API Documentation

### API Overview
The BookaBarber API is a RESTful interface allowing programmatic access to the system's functionality. All endpoints return JSON responses and accept JSON payloads where applicable.

### Base URL
```
Development: http://localhost:5000/api
Production: https://api.bookabarber.com/v1
```

### Authentication
All API requests require authentication using JSON Web Tokens (JWT).

```
Authorization: Bearer <your_jwt_token>
```

To obtain a token, use the authentication endpoints.

### Rate Limiting
API requests are rate limited to prevent abuse:
- 60 requests per minute for authenticated users
- 10 requests per minute for unauthenticated endpoints

### Authentication Endpoints

#### Register New User
- **Endpoint:** `POST /api/auth/register`
- **Description:** Create a new user account
- **Request Body:**
  ```json
  {
    "email": "user@example.com",
    "password": "securepassword",
    "fullName": "John Doe",
    "phone": "+1234567890",
    "role": "customer"
  }
  ```
- **Response:**
  ```json
  {
    "success": true,
    "message": "User registered successfully",
    "userId": "user_uuid",
    "verificationRequired": true
  }
  ```

#### Login
- **Endpoint:** `POST /api/auth/login`
- **Description:** Authenticate user and receive token
- **Request Body:**
  ```json
  {
    "email": "user@example.com",
    "password": "securepassword"
  }
  ```
- **Response:**
  ```json
  {
    "success": true,
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": "user_uuid",
      "email": "user@example.com",
      "name": "John Doe",
      "role": "customer"
    }
  }
  ```

#### Request Password Reset
- **Endpoint:** `POST /api/auth/forgot-password`
- **Description:** Request password reset
- **Request Body:**
  ```json
  {
    "email": "user@example.com"
  }
  ```
- **Response:**
  ```json
  {
    "success": true,
    "message": "If the email exists, a reset link has been sent"
  }
  ```

#### Reset Password
- **Endpoint:** `POST /api/auth/reset-password`
- **Description:** Reset password with token
- **Request Body:**
  ```json
  {
    "token": "reset_token",
    "password": "newSecurePassword"
  }
  ```
- **Response:**
  ```json
  {
    "success": true,
    "message": "Password has been reset successfully"
  }
  ```

### Barber Endpoints

#### Get Barber List
- **Endpoint:** `GET /api/barbers`
- **Description:** Get list of barbers with filtering
- **Query Parameters:**
  - `location`: Geographic coordinates (lat,lng)
  - `radius`: Search radius in km (default: 10)
  - `service`: Filter by service ID
  - `rating`: Minimum rating (1-5)
  - `available`: Filter for availability (true/false)
  - `page`: Page number for pagination
  - `limit`: Items per page (max 50)
- **Response:**
  ```json
  {
    "success": true,
    "barbers": [
      {
        "id": "barber_uuid",
        "name": "Mike Johnson",
        "rating": 4.8,
        "reviewCount": 124,
        "specialties": ["Fade", "Beard Trim"],
        "shopName": "Elite Cuts",
        "distance": 1.2,
        "availableToday": true,
        "nextAvailable": "2023-06-21T14:00:00Z",
        "thumbnailUrl": "https://example.com/barber.jpg",
        "priceRange": "$20-45"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 10,
      "totalItems": 45,
      "totalPages": 5
    }
  }
  ```

#### Find Nearby Barbers
- **Endpoint:** `GET /api/barbers/nearby`
- **Description:** Find nearby barbers based on location
- **Query Parameters:**
  - `lat`: Latitude
  - `lng`: Longitude
  - `radius`: Search radius in km (default: 5)
  - `limit`: Maximum results (default: 20)
- **Response:**
  ```json
  {
    "success": true,
    "barbers": [
      {
        "id": "barber_uuid",
        "name": "John Smith",
        "shopName": "Modern Cuts",
        "distance": 0.8,
        "rating": 4.5,
        "location": {
          "lat": 40.7128,
          "lng": -74.0060
        }
      }
    ]
  }
  ```

#### Get Barber Details
- **Endpoint:** `GET /api/barbers/{id}`
- **Description:** Get detailed information about a specific barber
- **Response:**
  ```json
  {
    "success": true,
    "barber": {
      "id": "barber_uuid",
      "name": "John Smith",
      "bio": "Specializing in modern cuts with 10+ years experience",
      "rating": 4.7,
      "reviewCount": 213,
      "specialties": ["Fade", "Beard Trim", "Hot Towel Shave"],
      "services": [
        {
          "id": "service_uuid",
          "name": "Haircut",
          "price": 30.00,
          "duration": 30
        }
      ],
      "gallery": [
        "https://example.com/gallery1.jpg",
        "https://example.com/gallery2.jpg"
      ],
      "shop": {
        "id": "shop_uuid",
        "name": "Modern Cuts",
        "address": "123 Main St, New York, NY",
        "phone": "+12125551234"
      }
    }
  }
  ```

#### Get Barber Availability
- **Endpoint:** `GET /api/barbers/{id}/availability`
- **Description:** Get barber's availability slots
- **Query Parameters:**
  - `date`: Date in YYYY-MM-DD format
  - `service`: Service ID for duration calculation
- **Response:**
  ```json
  {
    "success": true,
    "availability": {
      "date": "2023-06-21",
      "timeSlots": [
        {
          "start": "09:00",
          "end": "09:30",
          "available": true
        },
        {
          "start": "09:30",
          "end": "10:00",
          "available": false
        }
      ]
    },
    "nextAvailableDate": "2023-06-22"
  }
  ```

#### Get Barber Reviews
- **Endpoint:** `GET /api/barbers/{id}/reviews`
- **Description:** Get barber reviews
- **Query Parameters:**
  - `page`: Page number
  - `limit`: Items per page
  - `sort`: Sort order (newest, highest, lowest)
- **Response:**
  ```json
  {
    "success": true,
    "reviews": [
      {
        "id": "review_uuid",
        "customer": {
          "name": "Alex",
          "avatarUrl": "https://example.com/avatar.jpg"
        },
        "rating": 5,
        "comment": "Great haircut, very professional",
        "serviceDate": "2023-06-15T14:30:00Z",
        "createdAt": "2023-06-15T18:40:12Z",
        "serviceName": "Haircut"
      }
    ],
    "summary": {
      "averageRating": 4.7,
      "totalReviews": 213,
      "ratingDistribution": {
        "5": 150,
        "4": 43,
        "3": 12,
        "2": 5,
        "1": 3
      }
    }
  }
  ```

### Booking Endpoints

#### Get User's Bookings
- **Endpoint:** `GET /api/bookings`
- **Description:** Get current user's bookings
- **Query Parameters:**
  - `status`: Filter by status (upcoming, past, cancelled)
  - `page`: Page number
  - `limit`: Items per page
- **Response:**
  ```json
  {
    "success": true,
    "bookings": [
      {
        "id": "booking_uuid",
        "status": "confirmed",
        "dateTime": "2023-06-21T14:00:00Z",
        "service": {
          "name": "Haircut",
          "price": 30.00,
          "duration": 30
        },
        "barber": {
          "id": "barber_uuid",
          "name": "John Smith"
        },
        "shop": {
          "name": "Modern Cuts",
          "address": "123 Main St"
        },
        "canCancel": true,
        "canReschedule": true
      }
    ]
  }
  ```

#### Create Booking
- **Endpoint:** `POST /api/bookings`
- **Description:** Create new booking
- **Request Body:**
  ```json
  {
    "barberId": "barber_uuid",
    "serviceId": "service_uuid",
    "date": "2023-06-21",
    "time": "14:00",
    "notes": "Short on sides, longer on top",
    "addons": ["service_uuid_2"]
  }
  ```
- **Response:**
  ```json
  {
    "success": true,
    "booking": {
      "id": "booking_uuid",
      "reference": "BKG12345",
      "status": "confirmed",
      "dateTime": "2023-06-21T14:00:00Z",
      "endTime": "2023-06-21T14:30:00Z",
      "totalPrice": 35.00,
      "barber": {
        "name": "John Smith",
        "phone": "+12125551234"
      }
    },
    "calendar": {
      "googleCalendarLink": "https://calendar.google.com/...",
      "icsFileUrl": "https://api.bookabarber.com/calendar/bkg12345.ics"
    }
  }
  ```

#### Get Booking Details
- **Endpoint:** `GET /api/bookings/{id}`
- **Description:** Get booking details
- **Response:**
  ```json
  {
    "success": true,
    "booking": {
      "id": "booking_uuid",
      "reference": "BKG12345",
      "status": "confirmed",
      "createdAt": "2023-06-15T10:30:00Z",
      "dateTime": "2023-06-21T14:00:00Z",
      "endTime": "2023-06-21T14:30:00Z",
      "service": {
        "name": "Haircut",
        "price": 30.00,
        "duration": 30
      },
      "addons": [
        {
          "name": "Beard Trim",
          "price": 15.00,
          "duration": 15
        }
      ],
      "notes": "Short on sides, longer on top",
      "totalPrice": 45.00,
      "barber": {
        "id": "barber_uuid",
        "name": "John Smith"
      },
      "shop": {
        "name": "Modern Cuts",
        "address": "123 Main St, New York, NY",
        "location": {
          "lat": 40.7128,
          "lng": -74.0060
        }
      },
      "canCancel": true,
      "canReschedule": true,
      "cancellationFee": 0.00
    }
  }
  ```

#### Update Booking
- **Endpoint:** `PUT /api/bookings/{id}`
- **Description:** Update booking (reschedule)
- **Request Body:**
  ```json
  {
    "date": "2023-06-22",
    "time": "15:00",
    "notes": "Updated instructions"
  }
  ```
- **Response:**
  ```json
  {
    "success": true,
    "message": "Booking updated successfully",
    "booking": {
      "id": "booking_uuid",
      "dateTime": "2023-06-22T15:00:00Z",
      "status": "confirmed"
    }
  }
  ```

#### Cancel Booking
- **Endpoint:** `DELETE /api/bookings/{id}`
- **Description:** Cancel booking
- **Query Parameters:**
  - `reason`: Cancellation reason (optional)
- **Response:**
  ```json
  {
    "success": true,
    "message": "Booking cancelled successfully",
    "cancellationFee": 0.00,
    "refundAmount": 30.00
  }
  ```

### Service Endpoints

#### Get Services List
- **Endpoint:** `GET /api/services`
- **Description:** Get available services
- **Query Parameters:**
  - `shopId`: Filter by shop (optional)
  - `category`: Filter by category (optional)
- **Response:**
  ```json
  {
    "success": true,
    "services": [
      {
        "id": "service_uuid",
        "name": "Haircut",
        "description": "Standard haircut service",
        "price": 30.00,
        "duration": 30,
        "category": "basic",
        "imageUrl": "https://example.com/haircut.jpg"
      }
    ],
    "categories": [
      {
        "id": "category_uuid",
        "name": "Basic Services",
        "serviceCount": 5
      }
    ]
  }
  ```

### Admin Endpoints

#### Get All Users
- **Endpoint:** `GET /api/admin/users`
- **Description:** Get all users (requires admin role)
- **Query Parameters:**
  - `role`: Filter by role
  - `status`: Filter by status
  - `search`: Search term for name/email
  - `page`: Page number
  - `limit`: Items per page
- **Response:**
  ```json
  {
    "success": true,
    "users": [
      {
        "id": "user_uuid",
        "email": "user@example.com",
        "name": "John Doe",
        "role": "customer",
        "status": "active",
        "createdAt": "2023-05-10T12:30:45Z",
        "lastLogin": "2023-06-15T08:22:13Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "totalItems": 245,
      "totalPages": 13
    }
  }
  ```

## ✅ Testing

### Test Suite Structure
- **Unit Tests**: Test individual functions and classes
- **Integration Tests**: Test component interactions
- **API Tests**: Test API endpoints
- **End-to-End Tests**: Test complete user flows
- **Performance Tests**: Test system under load

### Running Tests

```bash
# Run all tests
pytest

# Run specific test category
pytest tests/unit/
pytest tests/api/

# Run with coverage report
pytest --cov=. tests/
```

### Test Data
Test data is automatically generated using fixtures and factories:

```python
@pytest.fixture
def sample_booking():
    return Booking(
        customer_id=1,
        barber_id=2,
        service_id=3,
        date="2023-06-21",
        time="14:00",
        status="confirmed"
    )
```

### Continuous Integration
Tests are automatically run on:
- Pull request creation
- Merge to main branch
- Daily scheduled runs

## 🔒 Security Considerations

### Authentication Security
- Password hashing using bcrypt with salt
- JWT with short expiration and refresh token rotation
- Multi-factor authentication option
- Account lockout after failed attempts
- Session invalidation on suspicious activity

### Data Protection
- Encryption of sensitive data at rest
- TLS/SSL for all communications
- Regular security audits
- GDPR and CCPA compliance measures
- Data minimization practices

### API Security
- Rate limiting to prevent abuse
- Input validation and sanitization
- CSRF protection
- CORS policy configuration
- API key rotation policies

### Infrastructure Security
- Regular security patches
- Network segmentation
- Web Application Firewall (WAF)
- DDoS protection
- Regular vulnerability scanning

## 🚄 Performance Optimization

### Database Optimization
- Query optimization with proper indexing
- Connection pooling
- Statement caching
- Read replicas for scale
- Denormalization for read-heavy operations

### Caching Strategy
- Multi-level caching approach:
  - Browser caching for static assets
  - CDN for media content
  - Redis for application data
  - Memory cache for frequent lookups

### Frontend Performance
- Asset bundling and minification
- Lazy loading of components
- Image optimization
- Critical CSS inlining
- Prefetching for anticipated user paths

### Backend Efficiency
- Asynchronous processing for long-running tasks
- Horizontal scaling for API services
- Optimized algorithms for core functions
- Database query batching
- Response compression

## 🚀 Deployment

### Development Environment
- Local development with Docker
- Hot-reloading for rapid iteration
- Development database seeding
- Local email trapping

### Staging Environment
- Cloud-based replica of production
- Integration with CI/CD pipeline
- Automated testing before promotion
- Data anonymization from production

### Production Deployment
- Blue-green deployment strategy
- Automated rollback capabilities
- Health checks and monitoring
- Load balancing across multiple instances
- Geographic distribution for low latency

### Deployment Commands
```bash
# Build Docker image
docker build -t bookabarber:latest .

# Run Docker container
docker run -p 5000:5000 -e ENVIRONMENT=production bookabarber:latest

# Deploy to production (using deployment script)
./deploy.sh production
```

## ❓ Troubleshooting

### Common Issues

#### Application Won't Start
- Check if database connection is properly configured
- Verify that required environment variables are set
- Ensure Python version compatibility (3.8+)
- Check logs for specific error messages

#### Booking Creation Fails
- Verify that selected time slot is still available
- Check if service and barber IDs are valid
- Ensure user is authenticated if required
- Verify that all required fields are provided

#### Email Notifications Not Sending
- Check SMTP server configuration
- Verify that email templates exist
- Check if the email service is running
- Look for errors in the email service logs

### Logging and Debugging

```bash
# Enable debug mode
export DEBUG=True

# Set verbose logging
export LOG_LEVEL=DEBUG

# Check application logs
tail -f logs/application.log

# Check error logs
tail -f logs/error.log
```

### Support Channels
- GitHub Issues for bug reports
- Documentation Wiki for self-service
- Email support at support@bookabarber.com
- Community forum at community.bookabarber.com

## 🤝 Contributing

We welcome contributions to improve BookaBarber! Please follow these steps:

1. **Fork the Repository**
   ```bash
   # Clone your fork
   git clone https://github.com/Lusan-sapkota/Barber-booking-system.git
   cd Barber-shop-booking-system
   ```

2. **Create a Feature Branch**
   ```bash
   # Create and switch to new branch
   git checkout -b feature/your-feature-name
   ```

3. **Set Up Development Environment**
   ```bash
   # Install development dependencies
   pip install -r requirements-dev.txt
   
   # Install pre-commit hooks
   pre-commit install
   ```

4. **Make Your Changes**
   - Write code that follows the style guidelines
   - Add tests for new functionality
   - Update documentation as needed

5. **Run Tests**
   ```bash
   # Run test suite
   pytest
   
   # Check code style
   flake8
   ```

6. **Commit Your Changes**
   ```bash
   # Stage and commit changes
   git add .
   git commit -m 'Add some feature'
   ```

7. **Push to GitHub**
   ```bash
   git push origin feature/your-feature-name
   ```

8. **Create a Pull Request**
   - Open a PR against the main repository
   - Provide a clear description of the changes
   - Reference any related issues

### Contribution Guidelines
- Follow the existing code style and conventions
- Write clear, descriptive commit messages using conventional commits format
- Include tests for new features and bug fixes
- Update documentation for API changes
- Keep PRs focused on a single change to facilitate review
- Ensure all tests pass before submitting
- Be respectful and collaborative in discussions

### Code of Conduct
Please note that this project adheres to the Contributor Covenant Code of Conduct. By participating, you are expected to uphold this code.

## 🗺️ Roadmap

### Upcoming Features (Q3 2023)
- Mobile application for iOS and Android
- Integrated payment processing
- AI-powered style recommendation
- Video consultation before booking
- Loyalty program with rewards

### Medium Term (Q4 2023)
- Inventory management for shops
- Staff performance analytics
- Advanced reporting dashboard
- Customer retention tools
- Multi-language support

### Long Term (2024)
- Marketplace for barber products
- Franchise management system
- Integrated POS system
- Machine learning for improved recommendations
- White-label solution for enterprise customers

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

Created with ❤️ by Lusan Sapkota. For issues, feature requests, or questions, please open an [issue](https://github.com/Lusan-sapkota/Barber-booking-system/issues).
