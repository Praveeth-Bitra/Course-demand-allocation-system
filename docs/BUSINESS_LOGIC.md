# Business Logic Documentation

This document describes the business rules, algorithms, and logic implemented in the YottaFlex Course Demand & Allocation System. It is intended for technical reviewers and hackathon evaluators to understand the exact behavior of the system.

---

## 2.1 Problem Definition

Educational institutions face a recurring planning challenge: predict student demand for courses in an upcoming term and allocate limited resources (classrooms, faculty, time slots) to satisfy that demand while respecting academic constraints (prerequisites, faculty expertise, workload limits, room capacities).

The system addresses this by:
1. **Forecasting** demand using historical enrollments and current registration interests.
2. **Generating** course sections that fit into available rooms and time slots.
3. **Assigning** qualified faculty to sections without exceeding workload or creating schedule conflicts.
4. **Tracking** unmet demand where constraints prevent full satisfaction.

---

## 2.2 Academic Data Model

The following entities and their key attributes form the core data model. Table and column names match the MySQL schema.

| Entity | Table | Key Columns | Role |
|--------|-------|-------------|------|
| **Program** | `programs` | `program_id`, `program_name`, `degree_level`, `duration_years`, `department_name`, `status` | Academic program (e.g., "BACHELOR in Computer Science") |
| **Course** | `courses` | `course_id`, `course_name`, `course_code`, `credits`, `course_type` (CORE/ELECTIVE/LAB), `description`, `status` | Individual course offering |
| **Student** | `students` | `student_id`, `student_name`, `email`, `admission_year`, `status` | Enrolled student |
| **Academic Term** | `academic_terms` | `term_id`, `academic_year`, `semester` (ODD/EVEN), `start_date`, `end_date`, `status` | Planning window (e.g., TERM-2027-EVEN) |
| **Student Plan** | `student_plans` | `plan_id`, `student_id`, `program_id`, `term_id`, `current_semester`, `plan_status` | Student's enrollment plan for a term |
| **Registration Interest** | `registration_interests` | `interest_id`, `plan_id`, `course_id`, `priority`, `interest_date`, `interest_status` | Student's desired courses for a term |
| **Course History** | `student_course_history` | `history_id`, `student_id`, `course_id`, `term_id`, `enrollment_status`, `final_grade`, `enrolled_at` | Actual past enrollments |
| **Faculty** | `faculty` | `faculty_id`, `faculty_name`, `department_name`, `email`, `max_workload_hours`, `employment_type`, `status` | Teaching staff |
| **Faculty Skill** | `faculty_skills` | `skill_id`, `faculty_id`, `course_id`, `proficiency_level` (INTERMEDIATE/ADVANCED/EXPERT), `years_experience` | Faculty qualification for a course |
| **Availability** | `availability` | `availability_id`, `faculty_id`, `start_datetime`, `end_datetime`, `availability_type` (AVAILABLE/LEAVE), `remarks` | Faculty time windows |
| **Room** | `rooms` | `room_id`, `room_name`, `building`, `capacity`, `room_type` (CLASSROOM/LAB/LECTURE_HALL), `status` | Physical teaching space |
| **Program-Course** | `program_courses` | `program_course_id`, `program_id`, `course_id`, `recommended_semester`, `is_mandatory` | Curriculum structure |
| **Prerequisite** | `prerequisites` | `prerequisite_id`, `course_id`, `prerequisite_course_id`, `minimum_grade`, `effective_from`, `effective_to` | Course dependencies |
| **Demand Forecast** | `demand_forecasts` | `forecast_id`, `course_id`, `term_id`, `forecast_run_id`, `historical_window_start`, `historical_window_end`, `predicted_enrollment`, `actual_enrollment`, `forecast_method`, `confidence_score` | Predicted demand |
| **Section** | `sections` | `section_id`, `course_id`, `term_id`, `room_id`, `section_number`, `capacity`, `scheduled_start`, `scheduled_end`, `status` | Generated class section |
| **Workload Assignment** | `workload_assignments` | `assignment_id`, `section_id`, `faculty_id`, `assigned_hours`, `assignment_role`, `status` | Faculty-to-section mapping |
| **Unmet Demand** | `unmet_demand` | `unmet_id`, `forecast_id`, `course_id`, `term_id`, `unmet_quantity`, `issue_type`, `resolution_status` | Demand not satisfied |
| **Allocation Event** | `allocation_events` | `event_id`, `section_id`, `assignment_id`, `event_type`, `previous_state`, `new_state`, `event_description` | Audit trail |

