
from backend.database import get_connection
from forecasting.forecast import calculate_forecasts


FORECAST_RUN_ID = "FORECAST-2027-EVEN-001"


def update_confidence():

    connection = get_connection()
    cursor = connection.cursor()

    try:
        # Get course IDs
        cursor.execute("""
            SELECT course_id
            FROM courses
            ORDER BY course_id
        """)

        courses = cursor.fetchall()

        # Get historical enrollment counts
        cursor.execute("""
            SELECT course_id, COUNT(*)
            FROM student_course_history
            WHERE term_id = 'TERM-2026-ODD'
            GROUP BY course_id
        """)

        historical = {
            row[0]: row[1]
            for row in cursor.fetchall()
        }

        # Get current registration interest counts
        cursor.execute("""
            SELECT ri.course_id, COUNT(*)
            FROM registration_interests ri
            JOIN student_plans sp
                ON ri.plan_id = sp.plan_id
            WHERE sp.term_id = 'TERM-2027-EVEN'
            GROUP BY ri.course_id
        """)

        interests = {
            row[0]: row[1]
            for row in cursor.fetchall()
        }

        # Calculate updated confidence scores
        forecasts = calculate_forecasts(
            courses,
            historical,
            interests
        )

        updated_count = 0

        for forecast in forecasts:

            course_id = forecast[0]
            confidence = forecast[4]

            cursor.execute("""
                UPDATE demand_forecasts
                SET confidence_score = %s
                WHERE course_id = %s
                  AND forecast_run_id = %s
            """, (
                confidence,
                course_id,
                FORECAST_RUN_ID
            ))

            updated_count += cursor.rowcount

        connection.commit()

        print("Confidence score update completed.")
        print("Forecast records updated:", updated_count)

        # Display updated confidence scores
        cursor.execute("""
            SELECT
                course_id,
                predicted_enrollment,
                confidence_score
            FROM demand_forecasts
            WHERE forecast_run_id = %s
            ORDER BY predicted_enrollment DESC
            LIMIT 10
        """, (FORECAST_RUN_ID,))

        print("\nTop 10 updated forecasts:")

        for row in cursor.fetchall():
            print(row)

    except Exception as error:
        connection.rollback()
        print("Update failed:", error)

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    update_confidence()
