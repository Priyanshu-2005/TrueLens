# Use the official Python 3.10 image as a base
FROM python:3.10-slim

# Set environment variables to avoid interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive
# Allow prints and logs to show up immediately
ENV PYTHONUNBUFFERED=1

# Install system dependencies
# tesseract-ocr is required for pytesseract document scanning
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# Hugging Face Spaces run as a non-root user (uid 1000)
# We must create a user and set up permissions properly
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Set the working directory
WORKDIR $HOME/app

# Copy requirements first to leverage Docker cache
COPY --chown=user requirements.txt .

# Install Python dependencies
# This includes PyTorch CPU and Transformers as defined in requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY --chown=user . .

# Hugging Face Spaces expects the app to run on port 7860
EXPOSE 7860

# Command to run the FastAPI application using Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