---

## 2.3 Course Demand Forecasting

### Inputs
| Source | Table | Filter | Metric |
|--------|-------|--------|--------|
| Historical Enrollment | `student_course_history` | `term_id = 'TERM-2026-ODD'` | Count of records per `course_id` |
| Registration Interest | `registration_interests` + `student_plans` | `student_plans.term_id = 'TERM-2027-EVEN'` | Count of interests per `course_id` |

### Forecasting Formula (WEIGHTED_70_30)
Implemented in `forecasting/forecast.py`:

```python
predicted_demand = int((0.7 * historical_count) + (0.3 * interest_count) + 0.5)
```

- **Historical weight:** 70%
- **Interest weight:** 30%
- **Rounding:** Add 0.5 and truncate to integer (round half up).

### Confidence Score Calculation
```python
historical_support = min(historical_count / 100, 1.0)
interest_support   = min(interest_count / 100, 1.0)
confidence = round(0.5 * historical_support + 0.5 * interest_support, 4)
```

- Each support metric caps at 1.0 (100 records = full support).
- Confidence is the average of the two supports.
- **Interpretation:** A data-support heuristic, **not** a calibrated probability of forecast accuracy. Higher values indicate more evidence; they do not guarantee lower error.

### Demand Categories
| Predicted Enrollment | Category |
|----------------------|----------|
| ≥ 50 | HIGH |
| 20–49 | MEDIUM |
| < 20 | LOW |

### Forecast Generation Process (`forecasting/run_forecast.py`)
1. Load all courses.
2. Aggregate historical counts (TERM-2026-ODD) and interest counts (TERM-2027-EVEN).
3. Compute forecasts for all 100 courses.
4. Check if `FORECAST-2027-EVEN-001` already exists; abort if yes.
5. Insert 100 records into `demand_forecasts` with:
   - `forecast_method = 'WEIGHTED_70_30'`
   - `confidence_score` as calculated
   - `actual_enrollment = NULL` (filled after term ends)

### Handling Missing Data
- Courses with no historical records → `historical_count = 0`
- Courses with no registration interests → `interest_count = 0`
- Both zero → `predicted_demand = 0`, `confidence = 0.0`

---

## 2.4 Section Generation Logic

Implemented in `allocation/section_generator.py`.

### Overview
For each course with `predicted_enrollment > 0`, the system creates one or more sections until demand is satisfied or no suitable rooms remain.

### Processing Order
Courses are topologically sorted by prerequisite dependencies (`order_courses_by_prerequisites`). A course is scheduled only after all its prerequisite sections have finished.

### Section Capacity
```python
section_capacity = min(remaining_demand, room_capacity)
```
- Each section fills up to the room's capacity.
- Multiple sections per course are created if demand > room capacity.

### Room Selection (`get_suitable_rooms`)
| Course Type | Eligible Room Types |
|-------------|---------------------|
| LAB | LAB only |
| CORE / ELECTIVE | CLASSROOM, LECTURE_HALL |

Rooms are sorted by capacity **descending** (largest first) to minimize section count.

### Time Slot Assignment (`get_schedule`)
- Term divided into **3 slots per day**: 09:00–11:00, 11:00–13:00, 14:00–16:00.
- Weekdays only (Mon–Fri).
- Each room tracks its next free slot (`room_usage[room_id]`).
- Prerequisite rule: a course's first section start time must be **after** the latest end time of all its prerequisite sections.

