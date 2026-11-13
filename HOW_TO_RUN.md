# How to Run the YottaFlex System

This guide provides step-by-step instructions to set up, generate data, run forecasts, allocate resources, validate results, and launch the dashboard on Windows using PowerShell.

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.10+ | Tested on 3.11 |
| MySQL Server | 8.0+ | Running locally on default port 3306 |
| Git | Any | Optional, for cloning |
| VS Code / Terminal | Any | PowerShell 5.1+ or PowerShell 7+ |

**Python Dependencies** (install via pip):
```text
Flask==3.1.3
mysql-connector-python==26.10.0
pandas==3.1.1
numpy==2.4.6
python-dotenv==1.2.4
```

---

## Environment Setup

### 1. Open the Project Directory
```powershell
cd C:\CandidateWorkspace
```

### 2. Create and Activate Virtual Environment (if not already present)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```powershell
pip install Flask mysql-connector-python pandas numpy python-dotenv
```

### 4. Configure Environment Variables
Copy the example file and edit it with your MySQL credentials:
```powershell
Copy-Item .env.example .env
notepad .env
```

**Required `.env` values:**
```ini
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=course_demand_db
```

> **Never commit real credentials.** The `.env` file is git-ignored.

---

## Database Setup

### 1. Start MySQL Server
Ensure the MySQL service is running:
```powershell
net start mysql80
# Or: Start-Service mysql80
```

### 2. Create the Database
```powershell
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS course_demand_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

### 3. Initialize Schema
The schema is created automatically by the generator scripts when they run their first `INSERT` statements (tables use `IF NOT EXISTS`). No separate SQL script is required.

### 4. Verify Connectivity
```powershell
python -c "from backend.database import test_connection; test_connection()"
```
Expected output:
```text
Database connection successful!
Database: course_demand_db
MySQL Version: 8.x.x
```

---

## Data Generation

Run the generator scripts **in this exact order**. Each script depends on tables created by the previous ones.

| Step | Command | Tables Populated | Description |
|------|---------|------------------|-------------|
| 1 | `python -m generator.main` | `programs`, `courses`, `students`, `faculty`, `rooms`, `academic_terms` | Master academic data (10 programs, 100 courses, 1000 students, 50 faculty, 10 rooms, 2 terms) |
| 2 | `python -m generator.relationships` | `program_courses`, `prerequisites` | Program-course mappings and prerequisite chains |
| 3 | `python -m generator.student_transactions` | `student_plans`, `registration_interests` | Student academic plans (2 per student) and course interests (up to 3 per plan) |
| 4 | `python -m generator.history_transactions` | `student_course_history` | Historical enrollments for TERM-2026-ODD (3000 records) |
| 5 | `python -m generator.faculty_transactions` | `faculty_skills`, `availability` | Faculty skills (3 per faculty), term availability, and 5 leave records |

### Verification After Generation
```powershell
python -m tests.validate_project
```
All 18 checks should pass (see Validation section for details).

---

## Forecasting

### Prerequisites
- All data generation steps completed.
- Historical term: `TERM-2026-ODD`
- Target term: `TERM-2027-EVEN`
- Forecast run ID: `FORECAST-2027-EVEN-001`

### Run Forecast
```powershell
python -m forecasting.run_forecast
```

### What It Does
- Reads historical enrollments from `student_course_history` (TERM-2026-ODD).
- Reads registration interests from `registration_interests` for TERM-2027-EVEN.
- Calculates predicted demand: `0.7 * historical + 0.3 * interest`.
- Computes confidence score from data support levels.
- Inserts 100 records into `demand_forecasts`.

### Expected Output
```text
COURSE DEMAND FORECAST
----------------------
Target Term: TERM-2027-EVEN
Forecast Run: FORECAST-2027-EVEN-001
Total Courses: 100
High Demand: X
Medium Demand: Y
Low Demand: Z
Forecasts saved successfully.
```

---

## Section and Faculty Allocation

Run these **in sequence**. Each step depends on the previous one.

| Step | Command | Purpose |
|------|---------|---------|
| 1 | `python -m allocation.section_generator` | Generates 71 sections for TERM-2027-EVEN based on forecast demand, room capacity, and prerequisite order. Populates `sections` and `unmet_demand` (ROOM_CAPACITY). |
| 2 | `python -m allocation.faculty_allocator` | Assigns faculty to proposed sections. Validates skills, workload (max hours), availability, and schedule conflicts. Populates `workload_assignments` and `allocation_events` (FACULTY_ASSIGNED). |
| 3 | `python -m allocation.record_allocation` | Records section-proposal events, links assignment events, and writes unmet-demand records for sections without qualified faculty (NO_QUALIFIED_FACULTY or FACULTY_SCHEDULING_CONFLICT). |

