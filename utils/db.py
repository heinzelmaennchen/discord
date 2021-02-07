import mysql.connector
import os

# Helper functions to manage the database connections


def init_db():
    connection = mysql.connector.connect(host=os.environ['DATABASE_HOST'],
                                         user=os.environ['DATABASE_USER'],
                                         passwd=os.environ['DATABASE_PW'],
                                         database=os.environ['DATABASE_DB'],
                                         charset='utf8mb4',
                                         collation='utf8mb4_unicode_ci')
    return connection


def check_connection(connection):
    try:
        connection.ping(reconnect=True, attempts=3, delay=5)
    except mysql.connector.Error:
        # reconnect the cursor
        connection = init_db()
    return connection
