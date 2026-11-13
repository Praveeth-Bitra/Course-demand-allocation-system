
from backend.database import get_connection
from forecasting.forecast import calculate_forecasts


def check_confidence():

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT course_id
            FROM courses
            ORDER BY course_id
        """)

        courses = cursor.fetchall()

        cursor.execute("""
            SELECT course_id, COUNT(*)
            FROM student_course_history
            WHERE term_id = 'TERM-2026-ODD'
            GROUP BY course_id
        """)

        historical = dict(cursor.fetchall())

        cursor.execute("""
            SELECT ri.course_id, COUNT(*)
            FROM registration_interests ri
            JOIN student_plans sp
                ON ri.plan_id = sp.plan_id
            WHERE sp.term_id = 'TERM-2027-EVEN'
            GROUP BY ri.course_id
        """)

        interests = dict(cursor.fetchall())

        forecasts = calculate_forecasts(
            courses,
            historical,
            interests
        )

        print("\nCALCULATED CONFIDENCE SCORES")
        print("-" * 65)

        for forecast in forecasts[:15]:
            print(
                forecast[0],
                "Historical:", forecast[1],
                "Interests:", forecast[2],
                "Confidence:", forecast[4]
            )

        cursor.execute("""
            SELECT
                COUNT(*),
                MIN(confidence_score),
                MAX(confidence_score)
            FROM demand_forecasts
            WHERE forecast_run_id = %s
        """, ("FORECAST-2027-EVEN-001",))

        print("\nSTORED CONFIDENCE SCORES")
        print(cursor.fetchone())

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    check_confidence()
