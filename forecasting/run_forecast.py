
from backend.database import get_connection
from forecasting.forecast import calculate_forecasts


TARGET_TERM = "TERM-2027-EVEN"
FORECAST_RUN_ID = "FORECAST-2027-EVEN-001"


connection = get_connection()
cursor = connection.cursor()

cursor.execute(
    "SELECT course_id, course_name FROM courses ORDER BY course_id"
)
courses = cursor.fetchall()

cursor.execute(
    """SELECT course_id, COUNT(*)
    FROM student_course_history
    WHERE term_id = 'TERM-2026-ODD'
    GROUP BY course_id"""
)

historical_records = cursor.fetchall()

historical = {}

for record in historical_records:
    historical[record[0]] = record[1]


cursor.execute(
    """SELECT ri.course_id, COUNT(*)
    FROM registration_interests ri
    JOIN student_plans sp
        ON ri.plan_id = sp.plan_id
    WHERE sp.term_id = %s
    GROUP BY ri.course_id""",
    (TARGET_TERM,)
)

interest_records = cursor.fetchall()

interests = {}

for record in interest_records:
    interests[record[0]] = record[1]


cursor.execute(
    """SELECT start_date, end_date
    FROM academic_terms
    WHERE term_id = %s""",
    (TARGET_TERM,)
)

target_dates = cursor.fetchone()

cursor.execute(
    """SELECT start_date, end_date
    FROM academic_terms
    WHERE term_id = 'TERM-2026-ODD'"""
)

historical_dates = cursor.fetchone()

cursor.execute(
    """SELECT COUNT(*)
    FROM demand_forecasts
    WHERE forecast_run_id = %s""",
    (FORECAST_RUN_ID,)
)

existing_run = cursor.fetchone()[0]

cursor.close()
connection.close()


if target_dates is None or historical_dates is None:
    print("Academic term information not found.")

elif existing_run > 0:
    print("This forecast run already exists.")
    print("Use a new forecast run ID for another forecast.")

else:

    forecasts = calculate_forecasts(
        courses,
        historical,
        interests
    )

    connection = get_connection()
    cursor = connection.cursor()

    forecast_records = []

    for forecast in forecasts:

        record = (
            forecast[0],
            TARGET_TERM,
            FORECAST_RUN_ID,
            historical_dates[0],
            historical_dates[1],
            forecast[3],
            None,
            "WEIGHTED_70_30",
            forecast[4]
        )

        forecast_records.append(record)

    try:

        cursor.executemany(
            """INSERT INTO demand_forecasts
            (course_id, term_id, forecast_run_id,
            historical_window_start, historical_window_end,
            predicted_enrollment, actual_enrollment,
            forecast_method, confidence_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            forecast_records
        )

        connection.commit()

        high = 0
        medium = 0
        low = 0

        for forecast in forecasts:

            if forecast[5] == "HIGH":
                high += 1
            elif forecast[5] == "MEDIUM":
                medium += 1
            else:
                low += 1

        print("\nCOURSE DEMAND FORECAST")
        print("----------------------")
        print("Target Term:", TARGET_TERM)
        print("Forecast Run:", FORECAST_RUN_ID)
        print("Total Courses:", len(forecasts))
        print("High Demand:", high)
        print("Medium Demand:", medium)
        print("Low Demand:", low)
        print("Forecasts saved successfully.")

        print("\nTOP 10 COURSES BY PREDICTED DEMAND")

        sorted_forecasts = sorted(
            forecasts,
            key=lambda item: item[3],
            reverse=True
        )

        for forecast in sorted_forecasts[:10]:

            print(
                forecast[0],
                "Historical:", forecast[1],
                "Interest:", forecast[2],
                "Predicted:", forecast[3],
                "Category:", forecast[5]
            )

    except Exception as error:

        connection.rollback()
        print("Forecast insertion failed:", error)

    finally:

        cursor.close()
        connection.close()
