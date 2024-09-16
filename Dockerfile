FROM apache/airflow:slim-2.10.0

# Switch to root to install additional packages
USER root

# Install system dependencies and clean up
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install gcc g++ -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy the requirements.txt file into the image
COPY requirements.txt /requirements.txt

# Switch back to the airflow user
USER airflow

# Install Python packages from requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt