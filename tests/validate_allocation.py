
from backend.database import get_connection


TERM_ID = "TERM-2027-EVEN"
FORECAST_RUN_ID = "FORECAST-2027-EVEN-001"


def run_validation():
    connection = get_connection()
    cursor = connection.cursor()

    checks = []

    try:
        cursor.execute("""
            SELECT COUNT(*)
            FROM sections
            WHERE term_id = %s
        """, (TERM_ID,))

        total_sections = cursor.fetchone()[0]
        checks.append(
            ("Section generation", total_sections == 71, total_sections)
        )

        cursor.execute("""
            SELECT COUNT(*)
            FROM sections s
            JOIN rooms r ON s.room_id = r.room_id
            WHERE s.term_id = %s
              AND s.capacity > r.capacity
        """, (TERM_ID,))

        invalid_capacity = cursor.fetchone()[0]
        checks.append(
            ("Room capacity", invalid_capacity == 0, invalid_capacity)
        )

        cursor.execute("""
            SELECT COUNT(*)
            FROM workload_assignments wa
            JOIN sections s ON wa.section_id = s.section_id
            LEFT JOIN faculty_skills fs
                ON wa.faculty_id = fs.faculty_id
               AND s.course_id = fs.course_id
            WHERE s.term_id = %s
              AND fs.skill_id IS NULL
        """, (TERM_ID,))

        invalid_skills = cursor.fetchone()[0]
        checks.append(
            ("Faculty skill matching", invalid_skills == 0, invalid_skills)
        )

        cursor.execute("""
            SELECT COUNT(*)
            FROM (
                SELECT wa.faculty_id
                FROM workload_assignments wa
                JOIN sections s ON wa.section_id = s.section_id
                JOIN faculty f ON wa.faculty_id = f.faculty_id
                WHERE s.term_id = %s
                  AND wa.status IN ('PROPOSED', 'APPROVED')
                GROUP BY wa.faculty_id, f.max_workload_hours
                HAVING SUM(wa.assigned_hours) > f.max_workload_hours
            ) AS violations
        """, (TERM_ID,))

        workload_violations = cursor.fetchone()[0]
        checks.append(
            ("Faculty workload", workload_violations == 0, workload_violations)
        )

        cursor.execute("""
            SELECT COUNT(*)
            FROM workload_assignments wa
            JOIN sections s ON wa.section_id = s.section_id
            WHERE s.term_id = %s
        """, (TERM_ID,))

        actual_assignments = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM workload_assignments wa
            JOIN sections s ON wa.section_id = s.section_id
            WHERE s.term_id = %s
              AND wa.status IN ('PROPOSED', 'APPROVED')
        """, (TERM_ID,))

        valid_assignments = cursor.fetchone()[0]

        checks.append((
            "Assignment records",
            valid_assignments == actual_assignments,
            actual_assignments
        ))

        cursor.execute("""
            SELECT COUNT(*)
            FROM allocation_events ae
            JOIN sections s ON ae.section_id = s.section_id
            WHERE s.term_id = %s
              AND ae.event_type = 'SECTION_PROPOSED'
        """, (TERM_ID,))

        section_events = cursor.fetchone()[0]

        checks.append((
            "Section event history",
            section_events == total_sections,
            section_events
        ))

        cursor.execute("""
            SELECT COUNT(*)
            FROM allocation_events ae
            JOIN sections s ON ae.section_id = s.section_id
            WHERE s.term_id = %s
              AND ae.event_type = 'FACULTY_ASSIGNED'
        """, (TERM_ID,))

        assignment_events = cursor.fetchone()[0]

        checks.append((
            "Assignment event history",
            assignment_events == actual_assignments,
            assignment_events
        ))

        # Calculate expected unmet demand from forecasts and section capacities.
        cursor.execute("""
            SELECT
                df.course_id,
                df.predicted_enrollment,
                COALESCE(SUM(s.capacity), 0)
            FROM demand_forecasts df
            LEFT JOIN sections s
                ON df.course_id = s.course_id
               AND df.term_id = s.term_id
            WHERE df.forecast_run_id = %s
            GROUP BY df.course_id, df.predicted_enrollment
        """, (FORECAST_RUN_ID,))

        forecast_rows = cursor.fetchall()

        expected_unmet = 0

        for course_id, predicted, allocated in forecast_rows:
            expected_unmet += max(
                int(predicted) - int(allocated),
                0
            )

        cursor.execute("""
            SELECT COALESCE(SUM(unmet_quantity), 0)
            FROM unmet_demand
            WHERE term_id = %s
        """, (TERM_ID,))

        recorded_unmet = int(cursor.fetchone()[0])

        checks.append((
            "Unmet demand recorded",
            recorded_unmet == expected_unmet,
            recorded_unmet
        ))

        print("\nALLOCATION VALIDATION REPORT")
        print("--------------------------------")

        passed = 0

        for name, result, value in checks:
            if result:
                print(f"PASS: {name} ({value})")
                passed += 1
            else:
                print(f"FAIL: {name} ({value})")

        print("--------------------------------")
        print(f"Expected unmet demand: {expected_unmet}")
        print(f"Passed: {passed}/{len(checks)}")
        print(f"Failed: {len(checks) - passed}/{len(checks)}")

    except Exception as error:
        print(f"Validation failed: {error}")

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    run_validation()
