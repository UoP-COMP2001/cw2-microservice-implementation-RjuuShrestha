FROM python:3.11-slim-bookworm

# Set working directory
WORKDIR /app

# Install system dependencies for pyodbc + SQL Server driver
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    gnupg \
    unixodbc \
    unixodbc-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Add Microsoft package signing key
RUN curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor \
    > /usr/share/keyrings/microsoft-prod.gpg

# Add Microsoft SQL Server repo (Debian 12 / bookworm)
RUN echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] \
    https://packages.microsoft.com/debian/12/prod bookworm main" \
    > /etc/apt/sources.list.d/microsoft-prod.list

# Install SQL Server ODBC driver
RUN apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql17 && \
    rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose Flask port
EXPOSE 8000

# Run the application
CMD ["python", "app.py"]
