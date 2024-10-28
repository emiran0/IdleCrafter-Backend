# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y
# Copy the requirements file into the container
COPY requirements.txt /app/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# Copy the rest of the application code into the container
COPY . /app/

# Copy the .env file into the container
COPY .env /app/

# Expose the port that the app runs on
EXPOSE 8000

# Run the command to start the application
CMD ["uvicorn", "API.api_app:app", "--host", "192.168.1.183", "--port", "8000"]