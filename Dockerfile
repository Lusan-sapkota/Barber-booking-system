# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container at /app
COPY . .

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV ENVIRONMENT=production
ENV APP_NAME=BookaBarber
# Add other environment variables from your .env file as needed,
# or pass them during `docker run`

# Run app.py when the container launches
# Using Gunicorn as suggested in your README.md for production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers=4", "--threads=2", "app:create_app()"]