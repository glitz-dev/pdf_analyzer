# Use official Python image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy files
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 7860 (required for HF Spaces)
EXPOSE 7860

# Set environment variable to tell HF which port to use
ENV PORT=7860

# Start the Flask app
CMD ["python", "app.py"]
