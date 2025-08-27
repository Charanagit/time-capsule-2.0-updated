# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make sure your templates and static files are in the correct place
RUN mkdir -p /app/templates /app/static

# Expose the port the app runs on
EXPOSE 5000

# Set environment variables (if any, like Flask environment)
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Define the command to run your app
CMD ["flask", "run"]
