# Use a specific Python version
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Copy requirements first to leverage caching
COPY requirements.txt .

# Install dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Expose port
EXPOSE 8080

# Set environment variables if needed
ENV PYTHONPATH=/app

# Start Uvicorn
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]