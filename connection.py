import psycopg2
DB_HOST = 'localhost'
DB_NAME = 'brightkid'
DB_USER = 'fmug'
DB_PASS = 'W@IIZT-S262fL[Yz'

def create_connection():

    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
