# Use the official Python image from the Docker Hub
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt


# Copy the project
COPY . /app/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY start_celery.sh /app/
RUN chmod +x /app/start_celery.sh

# Use entrypoint
ENTRYPOINT ["sh", "./entrypoint.sh"]