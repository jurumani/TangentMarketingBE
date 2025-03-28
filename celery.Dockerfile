# celery.Dockerfile
FROM python:3.11

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your project files
COPY . .

# Command to run Celery
CMD ["celery", "-A", "core", "worker", "--loglevel=debug"]