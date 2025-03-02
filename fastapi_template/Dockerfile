# Use an official Python runtime as a parent image
FROM python:3.10

# Set the working directory
WORKDIR /app

# Install system dependencies if needed (you might need some system libraries for certain Python packages)
RUN apt-get update && apt-get install -y \
    libpq-dev  # Required for psycopg2, you can add more if necessary

# Copy the requirements.txt first to leverage Docker cache (install dependencies first)
COPY ./requirements.txt /app/requirements.txt

# Install dependencies globally (we'll avoid using virtualenv in Docker since each container is already isolated)
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY ./app /app/app
COPY .env /app/.env
COPY ./alembic /app/alembic
COPY ./alembic.ini /app/alembic.ini
COPY ./main.py /app/main.py
COPY ./font /app/font
COPY ./images /app/images
COPY ./prestart.sh /app/prestart.sh
COPY ./backend_pre_start.py /app/backend_pre_start.py
COPY ./initial_data.py /app/initial_data.py

# Make sure prestart.sh is executable
RUN chmod +x /app/prestart.sh

# Expose the application port
EXPOSE 8081

# Start the application using prestart.sh
ENTRYPOINT ["/app/prestart.sh"]
