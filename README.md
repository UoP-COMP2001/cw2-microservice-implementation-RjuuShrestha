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
- Docker
- Postman (API testing)

---

## Database
The service connects to a dedicated Microsoft SQL Server database provided by the University of Plymouth.

All database operations are implemented in Python using `pyodbc`, in line with the Coursework 2 guidance. Database credentials are not stored in the repository.

---

## Configuration (Database Credentials)

The service reads database connection details from environment variables:

- `DB_SERVER`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`

Credentials must be provided at runtime and are not committed to source control for security reasons.

---

## API Documentation

The API is documented using OpenAPI.
A static OpenAPI specification is provided in `openapi.yaml`.

## Running the Service Locally


### Prerequisites
- Python 3 installed
- FortiClient VPN connected
- Access to the University SQL Server


### Installation
```bash
pip install flask pyodbc


### Windows PowerShell example
```powershell
$env:DB_SERVER="dist-6-505.uopnet.plymouth.ac.uk"
$env:DB_NAME="DATABASE_NAME"
$env:DB_USER="YOUR_USERNAME"
$env:DB_PASSWORD="YOUR_PASSWORD"
python app.py


docker build -t yourdockerhubusername/cw2-profile-service .


docker run -p 8000:8000 ^
  -e DB_SERVER=dist-6-505.uopnet.plymouth.ac.uk ^
  -e DB_NAME=DATABASE_NAME ^
  -e DB_USER=YOUR_USERNAME ^
  -e DB_PASSWORD=YOUR_PASSWORD ^
  yourdockerhubusername/cw2-profile-service


The service will be available at:
http://localhost:8000