# Use an official Python runtime as a parent image
FROM python:3.10

# Set environment variables to prevent interactive prompts and ensure logs flush
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# --- Removed appuser creation ---
# RUN groupadd -r appuser && useradd --no-log-init -r -g appuser appuser

# Install system dependencies
# Combine update, install, and clean in one layer to reduce image size
# Use --no-install-recommends to avoid installing unnecessary packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    # Add any other system dependencies here
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker cache
# Removed --chown flag as files will now be owned by root
COPY ./requirements.txt /app/requirements.txt

# Install Python dependencies
# Using --no-cache-dir reduces image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
# Removed --chown flag as files will now be owned by root
# Note: Ensure .env is not copied; use runtime environment variables instead.
COPY ./app /app/app
COPY ./alembic /app/alembic
COPY ./alembic.ini /app/alembic.ini
COPY ./main.py /app/main.py
COPY ./prestart.sh /app/prestart.sh
COPY ./backend_pre_start.py /app/backend_pre_start.py
COPY ./initial_data.py /app/initial_data.py

# Make prestart.sh executable (This instruction IS correct)
# Permissions are now set for the root user
RUN chmod +x /app/prestart.sh

# --- Removed USER appuser ---
# USER appuser
# By default, subsequent commands and the container will run as root

# Expose the application port (doesn't publish the port, just documents it)
EXPOSE 8081

# Start the application using prestart.sh (exec form is preferred)
# This will now be executed by the root user
ENTRYPOINT ["sh","/app/prestart.sh"]
# Or ENTRYPOINT ["sh", "/app/prestart.sh"] if you prefer that method
