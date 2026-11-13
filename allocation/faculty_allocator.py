
from backend.database import get_connection


ASSIGNED_HOURS_PER_SECTION = 3.0


def get_faculty_candidates(cursor, course_id):
    cursor.execute("""
        SELECT
            f.faculty_id,
            f.max_workload_hours
        FROM faculty f
        JOIN faculty_skills fs
            ON f.faculty_id = fs.faculty_id
        WHERE fs.course_id = %s
          AND f.status = 'ACTIVE'
        ORDER BY fs.proficiency_level DESC,
                 fs.years_experience DESC
    """, (course_id,))

    return cursor.fetchall()


def is_faculty_available(cursor, faculty_id, start_time, end_time):
    cursor.execute("""
        SELECT availability_type
        FROM availability
        WHERE faculty_id = %s
          AND start_datetime <= %s
          AND end_datetime >= %s
    """, (faculty_id, start_time, end_time))

    records = cursor.fetchall()

    if not records:
        return False

    for record in records:
        if record[0] != "AVAILABLE":
            return False

    return True


def has_schedule_conflict(cursor, faculty_id, start_time, end_time):
    cursor.execute("""
        SELECT COUNT(*)
        FROM workload_assignments wa
        JOIN sections s
            ON wa.section_id = s.section_id
        WHERE wa.faculty_id = %s
          AND wa.status IN ('PROPOSED', 'APPROVED')
          AND s.scheduled_start < %s
          AND s.scheduled_end > %s
    """, (faculty_id, end_time, start_time))

    return cursor.fetchone()[0] > 0


def get_current_workload(cursor, faculty_id):
    cursor.execute("""
        SELECT COALESCE(SUM(assigned_hours), 0)
        FROM workload_assignments
        WHERE faculty_id = %s
          AND status IN ('PROPOSED', 'APPROVED')
    """, (faculty_id,))

    return float(cursor.fetchone()[0])


def allocate_faculty():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT
                section_id,
                course_id,
                scheduled_start,
                scheduled_end
            FROM sections
            WHERE term_id = 'TERM-2027-EVEN'
              AND status = 'PROPOSED'
            ORDER BY scheduled_start, section_id
        """)

        sections = cursor.fetchall()

        if not sections:
            print("No proposed sections found.")
            return

        cursor.execute("""
            SELECT COUNT(*)
            FROM workload_assignments wa
            JOIN sections s ON wa.section_id = s.section_id
            WHERE s.term_id = 'TERM-2027-EVEN'
        """)

        existing_assignments = cursor.fetchone()[0]

        if existing_assignments > 0:
            print("Faculty assignments already exist for this term.")
            print("Allocation stopped to prevent duplicate assignments.")
            return

        assignment_counter = 1
        assigned_count = 0
        unassigned_count = 0

        for section in sections:
            section_id = section[0]
            course_id = section[1]
            start_time = section[2]
            end_time = section[3]

            candidates = get_faculty_candidates(cursor, course_id)

            selected_faculty = None

            for candidate in candidates:
                faculty_id = candidate[0]
                max_hours = float(candidate[1])

                current_hours = get_current_workload(
                    cursor,
                    faculty_id
                )

                if current_hours + ASSIGNED_HOURS_PER_SECTION > max_hours:
                    continue

                if not is_faculty_available(
                    cursor,
                    faculty_id,
                    start_time,
                    end_time
                ):
                    continue

                if has_schedule_conflict(
                    cursor,
                    faculty_id,
                    start_time,
                    end_time
                ):
                    continue

                selected_faculty = faculty_id
                break

            if selected_faculty is None:
                unassigned_count += 1
                continue

            assignment_id = f"WLA-2027-{assignment_counter:06d}"

            cursor.execute("""
                INSERT INTO workload_assignments (
                    assignment_id,
                    section_id,
                    faculty_id,
                    assigned_hours,
                    assignment_role,
                    status
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                assignment_id,
                section_id,
                selected_faculty,
                ASSIGNED_HOURS_PER_SECTION,
                "PRIMARY",
                "PROPOSED"
            ))

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
                f"Faculty {selected_faculty} assigned to section {section_id}"
            ))

            assignment_counter += 1
            assigned_count += 1

        connection.commit()

        print("\nFACULTY ALLOCATION COMPLETED")
        print("--------------------------------")
        print(f"Total sections: {len(sections)}")
        print(f"Assigned sections: {assigned_count}")
        print(f"Unassigned sections: {unassigned_count}")
        print(f"Assignment events created: {assigned_count}")

    except Exception as error:
        connection.rollback()
        print(f"Faculty allocation failed: {error}")

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    allocate_faculty()
