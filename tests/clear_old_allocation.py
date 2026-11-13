
from backend.database import get_connection


connection = get_connection()
cursor = connection.cursor()

try:
    # Remove records in foreign-key dependency order.
    cursor.execute("DELETE FROM allocation_events")

    cursor.execute("DELETE FROM workload_assignments")

    cursor.execute(
        "DELETE FROM unmet_demand WHERE term_id = %s",
        ("TERM-2027-EVEN",)
    )

    cursor.execute(
        "DELETE FROM sections WHERE term_id = %s",
        ("TERM-2027-EVEN",)
    )

    connection.commit()

    print("Old allocation records cleared successfully.")

except Exception as error:
    connection.rollback()
    print(f"Cleanup failed: {error}")

finally:
    cursor.close()
    connection.close()
