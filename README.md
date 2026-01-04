# Profile Service – COMP2001 Coursework 2

This repository contains a Python Flask microservice developed for COMP2001 Coursework 2.

The microservice provides CRUD (Create, Read, Update, Delete) operations for managing user profiles and connects to a Microsoft SQL Server database hosted on the University of Plymouth infrastructure.

---

## Features
- Create a new user profile
- Retrieve all profiles
- Retrieve a single profile
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

## Authentication and Authorisation
The microservice integrates with the Authenticator API provided as part of the coursework.

User identity is validated at runtime and role-based access control is enforced:
- **Admin** and **staff** users can manage all profiles
- **Standard users** can only access and modify their own profile

The following users are supported via the Authenticator API:
- grace.hopper
- ada.lovelace
- tim.berners-lee

---

## Configuration (Environment Variables)

The service reads configuration values from environment variables:

- `DB_SERVER`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `AUTH_API_URL`

Sensitive credentials are not committed to source control.

---

## API Documentation

The API is documented using OpenAPI.  
A static OpenAPI specification is provided in `openapi.yaml`.

---

## Running the Service (Docker)

### Prerequisites
- Docker and Docker Compose installed
- FortiClient VPN connected
- Access to the University of Plymouth SQL Server

---

### Configuration

Create an environment file from the provided example:

```bash
cp .env.example .env


DB_SERVER=dist-6-505.uopnet.plymouth.ac.uk
DB_NAME=DATABASE_NAME
DB_USER=YOUR_USERNAME
DB_PASSWORD=YOUR_PASSWORD
AUTH_API_URL=https://web.socem.plymouth.ac.uk/COMP2001/auth/api/users


docker compose up --build
http://localhost:8000
GET http://localhost:8000/health
X-User: <username>
X-User: grace.hopper
