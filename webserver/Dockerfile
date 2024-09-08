# Use the official Python image from the Docker Hub with a slim variant
FROM python:3.11-slim

# Set environment variables to avoid Python writing .pyc files and to ensure stdout/stderr are unbuffered
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY ./requirements.txt /app/webserver/requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r webserver/requirements.txt
RUN pip list

# Create a non-root user and switch to that user
RUN useradd -m myuser
USER myuser

# Copy the current directory contents into the container at /app
COPY . /app/webserver

# Expose port 8000 for the FastAPI app
EXPOSE 8000

# Run the FastAPI app with gunicorn and uvicorn workers
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "webserver.main:app"]
# CMD ["sh"]
