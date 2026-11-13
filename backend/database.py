import mysql.connector
from backend.config import DB_CONFIG


def get_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection

    except mysql.connector.Error as error:
        print(f"Database connection failed: {error}")
        raise


def test_connection():
    connection = None

    try:
        connection = get_connection()

        cursor = connection.cursor()
        cursor.execute("SELECT DATABASE(), VERSION()")

        result = cursor.fetchone()

        print("Database connection successful!")
        print(f"Database: {result[0]}")
        print(f"MySQL Version: {result[1]}")

        cursor.close()

    finally:
        if connection and connection.is_connected():
            connection.close()
