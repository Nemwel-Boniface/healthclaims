# Health Claims Adjudication Engine

Health Claims is an enterprise-grade backend service designed for real-time medical claim processing. The platform integrates directly with hospitals and insurers to validate member eligibility, verify benefit coverage, and detect fraud signals instantaneously.

This application demonstrates mastery in:

- **Service Layer Architecture**: Decoupling business rules (adjudication) from transport logic (REST).
- **The Gateway Pattern**: Abstracting third-party data access for future microservice scalability.
- **Financial Integrity**: Implementing Idempotency to prevent double-deduction of member balances.
- **Production Awareness**: High-performance database indexing and structured logging for auditability.
- **Test-Driven Development (TDD)**: Comprehensive suite covering complex business edge cases.

---

# Architectural Decisions

## 1. Service Layer Pattern

Instead of bloating Django views, all adjudication logic resides in `ClaimProcessorService`.  
This makes the core **"Brain"** of the app portable, reusable, and easily testable.

## 2. Gateway Pattern

The `InsurerGateway` isolates the **"where" and "how"** we find `Member` or `Procedure` data.

If Ginja AI eventually moves member data to an external API, we only update the Gateway — leaving the adjudication logic untouched.

## 3. Idempotency (The "Double-Tap" Protection)

In health claims, a network glitch can lead to duplicate submissions.

By using an `X-Idempotency-Key` header, we ensure a member's balance is **never deducted twice for the same request**.


## Adjudication Rules
The engine processes every claim against these 4 automated checks:
| Rule | Logic | Result if Failed |
| :--- | :--- | :--- |
| **Member Eligibility** | Checks if `is_active` is true. | REJECTED |
| **Benefit Limit** | Checks if `benefit_balance` > 0. | REJECTED |
| **Fraud Detection** | Flags if `claim_amount` > 2x the procedure's average cost. | FLAG & PROCEED |
| **Balance Capping** | If `claim_amount` > `benefit_balance`, it approves the remaining balance only. | PARTIAL |


## Data Model
- **Members**: Tracks eligibility status and remaining benefit balances.
- **Providers**: Registered healthcare facilities.
- **Procedures**: Common medical codes with average cost benchmarks for fraud detection.
- **Claims**: The central ledger of all processed requests and their outcomes.
- **IdempotencyRecords**: Stores request keys to prevent duplicate financial processing.

## Logging & Audit Trail
The system uses structured logging to track the lifecycle of a claim. Every adjudication event includes the `UserID` and `MemberID` for security auditing.
- **INFO**: Successful adjudications and fraud flags.
- **WARNING**: Denied or Rejected claims.
- **ERROR**: System or database failures.

---

# Built With

- Python 3.12
- Django
- Django REST Framework
- PostgreSQL (Production database)
- Docker & Docker Compose (Containerization)
- Gunicorn (Production WSGI server)
- Pytest (Automated testing)

---

# Getting Started

## Prerequisites

- Python 3.12+
- PostgreSQL (if running manually)
- Docker Desktop (Optional but recommended)

---

# Manual Setup (Without Docker)

If you prefer to run the app outside Docker:

## 1. Clone the Repository

```bash
git clone git@github.com:Nemwel-Boniface/healthclaims.git
cd healthclaims
```

## 2. Setup Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

To create a virtual environment with pip, use the following commands:

```bash
pip install pipenv
pipenv install
```

After running above commands run `pip install -r requirements.txt` to install all packages used.

## 3. Environment Configuration

Create a .env file in the project root:

```bash
DATABASE_URL=postgres://your_user:your_password@localhost:5432/healthclaims
DEBUG=True
```

## 4. Initialize (Run these to create db tables, run migrations and load seed data)

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py seed_data

```

 To run the server:
```bash
python manage.py runserver
```

Access the app to test via the base URL: `http://127.0.0.1:8000/`


## Docker Setup (Recommended)

1. Run the entire stack (Django + PostgreSQL) with one command: `sudo docker-compose up --build`

2. To run in detached mode: `sudo docker-compose up -d --build`

3. Check running containers: `sudo docker-compose ps`.
> Note: The web service should show Up and the db service should show Up (healthy).

4. Apply Database Migrations `sudo docker-compose exec web python manage.py migrate`

