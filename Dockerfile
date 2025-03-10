# Use the Python 3.9 Buster image
FROM python:3.9-buster
#FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libjpeg-dev \
    libblas-dev \
    liblapack-dev \
    libatlas-base-dev \
    gfortran

# Upgrade pip to the latest version
RUN pip install --upgrade pip

# Install Python dependencies
RUN pip install --no-cache-dir --pre duckdb
RUN pip install --no-cache-dir prefect pandas jsonlines

# Copy the rest of the application code (including pipeline.py)
COPY . .

# Expose the Prefect server port
EXPOSE 4200

# Define the command to run the application
CMD ["python", "pipeline.py"]