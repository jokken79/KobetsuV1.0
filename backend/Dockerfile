FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including LibreOffice and Japanese fonts
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    libreoffice-writer \
    fonts-ipafont \
    fonts-ipaexfont \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