### Key Dependencies
- `section_generator` requires `demand_forecasts`, `rooms`, `academic_terms`, `prerequisites`.
- `faculty_allocator` requires `sections` (status=PROPOSED), `faculty_skills`, `availability`, `workload_assignments` (empty).
- `record_allocation` requires `sections`, `workload_assignments`, `demand_forecasts`, `faculty_skills`.

### Expected Results
- 71 sections generated.
- 55 faculty assignments created.
- 16 sections remain unassigned (logged as unmet demand).
- 126 allocation events recorded.

---

## Validation

Run these commands to verify data integrity and business-rule compliance.

### Core Validation Suite
```powershell
# Full project validation (18 checks)
python -m tests.validate_project

# Allocation-specific validation (8 checks)
python -m tests.validate_allocation

# Export integrity validation (20 checks)
python -m tests.validate_exports
```

### Additional Constraint Checks
```powershell
# Foreign key integrity on allocation tables
python -m tests.check_allocation_fks

# Prerequisite scheduling violations
python -m tests.check_prerequisite_schedule

# Room capacity violations
python -m tests.check_room_constraints
```

### Anomaly Ground Truth Validation
```powershell
# Generates and validates 5 synthetic anomaly test cases
python -m generator.anomalies
```

### Expected Outcome
All checks report `PASS`. Any `FAIL` indicates a data or logic issue that must be resolved before submission.

---

## Data Export

Generate portable dataset exports (CSV, JSON, SQL) for submission or analysis.

```powershell
python -m generator.export_data
```

### Output Location
```
data/exports/
├── csv/                    # One CSV per table (18 files)
├── project_data.json       # Complete database snapshot (4.3 MB)
└── project_data.sql        # Full schema + INSERT statements (0.97 MB)
```

### Verification
```powershell
python -m tests.validate_exports
```
Confirms JSON readability, SQL existence, and row-count parity between JSON and CSV for all 18 tables.

---

## Running the Dashboard

### Start the Flask Application
```powershell
python -m backend.app
```

### Access the Dashboard
Open a browser and navigate to:
```
http://127.0.0.1:5000
```

### Dashboard Features
- **Stats Cards:** Total forecasts, sections, faculty assignments, unmet demand.
- **Bar Chart:** Top 10 courses by predicted enrollment (Chart.js).
- **Table:** Course ID, name, predicted enrollment, confidence score.

### Stop the Server
Press `CTRL+C` in the PowerShell terminal.

### Common Startup Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `mysql.connector.Error: Access denied` | Wrong credentials in `.env` | Verify DB_USER, DB_PASSWORD, DB_HOST |
| `mysql.connector.Error: Unknown database` | Database not created | Run `CREATE DATABASE` step |
| `ModuleNotFoundError` | Dependencies not installed | Run `pip install -r requirements.txt` (or manual list) |
| `Address already in use` | Port 5000 occupied | Stop other Flask instances or change port in `app.py` |

---

## Complete Execution Sequences

### First-Time Setup (Fresh Database)
```powershell
# 1. Environment
cd C:\CandidateWorkspace
.\venv\Scripts\Activate.ps1
pip install Flask mysql-connector-python pandas numpy python-dotenv
Copy-Item .env.example .env
notepad .env  # Configure DB credentials

# 2. Database
net start mysql80
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS course_demand_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 3. Generate Master Data
python -m generator.main
python -m generator.relationships
python -m generator.student_transactions
python -m generator.history_transactions
python -m generator.faculty_transactions

# 4. Verify Generation
python -m tests.validate_project

# 5. Run Forecast
python -m forecasting.run_forecast

# 6. Run Allocation Pipeline
python -m allocation.section_generator
python -m allocation.faculty_allocator
python -m allocation.record_allocation

# 7. Validate Allocation
python -m tests.validate_allocation

# 8. Export Data
python -m generator.export_data
python -m tests.validate_exports

# 9. Launch Dashboard
python -m backend.app
```

### Normal Startup (Existing Data)
```powershell
cd C:\CandidateWorkspace
.\venv\Scripts\Activate.ps1
net start mysql80
python -m backend.app
```
> **Do not re-run generator or allocation scripts** unless you intend to reset the database. The dashboard reads from the existing database.

---

## Quick Reference Card

| Task | Command |
|------|---------|
| Activate venv | `.\venv\Scripts\Activate.ps1` |
| Test DB connection | `python -c "from backend.database import test_connection; test_connection()"` |
| Full validation | `python -m tests.validate_project` |
| Allocation validation | `python -m tests.validate_allocation` |
| Export validation | `python -m tests.validate_exports` |
| Run forecast | `python -m forecasting.run_forecast` |
| Generate sections | `python -m allocation.section_generator` |
| Assign faculty | `python -m allocation.faculty_allocator` |
| Record allocation | `python -m allocation.record_allocation` |
| Export data | `python -m generator.export_data` |
| Start dashboard | `python -m backend.app` |

---