### Unmet Demand (ROOM_CAPACITY)
If no suitable room has a free slot before term end:
```sql
INSERT INTO unmet_demand (..., issue_type='ROOM_CAPACITY', ...)
VALUES (..., remaining_demand, ...)
```

### Circular Prerequisite Detection
Topological sort raises `ValueError` if a cycle is detected; generation aborts.

### Output
- 71 sections inserted into `sections` (status = 'PROPOSED').
- `unmet_demand` rows for any unsatisfied demand (issue_type = 'ROOM_CAPACITY').

---

## 2.5 Room Allocation Rules

| Rule | Implementation |
|------|----------------|
| Capacity | Section capacity ≤ room capacity (enforced by `min()`) |
| Type Match | LAB courses → LAB rooms only; others → CLASSROOM or LECTURE_HALL |
| No Double-Booking | `room_usage` counter ensures each room's slots are sequential |
| Availability | Only rooms with `status = 'AVAILABLE'` are considered |
| Term Bounds | Slots beyond `academic_terms.end_date` are skipped |

**When no suitable room is available:** Demand becomes unmet (ROOM_CAPACITY), no section created for that remainder.

---

## 2.6 Faculty Allocation Rules

Implemented in `allocation/faculty_allocator.py`.

### Assignment Constants
```python
ASSIGNED_HOURS_PER_SECTION = 3.0
```

### Candidate Selection (`get_faculty_candidates`)
```sql
SELECT f.faculty_id, f.max_workload_hours
FROM faculty f
JOIN faculty_skills fs ON f.faculty_id = fs.faculty_id
WHERE fs.course_id = ? AND f.status = 'ACTIVE'
ORDER BY fs.proficiency_level DESC, fs.years_experience DESC
```
- Only faculty with the required course skill.
- Ordered by proficiency (EXPERT > ADVANCED > INTERMEDIATE) then experience.

### Availability Check (`is_faculty_available`)
Faculty must have an `availability` record covering the section's time window with `availability_type = 'AVAILABLE'`. Any `LEAVE` record overlapping the window disqualifies them.

### Schedule Conflict Check (`has_schedule_conflict`)
No existing `workload_assignments` (status PROPOSED/APPROVED) for the same faculty where section times overlap.

### Workload Limit (`get_current_workload`)
Sum of `assigned_hours` for PROPOSED/APPROVED assignments. Candidate rejected if:
```python
current_hours + 3.0 > max_workload_hours
```

### Selection Logic
First candidate passing **all three checks** (skill, availability, workload, conflict) is assigned.

### Unassigned Sections
If no candidate passes, section remains unassigned. `record_allocation.py` later logs this as unmet demand with:
- `issue_type = 'NO_QUALIFIED_FACULTY'` (zero skilled faculty) OR
- `issue_type = 'FACULTY_SCHEDULING_CONFLICT'` (skilled faculty exist but all unavailable/overloaded/conflicted)

### Output
- 55 `workload_assignments` (status = 'PROPOSED').
- 55 `allocation_events` (event_type = 'FACULTY_ASSIGNED').
- 16 sections unassigned → unmet demand records.

---

## 2.7 Prerequisite Business Rules

### Scheduling Dependency
In `section_generator.py`, a course's first section start time must be **strictly after** the latest end time of all its prerequisite sections:
```python
if prerequisite_end is None or start_datetime > prerequisite_end:
    # slot is valid
```

### Effective Windows
Prerequisites are filtered by date:
```sql
WHERE (effective_from IS NULL OR effective_from <= term_end)
  AND (effective_to IS NULL OR effective_to >= term_start)
```