5. Run Seed Data to Populate the database with initial members, providers, and procedures: `sudo docker-compose exec web python manage.py seed_data`

6. Run the Test Suite to Verify both claims (business logic) and users (auth logic) tests: `sudo docker-compose exec web pytest`

7. View logs: `sudo docker-compose logs -f web`

8. Access the API at (Base URL): `http://127.0.0.1:8000/`


### Troubleshooting & System Reset

If you encounter persistent errors, "ModuleNotFound" issues, or if the Docker environment becomes corrupted, run the following commands to perform a Deep Reset.
1. The "Clean Slate" Reset - This command stops all services, removes the network, and deletes the database volume. Use this if you want to start with a completely fresh database. `sudo docker-compose down -v --remove-orphans`

2. The "Nuclear" Rebuild - Use this if the code isn't updating correctly or dependencies are missing. This removes all stopped containers and the entire build cache before rebuilding:

```bash
# Warning: This clears all unused Docker data on your system
sudo docker system prune -a -f

# Rebuild from scratch
sudo docker-compose up --build -d
```

Check running containers: `sudo docker-compose ps`.
> Note: The web service should show Up and the db service should show Up (healthy).

<img width="1046" height="192" alt="Image" src="https://github.com/user-attachments/assets/c0b2070d-17e5-4828-b06e-18f292a0767b" />

3. Re-initialize after Reset - After performing a reset, you must re-apply migrations and seed data:

```bash
sudo docker-compose exec web python manage.py migrate
sudo docker-compose exec web python manage.py seed_data
```

<img width="1093" height="545" alt="Image" src="https://github.com/user-attachments/assets/1e35402c-1afc-48c2-a820-e7a631566367" />

> Pro-Tip - If the db service stays in a starting state too long, check the logs specifically for the database:

```bash
sudo docker-compose logs db
```

<img width="1093" height="545" alt="Image" src="https://github.com/user-attachments/assets/838f6a8e-6717-44a7-9a29-15c45a19d3d1" />


## API Endpoints & Usage
1. User Registration

POST `/api/v1/auth/register/`

```
{
  "username": "nemwelb",
  "email": "nemwel@ginja.ai",
  "password": "strongpassword123",
  "first_name": "Nemwel",
  "last_name": "Boniface"
}
```

2. Login (Obtain JWT Token)

POST `/api/v1/auth/login/`

```
{
  "email": "nemwel@ginja.ai",
  "password": "strongpassword123"
}
```

Response includes:

```
{
  "access": "your_access_token",
  "refresh": "your_refresh_token"
}
```

3. Submit a Claim

POST `/api/v1/claims/`

Headers:

```
Authorization: Bearer <your_access_token>
X-Idempotency-Key: <unique_uuid_or_string>
Content-Type: application/json
```

Body:

```
{
  "member_id": "M123",
  "provider_id": "H456",
  "diagnosis_code": "D001",
  "procedure_code": "P001",
  "claim_amount": 5000.00
}
```

Example Response:

```
{
  "claim_id": "C789",
  "status": "APPROVED",
  "fraud_flag": false,
  "approved_amount": 40000
}
```

## Testing

The test suite covers the 4 core adjudication rules:
1. Member Eligibility (Active vs Inactive)
2. Benefit Limits
3. Fraud Detection Rules
4. Partial Approvals

Run all tests: `sudo docker-compose exec web pytest` or `python manage.py test users` or `python manage.py test claims`


### Production-Ready Features

1. JWT-based authentication
2. Idempotent claim submissions
3. Fraud detection simulation logic
4. Service-layer architecture
5. Gateway abstraction for external integrations
6. Structured logging
7. Database indexing for performance
8. Dockerized deployment


## Author

👤 **Nemwel Boniface**

- GitHub: [@Nemwel Boniface](https://github.com/Nemwel-Boniface)
- Twitter: [@Nemwel Boniface](https://twitter.com/nemwel_bonie)
- LinkedIn: [@Nemwel Bonifacej](https://www.linkedin.com/in/nemwel-nyandoro/)


## Contributing

Contributions, issues, and feature requests are welcome!

Feel free to check the [issues page](https://github.com/Nemwel-Boniface/healthclaims/issues).

## Show your support

Give a ⭐️ if you like this project!