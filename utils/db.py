import mysql.connector
from mysql.connector import pooling
import os

_db_pool = None

def get_db_connection():
    """
    Retrieves a connection from the connection pool.
    Initializes the pool if it doesn't exist.
    """
    global _db_pool
    if _db_pool is None:
        _db_pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="wlcbot_pool",
            pool_size=5,
            pool_reset_session=True,
            host=os.environ['DATABASE_HOST'],
            user=os.environ['DATABASE_USER'],
            passwd=os.environ['DATABASE_PW'],
            database=os.environ['DATABASE_DB'],
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
    
    return _db_pool.get_connection()


