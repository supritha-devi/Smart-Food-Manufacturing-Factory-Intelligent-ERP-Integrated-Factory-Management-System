# Smart Food Manufacturing Factory ERP

This repository contains the authentication and role-based access-control foundation for the Smart Food Manufacturing Factory ERP.

## Features

- Secure Flask login and logout
- Password hashing with Werkzeug
- Owner, Factory Admin, Production Supervisor, Salesman, and Accountant/Auditor roles
- Role and user-specific permissions
- Login attempt limits and temporary account locking
- CSRF protection and secure session cookies
- Owner-only employee account management
- Password changes and Owner password reset
- Audit logging for authentication and account changes
- PostgreSQL support with a SQLite local demonstration fallback
- Premium Caramel and Baby Pink interface theme

## Local setup

### Windows / PowerShell

```powershell
cd c:\Users\acer\OneDrive\Desktop\NIT
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python database\seed_users.py
python run.py
```

Open `http://127.0.0.1:5000/login`.

No database credentials are required for the local demonstration: omit `DATABASE_URL` to use `instance/smart_factory.db`.

### PostgreSQL setup

Set a PostgreSQL connection string in `.env`:

```text
DATABASE_URL=postgresql://postgres:password@localhost:5432/smart_factory
SECRET_KEY=a-long-random-secret
SESSION_COOKIE_SECURE=true
```

Then initialise users:

```powershell
python database/seed_users.py
```

`schema.sql` is PostgreSQL-ready and `schema.sqlite.sql` provides the local demonstration database.

## Integrated modules

The application includes connected database-backed workspaces for:

1. Authentication and RBAC
2. 2D factory layout and departments
3. Labour and workforce
4. Production configuration and BOM setup
5. Machines and capacity
6. Production planning and batches
7. First-time factory initialization wizard
8. Purchasing and procurement
9. Quality control and CAPA
10. Maintenance and work orders
11. Inventory and warehouses
12. Sales, GST invoices and payments
13. Financial management
14. Warehouse dispatch and logistics
15. Reports and audit trail
16. Owner operational dashboard
17. Premium caramel and baby pink theme
18. Interactive 2D factory map
19. Responsive 2D layout styling
20. Premium Caramel and Baby Pink unified theme

## Demo accounts

Replace all demonstration passwords before deploying to a real factory environment.

| Role | Email | Password |
|---|---|---|
| Owner | owner@smartfactory.com | Owner@123 |
| Factory Admin | admin@smartfactory.com | Admin@123 |
| Production Supervisor | supervisor@smartfactory.com | Supervisor@123 |
| Salesman A | sales1@smartfactory.com | Sales@123 |
| Salesman B | sales2@smartfactory.com | Sales@456 |
| Accountant / Auditor | auditor@smartfactory.com | Auditor@123 |

## Tests

```powershell
python -m pytest -q
```

## GitHub deployment workflow

1. Push this repository to GitHub.
2. Create a PostgreSQL database on Render or another hosted PostgreSQL provider.
3. Create a web service for this repository.
4. Set `DATABASE_URL`, `SECRET_KEY`, and `SESSION_COOKIE_SECURE=true` in hosting environment variables.
5. Use `pip install -r requirements.txt` as the build command.
6. Use `gunicorn run:app` as the start command.
7. Run `python database/seed_users.py` once after the database is reachable.

The repository includes `render.yaml` and `Procfile` for deployment automation.

## Security notes

- Demo credentials are for demonstration only.
- Password reset requests do not reveal whether an account exists.
- All mutations use server-side permission checks and parameterised database queries.
- The Owner should replace demo credentials immediately in any real deployment.
