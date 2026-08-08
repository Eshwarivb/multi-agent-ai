# Use the official Python 3.11 slim image as the base
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies
# - git: For repository operations and PyGithub interactions
# - patch: To apply the generated unified diffs
RUN apt-get update && apt-get install -y \
    git \
    patch \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt first to leverage Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Define the entrypoint to run the main application
ENTRYPOINT ["python", "app.py"]

# By default, show help if no arguments are provided
CMD ["--help"]
