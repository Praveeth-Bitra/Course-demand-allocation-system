
from flask import Flask, render_template, jsonify

from backend.database import get_connection


app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static"
)


@app.route("/")
def dashboard():

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM demand_forecasts
            WHERE term_id = 'TERM-2027-EVEN'
        """)
        forecast_count = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM sections
            WHERE term_id = 'TERM-2027-EVEN'
        """)
        section_count = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM workload_assignments wa
            JOIN sections s ON wa.section_id = s.section_id
            WHERE s.term_id = 'TERM-2027-EVEN'
        """)
        assignment_count = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COALESCE(SUM(unmet_quantity), 0) AS total
            FROM unmet_demand
            WHERE term_id = 'TERM-2027-EVEN'
        """)
        unmet_demand = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT
                c.course_id,
                c.course_name,
                df.predicted_enrollment,
                df.confidence_score
            FROM demand_forecasts df
            JOIN courses c ON df.course_id = c.course_id
            WHERE df.term_id = 'TERM-2027-EVEN'
            ORDER BY df.predicted_enrollment DESC
            LIMIT 10
        """)
        forecasts = cursor.fetchall()

        cursor.execute("""
            SELECT
                ud.unmet_id,
                ud.course_id,
                c.course_name,
                ud.unmet_quantity,
                ud.issue_type,
                ud.resolution_status,
                ud.created_at
            FROM unmet_demand ud
            JOIN courses c ON ud.course_id = c.course_id
            WHERE ud.term_id = 'TERM-2027-EVEN'
            ORDER BY ud.created_at DESC
        """)
        unmet_records = cursor.fetchall()

        return render_template(
            "dashboard.html",
            forecast_count=forecast_count,
            section_count=section_count,
            assignment_count=assignment_count,
            unmet_demand=unmet_demand,
            forecasts=forecasts,
            unmet_records=unmet_records
        )

    finally:
        cursor.close()
        connection.close()


@app.route("/api/summary")
def api_summary():

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                (SELECT COUNT(*)
                 FROM demand_forecasts
                 WHERE term_id = 'TERM-2027-EVEN') AS forecasts,

                (SELECT COUNT(*)
                 FROM sections
                 WHERE term_id = 'TERM-2027-EVEN') AS sections,

                (SELECT COUNT(*)
                 FROM workload_assignments wa
                 JOIN sections s ON wa.section_id = s.section_id
                 WHERE s.term_id = 'TERM-2027-EVEN') AS assignments,

                (SELECT COALESCE(SUM(unmet_quantity), 0)
                 FROM unmet_demand
                 WHERE term_id = 'TERM-2027-EVEN') AS unmet_demand
        """)

        return jsonify(cursor.fetchone())

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
