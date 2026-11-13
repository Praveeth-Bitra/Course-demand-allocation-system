
from backend.database import get_connection


def record_allocation():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT
                s.section_id,
                s.course_id,
                s.term_id,
                s.capacity,
                s.scheduled_start,
                s.scheduled_end,
                wa.assignment_id,
                wa.faculty_id
            FROM sections s
            LEFT JOIN workload_assignments wa
                ON s.section_id = wa.section_id
            WHERE s.term_id = 'TERM-2027-EVEN'
            ORDER BY s.section_id
        """)

        sections = cursor.fetchall()

        cursor.execute("""
            SELECT forecast_id, course_id
            FROM demand_forecasts
            WHERE forecast_run_id = 'FORECAST-2027-EVEN-001'
        """)

        forecasts = {}

        for row in cursor.fetchall():
            forecasts[row[1]] = row[0]

        unmet_count = 0
        section_event_count = 0
        assignment_event_count = 0

        for section in sections:
            section_id = section[0]
            course_id = section[1]
            term_id = section[2]
            capacity = section[3]
            start_time = section[4]
            end_time = section[5]
            assignment_id = section[6]
            faculty_id = section[7]

            cursor.execute("""
                SELECT COUNT(*)
                FROM allocation_events
                WHERE section_id = %s
                  AND event_type = 'SECTION_PROPOSED'
            """, (section_id,))

            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO allocation_events (
                        section_id,
                        event_type,
                        previous_state,
                        new_state,
                        event_description
                    )
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    section_id,
                    "SECTION_PROPOSED",
                    None,
                    "PROPOSED",
                    "Section created for predicted course demand"
                ))

                section_event_count += 1

            if assignment_id:
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM allocation_events
                    WHERE assignment_id = %s
                      AND event_type = 'FACULTY_ASSIGNED'
                """, (assignment_id,))

                if cursor.fetchone()[0] == 0:
                    cursor.execute("""
                        INSERT INTO allocation_events (
                            section_id,
                            assignment_id,
                            event_type,
                            previous_state,
                            new_state,
                            event_description
                        )
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        section_id,
                        assignment_id,
                        "FACULTY_ASSIGNED",
                        None,
                        "PROPOSED",
                        f"Faculty {faculty_id} assigned to section"
                    ))

                    assignment_event_count += 1

            else:
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM faculty_skills
                    WHERE course_id = %s
                """, (course_id,))

                qualified_count = cursor.fetchone()[0]

                if qualified_count == 0:
                    issue_type = "NO_QUALIFIED_FACULTY"
                    description = "No faculty has the required course skill"

                else:
                    issue_type = "FACULTY_SCHEDULING_CONFLICT"
                    description = "Qualified faculty unavailable due to workload, schedule or availability constraints"

                cursor.execute("""
                    SELECT COUNT(*)
                    FROM unmet_demand
                    WHERE course_id = %s
                      AND term_id = %s
                      AND issue_type = %s
                """, (course_id, term_id, issue_type))

                if cursor.fetchone()[0] == 0:
                    forecast_id = forecasts.get(course_id)

                    if forecast_id is not None:
                        cursor.execute("""
                            INSERT INTO unmet_demand (
                                forecast_id,
                                course_id,
                                term_id,
                                unmet_quantity,
                                issue_type,
                                resolution_status
                            )
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (
                            forecast_id,
                            course_id,
                            term_id,
                            capacity,
                            issue_type,
                            "OPEN"
                        ))

                        unmet_count += 1

        connection.commit()

        print("\nALLOCATION HISTORY RECORDED")
        print("--------------------------------")
        print(f"Sections processed: {len(sections)}")
        print(f"Unmet demand records: {unmet_count}")
        print(f"Section events created: {section_event_count}")
        print(f"Assignment events created: {assignment_event_count}")

    except Exception as error:
        connection.rollback()
        print(f"Recording failed: {error}")

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    record_allocation()
