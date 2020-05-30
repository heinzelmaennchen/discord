import mysql.connector
import os

# Helper functions to manage the database connections


def init_db():
    connection = mysql.connector.connect(host=os.environ['DATABASE_HOST'],
                                         user=os.environ['DATABASE_USER'],
                                         passwd=os.environ['DATABASE_PW'],
                                         database=os.environ['DATABASE_DB'])
    return connection


def check_connection(connection):
    try:
        connection.ping(reconnect=True, attempts=3, delay=5)
    except mysql.connector.Error:
        # reconnect your cursor as you did in __init__ or wherever
        connection = init_db()
    return connection
