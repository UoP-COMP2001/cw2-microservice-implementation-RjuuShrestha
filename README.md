# Profile Service – COMP2001 Coursework 2

This repository contains a Python Flask microservice developed for COMP2001 Coursework 2.

The microservice provides CRUD (Create, Read, Update, Delete) operations for managing user profiles and connects to a Microsoft SQL Server database hosted on the University of Plymouth infrastructure.

---

## Features
- Create a new user profile
- Retrieve all profiles
- Update an existing profile
- Delete a profile
- Health check endpoint

---

## Technologies Used
- Python 3
- Flask
- pyodbc
- Microsoft SQL Server
- Postman (API testing)

---

## Database
The service connects to a dedicated Microsoft SQL Server database provided by the University of Plymouth.

All database operations are handled using stored procedures created in Coursework 1.

Database credentials are not included in this repository.

---

## Configuration (Database Credentials)

This service reads database connection details from environment variables:

- DB_SERVER
- DB_NAME
- DB_USER
- DB_PASSWORD

---

## API Documentation

The API is documented using OpenAPI.
- Swagger UI available when the service is running
- Static specification provided in `openapi.yaml`

## Running the Service Locally

### Windows PowerShell example
```powershell
$env:DB_SERVER="dist-6-505.uopnet.plymouth.ac.uk"
$env:DB_NAME="COMP2001_AShrestha"
$env:DB_USER="YOUR_USERNAME"
$env:DB_PASSWORD="YOUR_PASSWORD"
python app.py

### Prerequisites
- Python 3 installed
- FortiClient VPN connected
- Access to the University SQL Server

### Installation
```bash
pip install flask pyodbc