### Circular Detection
Topological sort (Kahn's algorithm) detects cycles before generation starts. If detected, the process aborts with an error.

---

## 2.8 Unmet Demand

Two distinct categories are tracked in `unmet_demand`:

| Issue Type | Source | Meaning |
|------------|--------|---------|
| **ROOM_CAPACITY** | `section_generator.py` | Forecast demand exceeds total available room capacity across all suitable rooms and time slots. |
| **NO_QUALIFIED_FACULTY** | `record_allocation.py` | Zero faculty possess the required course skill. |
| **FACULTY_SCHEDULING_CONFLICT** | `record_allocation.py` | Qualified faculty exist but none can be assigned (workload, availability, or schedule conflict). |

**Important:** ROOM_CAPACITY unmet demand is calculated during section generation. Faculty-related unmet demand is calculated *after* faculty allocation, for sections that were generated but received no faculty assignment. They are **not** the same thing.

### Unmet Quantity
- ROOM_CAPACITY: remaining demand after exhausting rooms.
- Faculty types: the full `capacity` of the unassigned section.

### Resolution Status
All unmet demand records are inserted with `resolution_status = 'OPEN'`.

---

## 2.9 Allocation Event Tracking

Table: `allocation_events`

| Event Type | Trigger | Description |
|------------|---------|-------------|
| `SECTION_PROPOSED` | `record_allocation.py` (if missing) | Section created for predicted demand |
| `FACULTY_ASSIGNED` | `faculty_allocator.py` + `record_allocation.py` (if missing) | Faculty assigned to section |

Fields recorded: `section_id`, `assignment_id` (nullable), `event_type`, `previous_state`, `new_state`, `event_description`.

---

## 2.10 Validation Rules

Implemented in `tests/validate_project.py`, `tests/validate_allocation.py`, `tests/validate_exports.py`, and supporting scripts.

| Check | Script | Expected |
|-------|--------|----------|
| Row counts per master table | `validate_project` | Programs=10, Courses=100, Students=1000, Faculty=50, Plans=2000, Interests=6000, Skills=150, Availability=105, History=3000 |
| Forecast count | `validate_project` | 100 (TERM-2027-EVEN) |
| Section count | `validate_project` / `validate_allocation` | 71 |
| Faculty assignment count | `validate_project` / `validate_allocation` | 55 |
| Prerequisite count | `validate_project` | 40 |
| Unmet demand total | `validate_project` / `validate_allocation` | Matches calculated (forecast - allocated capacity) |
| Room capacity violation | `validate_project` / `validate_allocation` | 0 sections where capacity > room capacity |
| Faculty skill mismatch | `validate_project` / `validate_allocation` | 0 assignments without matching skill |
| Faculty workload violation | `validate_allocation` | 0 faculty exceeding max_workload_hours |
| Duplicate assignment | `validate_project` | 0 duplicate (faculty, section) pairs |
| Section event completeness | `validate_allocation` | 1 SECTION_PROPOSED per section |
| Assignment event completeness | `validate_allocation` | 1 FACULTY_ASSIGNED per assignment |
| Export JSON readable | `validate_exports` | PASS |
| Export SQL exists | `validate_exports` | PASS |
| CSV row counts match JSON | `validate_exports` | All 18 tables match |
| Anomaly ground truth | `validate_project` (via `check_ground_truth`) | 5 cases, all PASS |
| FK integrity (allocation) | `check_allocation_fks` | PASS |
| Prerequisite schedule | `check_prerequisite_schedule` | PASS |
| Room constraints | `check_room_constraints` | PASS |

---

## 2.11 Business Logic Limitations

| Limitation | Impact |
|------------|--------|
| **Static time slots** | Only 3 fixed slots per day; no support for variable-length classes. |
| **Single-term optimization** | No multi-term lookahead; faculty workload resets per term. |
| **Greedy room allocation** | Largest-room-first may fragment capacity sub-optimally. |
| **First-fit faculty** | Does not globally optimize faculty utilization; may leave assignable sections unassigned. |
| **No waitlisting** | Unmet demand is recorded but not queued for future resolution. |
| **Hard-coded term** | All logic targets `TERM-2027-EVEN` and `FORECAST-2027-EVEN-001`; not parameterized for arbitrary terms. |
| **No grade-based prerequisite enforcement** | `minimum_grade` column exists but is not validated during scheduling. |
| **No student-level section assignment** | Sections have capacities but no individual student enrollment is simulated. |

These are known constraints of the current implementation, not bugs.

---
