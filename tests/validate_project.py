
import json
import os

from backend.database import get_connection


def check_database():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    checks = []

    queries = [
        (
            "Programs",
            "SELECT COUNT(*) AS total FROM programs",
            10
        ),
        (
            "Courses",
            "SELECT COUNT(*) AS total FROM courses",
            100
        ),
        (
            "Students",
            "SELECT COUNT(*) AS total FROM students",
            1000
        ),
        (
            "Faculty",
            "SELECT COUNT(*) AS total FROM faculty",
            50
        ),
        (
            "Student plans",
            "SELECT COUNT(*) AS total FROM student_plans",
            2000
        ),
        (
            "Registration interests",
            "SELECT COUNT(*) AS total FROM registration_interests",
            6000
        ),
        (
            "Faculty skills",
            "SELECT COUNT(*) AS total FROM faculty_skills",
            150
        ),
        (
            "Availability records",
            "SELECT COUNT(*) AS total FROM availability",
            105
        ),
        (
            "Historical registrations",
            "SELECT COUNT(*) AS total FROM student_course_history",
            3000
        ),
        (
            "Demand forecasts",
            """
            SELECT COUNT(*) AS total
            FROM demand_forecasts
            WHERE term_id = 'TERM-2027-EVEN'
            """,
            100
        ),
        (
            "Generated sections",
            """
            SELECT COUNT(*) AS total
            FROM sections
            WHERE term_id = 'TERM-2027-EVEN'
            """,
            71
        ),
        (
            "Faculty assignments",
            """
            SELECT COUNT(*) AS total
            FROM workload_assignments wa
            JOIN sections s ON wa.section_id = s.section_id
            WHERE s.term_id = 'TERM-2027-EVEN'
            """,
            55
        ),
        (
            "Prerequisite relationships",
            "SELECT COUNT(*) AS total FROM prerequisites",
            40
        )
    ]

    try:
        for name, query, expected in queries:
            cursor.execute(query)
            actual = cursor.fetchone()["total"]

            checks.append((
                name,
                actual == expected,
                actual,
                expected
            ))

        # Calculate expected unmet demand from forecast and section capacity.
        cursor.execute("""
            SELECT
                df.course_id,
                df.predicted_enrollment,
                COALESCE(SUM(s.capacity), 0) AS allocated_capacity
            FROM demand_forecasts df
            LEFT JOIN sections s
                ON df.course_id = s.course_id
               AND df.term_id = s.term_id
            WHERE df.forecast_run_id = 'FORECAST-2027-EVEN-001'
            GROUP BY df.course_id, df.predicted_enrollment
        """)

        forecast_rows = cursor.fetchall()

        expected_unmet = 0

        for row in forecast_rows:
            expected_unmet += max(
                int(row["predicted_enrollment"])
                - int(row["allocated_capacity"]),
                0
            )

        cursor.execute("""
            SELECT COALESCE(SUM(unmet_quantity), 0) AS total
            FROM unmet_demand
            WHERE term_id = 'TERM-2027-EVEN'
        """)

        actual_unmet = cursor.fetchone()["total"]

        checks.append((
            "Unmet demand",
            actual_unmet == expected_unmet,
            actual_unmet,
            expected_unmet
        ))

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM sections s
            JOIN rooms r ON s.room_id = r.room_id
            WHERE s.term_id = 'TERM-2027-EVEN'
              AND s.capacity > r.capacity
        """)

        actual = cursor.fetchone()["total"]

        checks.append((
            "Room capacity validation",
            actual == 0,
            actual,
            0
        ))

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM workload_assignments wa
            JOIN sections s ON wa.section_id = s.section_id
            LEFT JOIN faculty_skills fs
                ON fs.faculty_id = wa.faculty_id
               AND fs.course_id = s.course_id
            WHERE s.term_id = 'TERM-2027-EVEN'
              AND fs.faculty_id IS NULL
        """)

        actual = cursor.fetchone()["total"]

        checks.append((
            "Faculty skill validation",
            actual == 0,
            actual,
            0
        ))

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM (
                SELECT wa.faculty_id, wa.section_id
                FROM workload_assignments wa
                JOIN sections s ON wa.section_id = s.section_id
                WHERE s.term_id = 'TERM-2027-EVEN'
                GROUP BY wa.faculty_id, wa.section_id
                HAVING COUNT(*) > 1
            ) duplicates
        """)

        actual = cursor.fetchone()["total"]

        checks.append((
            "Duplicate assignment validation",
            actual == 0,
            actual,
            0
        ))

    finally:
        cursor.close()
        connection.close()

    return checks


def check_ground_truth():
    path = os.path.join(
        "data",
        "ground_truth",
        "anomaly_ground_truth.json"
    )

    if not os.path.exists(path):
        return False, "Ground-truth JSON file not found"

    with open(path, "r", encoding="utf-8") as file:
        cases = json.load(file)

    if len(cases) != 5:
        return False, "Expected 5 anomaly cases"

    for case in cases:
        if case.get("validation_status") != "PASS":
            return False, "Anomaly validation failed"

    return True, "5 anomaly cases validated"


def main():
    print("PROJECT-WIDE VALIDATION")
    print("=" * 50)

    checks = check_database()

    ground_truth_status, ground_truth_message = check_ground_truth()

    checks.append((
        "Anomaly ground truth",
        ground_truth_status,
        ground_truth_message,
        "PASS"
    ))

    print("\nFINAL VALIDATION REPORT")
    print("-" * 50)

    passed = 0

    for name, status, actual, expected in checks:
        result = "PASS" if status else "FAIL"

        print(
            "{}: {} (Actual: {}, Expected: {})".format(
                result,
                name,
                actual,
                expected
            )
        )

        if status:
            passed += 1

    print("-" * 50)
    print("Passed: {}/{}".format(passed, len(checks)))
    print("Failed: {}/{}".format(
        len(checks) - passed,
        len(checks)
    ))


if __name__ == "__main__":
    main()
