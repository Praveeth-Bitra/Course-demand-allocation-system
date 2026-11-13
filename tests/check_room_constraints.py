
from backend.database import get_connection


def check_room_constraints():

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT
                room_id,
                COUNT(*)
            FROM sections
            WHERE term_id = 'TERM-2027-EVEN'
            GROUP BY room_id
        """)

        print("\nROOM SECTION COUNTS")

        for row in cursor.fetchall():
            print(row)

        cursor.execute("""
            SELECT
                s1.section_id,
                s1.room_id,
                s1.scheduled_start,
                s1.scheduled_end,
                s2.section_id,
                s2.scheduled_start,
                s2.scheduled_end
            FROM sections s1
            JOIN sections s2
                ON s1.room_id = s2.room_id
               AND s1.section_id < s2.section_id
               AND s1.scheduled_start < s2.scheduled_end
               AND s1.scheduled_end > s2.scheduled_start
            WHERE s1.term_id = 'TERM-2027-EVEN'
              AND s2.term_id = 'TERM-2027-EVEN'
        """)

        conflicts = cursor.fetchall()

        print("\nROOM SCHEDULING CONFLICTS:", len(conflicts))

        for conflict in conflicts:
            print(conflict)

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    check_room_constraints()
