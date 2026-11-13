# YottaFlex: Course Demand & Allocation System

The **YottaFlex Course Demand & Allocation System** is an end-to-end academic planning tool designed to optimize resource allocation for educational institutions. It integrates synthetic data generation, demand forecasting, classroom management, and faculty assignment to support administrative decision-making for upcoming academic terms.

## Project Overview

Efficient academic planning is critical to student success and institutional efficiency. This system addresses the complexity of balancing fluctuating course demand with limited faculty, classroom availability, and prerequisite constraints.

Key capabilities include:
- **Predictive Analytics:** Forecasting course enrollment demand based on historical data and student registration interests.
- **Automated Scheduling:** Converting forecasts into viable class sections with appropriate room and capacity matching.
- **Faculty Optimization:** Assigning faculty based on skill sets, workload limitations, and scheduling availability.
- **Administrative Insight:** A dashboard providing a high-level view of system health, unmet demand, and planning metrics.

## Key Features

- **Data Generation:** Synthetic data engine to simulate academic environments (students, programs, courses, faculty, and rooms).
- **Course Forecasting:** Weighted demand calculation model (70% historical, 30% student interest).
- **Automated Sectioning:** Intelligent section generation that respects room capacities, prerequisite sequences, and resource usage constraints.
- **Constraint-Aware Allocation:** Faculty allocation logic that validates skills, workload hours, and schedule conflicts.
- **Visualization:** Integrated Flask dashboard featuring enrollment analysis and summary statistics using Chart.js.
- **Data Validation & Export:** Comprehensive validation scripts and automated exports to JSON, SQL, and CSV formats.

## System Architecture

The workflow follows a structured sequence:

1. **Master Data Generation:** Initialize system state.
2. **Student & Historical Transactions:** Simulate historical trends and future interests.
3. **Course Forecasting:** Predict enrollment for the target term.
4. **Sectioning:** Generate sections based on demand.
5. **Allocation:** Distribute faculty to sections.
6. **Visualization:** View results via the web dashboard.
7. **Export & Validate:** Generate reports and run constraint checks.

## Technology Stack

- **Backend:** Python, Flask
- **Database:** MySQL (using `mysql-connector-python`)
- **Frontend:** HTML5, CSS3, Bootstrap 5, JavaScript, Chart.js
- **Data Processing:** Pandas, NumPy
- **Configuration:** python-dotenv

## Database Design

The database maintains the following primary entities:
- `programs` & `courses`: Institutional curriculum structure.
- `students`, `faculty`, & `rooms`: Resource entities.
- `academic_terms`: Temporal planning windows.
- `demand_forecasts`: Predicted course demand data.
- `sections`: Generated class sections.
- `workload_assignments`: Faculty assignments to sections.
- `unmet_demand`: Tracking of shortages in enrollment capacity.
- `allocation_events`: Audit trail for state changes.

## Forecasting Methodology

The system uses a weighted forecasting model:
- **Inputs:** Historical enrollment counts (for a comparable prior term) and current registration interest data.
- **Formula:** `Predicted Demand = (0.7 * Historical Count) + (0.3 * Interest Count)`
- **Confidence Score:** Derived from the support levels of historical and registration data (50/50 split), providing a measure of model reliability.

## Section and Faculty Allocation

- **Section Generation:** Demand is processed in an order based on prerequisite dependencies. The system seeks the first available room that meets the required capacity and room type criteria.
- **Faculty Allocation:** The allocator selects the highest-proficient and most-qualified available faculty member who has remaining workload capacity and no schedule conflicts.
- **Status Tracking:** Sections and assignments are tracked as `PROPOSED`, and unresolved demand is logged in the `unmet_demand` table for review.

## Project Structure

```text
C:\CandidateWorkspace
├── allocation/         # Faculty and section allocation logic
├── backend/            # Flask app and database connectivity
├── data/               # Datasets and exports (CSV, JSON, SQL)
├── database/           # Schema definitions
├── docs/               # Project documentation
├── forecasting/        # Demand calculation and update scripts
├── frontend/           # Static assets and Jinja2 templates
├── generator/          # Synthetic data generation scripts
├── tests/              # Validation and constraint testing scripts
└── venv/               # Virtual environment dependencies
```

## Installation and Setup

*Prerequisites: MySQL server running locally.*

1.  **Clone/Download:** Open the project folder.
2.  **Dependencies:** Ensure a virtual environment is active and install requirements:
    ```powershell
    # (If using existing environment, verify packages are installed)
    pip install Flask mysql-connector-python pandas numpy python-dotenv
    ```
3.  **Database Configuration:** Create a MySQL database (e.g., `course_demand_db`).
4.  **Environment:** Copy `.env.example` to `.env` and configure your database credentials.
5.  **Initialize Data:** Run generation scripts in the following order:
    ```powershell
    python -m generator.main
    python -m generator.relationships
    python -m generator.student_transactions
    python -m generator.history_transactions
    ```
6.  **Run Forecasting:** Execute the forecasting pipeline:
    ```powershell
    python -m forecasting.run_forecast
    ```
7.  **Generate Sections/Allocation:** Run the planning scripts:
    ```powershell
    python -m allocation.section_generator
    python -m allocation.faculty_allocator
    python -m allocation.record_allocation
    ```

## Running the Application

Start the Flask dashboard:
```powershell
python -m backend.app
```
Access the application at `http://127.0.0.1:5000`. Stop the server by pressing `CTRL+C` in the terminal.

## Validation and Testing

Verify the integrity of the generated data and the allocation constraints using:
```powershell
python -m tests.validate_project
python -m tests.validate_allocation
python -m tests.validate_exports
```

## Current Implementation Status

- **Implemented:** All core forecasting, allocation, and dashboard features.
- **Constraints:** The system currently allocates faculty based on predefined priorities. Some sections may remain unassigned if constraints are too restrictive; these are logged as unmet demand.
- **Validation:** All automated tests confirm data consistency and constraint compliance.

## Future Improvements

- Implementation of a GUI for manual override of faculty assignments.
- Integration of complex room-conflict algorithms.
- Support for multi-term scheduling optimization.
- Improved visualization of faculty workload balances.

---
*Generated for the YottaFlex Hackathon.*
