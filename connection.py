import psycopg2
from psycopg2 import OperationalError

#DB_HOST = 'localhost'
#DB_NAME = 'TheCreativeCornerstone'
#DB_USER = 'postgres'
#DB_PASS = 'Aaditya@123'

DB_HOST = 'localhost'
DB_NAME = 'brightkid'
DB_USER = 'fmug'
DB_PASS = 'W@IIZT-S262fL[Yz'

def create_connection():
    try:
        return psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
    except OperationalError as e:
        print(f"Database connection error: {e}")
        print("\nTroubleshooting steps:")
        print("1. Make sure PostgreSQL is installed")
        print("2. Start the PostgreSQL service (Windows: Services app, look for 'postgresql-*')")
        print("3. Verify the database 'brightkid' exists")
        print("4. Check that the user 'fmug' has access to the database")
        raise
