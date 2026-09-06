# Folium: AI-Powered Clinical Documentation Platform Backend

## 🎯 Features

### Backend (FastAPI)

- RESTful API with automatic OpenAPI docs
- Async Python for high performance
- Patient management and clinical records
- Interaction tracking (visits, calls, appointments)
- Clinical document management (notes, labs, imaging, uploads)
- AI service orchestration
- CORS configuration for frontend
- Docker containerization
- PostgreSQL database with SQLAlchemy ORM
- Alembic migrations for schema management
- Auto-seeding with test data on startup

## 🗄️ Database Setup

### Connection

PostgreSQL runs in Docker Compose. Connection configured via environment variables:

```
DATABASE_URL=postgresql+asyncpg://folium:folium@postgres:5432/folium_db
```

### Migrations

Alembic manages database schema changes:

```bash
# Create a new migration after model changes
docker compose exec folium-backend alembic revision --autogenerate -m "Description"

# Apply pending migrations
docker compose exec folium-backend alembic upgrade head

# Rollback last migration
docker compose exec folium-backend alembic downgrade -1

# View migration history
docker compose exec folium-backend alembic history
```

### Seed Data

Synthetic data automatically seeds on startup via `app/main.py`: users, three
patients, patient-owned encounters, diagnostic reports with observations,
clinical documents with attachments, and an imaging study.

Run maintenance commands through the running Compose service. This uses the same
image, network, and injected environment settings as the API.

To reseed the native synthetic clinical graph:

```bash
docker compose exec folium-backend python -m app.seed_db
```

To reset and recreate synthetic patient-owned clinical data:

```bash
docker compose exec folium-backend python -m app.clear_data
docker compose exec folium-backend python -m app.seed_db
```

### Database Console

Access PostgreSQL directly:

```bash
docker compose exec folium-postgres psql -U folium -d folium_db

# Useful queries
\dt                           # List tables
SELECT * FROM patient;        # View patients
```

## 📊 Core API Endpoints

### Patients

- `GET /api/patients` - List all patients
- `GET /api/patients/{id}` - Get patient details
- `GET /api/v1/patients/{id}/timeline` - Get a patient's ordered clinical history

### Imaging Studies

- `GET /api/v1/imaging-studies/?patientId={id}` - List patient-owned imaging studies.
- `GET /api/v1/imaging-studies/{study_id}` - Get one imaging study.
- `POST /api/v1/imaging-studies/` - Create a patient-owned imaging study.

### Clinical Documents

- `GET /api/clinical-documents?patientId={id}` - List patient documents
- `GET /api/clinical-documents/{id}` - Get document details
- `POST /api/clinical-documents?patientId={id}` - Create document

### Diagnostic Reports

- `POST /api/v1/diagnostic-reports/` - Create a patient-owned diagnostic report
  with its atomic observations.
- `GET /api/v1/diagnostic-reports/{report_id}` - Get a diagnostic report and its
  observations.

### Encounters

- `GET /api/v1/encounters/?patientId={id}` - List a patient's encounters and
  their narratives.
- `GET /api/v1/encounters/{encounter_id}` - Get one encounter and its narratives.
- `POST /api/v1/encounters/` - Create a patient-owned encounter.
- `POST /api/v1/encounters/{encounter_id}/narratives` - Add raw narrative content
  to an encounter.

For complete API documentation, see [SPEC.md](./SPEC.md)

## 🛠️ Development

### Local Development (Docker)

```bash
# Start all services
docker compose up

# View logs
docker compose logs folium-backend -f

# Restart backend after code changes
docker compose restart folium-backend

# Access backend shell
docker compose exec folium-backend sh
```

### Database Management

```bash
# Run migrations
docker compose exec folium-backend alembic upgrade head

# Create new migration
docker compose exec folium-backend alembic revision --autogenerate -m "Add field"

# Reset and reseed synthetic patient-owned clinical data
docker compose exec folium-backend python -m app.clear_data
docker compose exec folium-backend python -m app.seed_db
```

### API Testing

Interactive API docs available at:

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>

```bash
# Health check
curl http://localhost:8000/health

# List patients
curl http://localhost:8000/api/v1/patients

# Get the patient timeline
curl "http://localhost:8000/api/v1/patients/{id}/timeline"
```
