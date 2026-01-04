# Profile Service – COMP2001 Coursework 2

This repository contains a Python Flask microservice developed for COMP2001 Coursework 2.

The microservice provides CRUD operations for managing user profiles and connects to a Microsoft SQL Server database hosted on the University of Plymouth infrastructure.

---

## Features
- Create new users (validated via Authenticator API)
- Create user profiles
- Retrieve all profiles (role-restricted)
- Retrieve a single profile (role-restricted)
- Update profiles (role-restricted)
- Delete profiles (role-restricted)
- Role-based access control
- Health check endpoint
- OpenAPI specification

---

## Technologies Used
- Python 3
- Flask
- pyodbc
- Microsoft SQL Server
- Docker / Docker Compose
- Postman

---

## Authentication and Authorisation
The service integrates with the COMP2001 Authenticator API.

Role-based access control is enforced:
- **Admin / Staff**: full access
- **User**: access limited to own profile

Supported accounts:
- `grace.hopper`
- `ada.lovelace`
- `tim.berners-lee`


All protected endpoints require the following header:
```
X-User: <username>
```

Example:
```
X-User: grace.hopper
```


---

## Configuration

Create a `.env` file with the following variables:

```env
DB_SERVER=dist-6-505.uopnet.plymouth.ac.uk
DB_NAME=YOUR_DATABASE_NAME
DB_USER=YOUR_USERNAME
DB_PASSWORD=YOUR_PASSWORD
AUTH_API_URL=https://web.socem.plymouth.ac.uk/COMP2001/auth/api/users
```

---

## Running the Service (Docker)

### Prerequisites
- Docker and Docker Compose
- VPN connection if required for SQL Server access


### Build and Run
```
docker compose up --build
```

The service will be available at:
```
http://localhost:8000
```