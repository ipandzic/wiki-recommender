# Use an official Python runtime as a parent image
FROM python:3.8-slim-buster

# Set environment variables
ARG DATABASE_NAME
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBUG 0
ENV DATABASE_NAME=$DATABASE_NAME

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y libpq-dev gcc

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Remove build dependencies
RUN apt-get autoremove -y gcc && apt-get clean

# Copy the current directory contents into the container
COPY . .

# Change to the directory containing manage.py
WORKDIR /app/recommender

# Run Django commands
RUN python manage.py collectstatic --noinput
