
from backend.database import get_connection


connection = get_connection()
cursor = connection.cursor()

try:
    cursor.execute("""
        SELECT
            TABLE_NAME,
            COLUMN_NAME,
            REFERENCED_TABLE_NAME
        FROM information_schema.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = DATABASE()
          AND REFERENCED_TABLE_NAME IN (
              'sections',
              'workload_assignments'
          )
        ORDER BY TABLE_NAME
    """)

    rows = cursor.fetchall()

    print("\nALLOCATION FOREIGN KEY REFERENCES")
    print("----------------------------------")

    if rows:
        for row in rows:
            print(row)
    else:
        print("No foreign key references found.")

finally:
    cursor.close()
    connection.close()
