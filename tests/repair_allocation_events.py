
from backend.database import get_connection


TERM_ID = "TERM-2027-EVEN"


def repair_events():
    connection = get_connection()
    cursor = connection.cursor()

    section_events_added = 0
    assignment_events_added = 0

    try:
        cursor.execute("""
            SELECT section_id, course_id
            FROM sections
            WHERE term_id = %s
        """, (TERM_ID,))

        sections = cursor.fetchall()

        for section_id, course_id in sections:
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
                    f"Section {section_id} created for course {course_id}"
                ))

                section_events_added += 1

        cursor.execute("""
            SELECT
                wa.assignment_id,
                wa.section_id,
                wa.faculty_id
            FROM workload_assignments wa
            JOIN sections s ON wa.section_id = s.section_id
            WHERE s.term_id = %s
        """, (TERM_ID,))

        assignments = cursor.fetchall()

        for assignment_id, section_id, faculty_id in assignments:
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
                    f"Faculty {faculty_id} assigned to section {section_id}"
                ))

                assignment_events_added += 1

        connection.commit()

        print("\nALLOCATION EVENT REPAIR COMPLETED")
        print("--------------------------------")
        print(f"Section events added: {section_events_added}")
        print(f"Assignment events added: {assignment_events_added}")

    except Exception as error:
        connection.rollback()
        print(f"Event repair failed: {error}")

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    repair_events()
