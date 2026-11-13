
from backend.database import get_connection


def check_prerequisite_schedule():

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT
                p.course_id,
                p.prerequisite_course_id,
                s1.section_id,
                s1.scheduled_start,
                s2.section_id,
                s2.scheduled_start
            FROM prerequisites p
            JOIN sections s1
                ON s1.course_id = p.course_id
            JOIN sections s2
                ON s2.course_id = p.prerequisite_course_id
            WHERE s1.term_id = 'TERM-2027-EVEN'
              AND s2.term_id = 'TERM-2027-EVEN'
            ORDER BY p.course_id
        """)

        records = cursor.fetchall()

        print("\nPREREQUISITE SCHEDULING REPORT")
        print("-" * 90)

        violations = 0

        for row in records:

            course_id = row[0]
            prerequisite_id = row[1]
            course_section = row[2]
            course_start = row[3]
            prerequisite_section = row[4]
            prerequisite_start = row[5]

            status = (
                "PASS"
                if prerequisite_start < course_start
                else "FAIL"
            )

            if status == "FAIL":
                violations += 1
                print("\n***PREREQUISITE SCHEDULING VIOLATION***")

            print(
                status,
                "| Course:", course_id,
                "| Prerequisite:", prerequisite_id,
                "| Course section:", course_section,
                "| Course starts:", course_start,
                "| Prerequisite section:", prerequisite_section,
                "| Prerequisite starts:", prerequisite_start
            )

        print("\nTotal relationships checked:", len(records))
        print("Scheduling violations:", violations)

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    check_prerequisite_schedule()
