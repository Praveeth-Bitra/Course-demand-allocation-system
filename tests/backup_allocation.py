
import csv
import os

from backend.database import get_connection


BACKUP_DIR = "data/exports/allocation_backup"

TABLES = [
    "sections",
    "workload_assignments",
    "unmet_demand",
    "allocation_events",
]


def backup_table(cursor, table_name):
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()

    column_names = [column[0] for column in cursor.description]

    file_path = os.path.join(BACKUP_DIR, f"{table_name}.csv")

    with open(file_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(column_names)
        writer.writerows(rows)

    print(f"{table_name}: {len(rows)} records backed up")


def main():
    os.makedirs(BACKUP_DIR, exist_ok=True)

    connection = get_connection()
    cursor = connection.cursor()

    try:
        for table in TABLES:
            backup_table(cursor, table)

        print("\nAllocation backup completed.")
        print(f"Location: {BACKUP_DIR}")

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()
