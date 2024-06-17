import psycopg2
from psycopg2 import pool
import os

checkout_db_host= os.getenv("CHECKOUT_DB_HOST")
checkout_db_name=  os.getenv("CHECKOUT_DB_NAME")
checkout_db_user= os.getenv("CHECKOUT_DB_HOST")
checkout_db_password= os.getenv("CHECKOUT_DB_PASSWORD")

# Create a connection pool
connection_pool = psycopg2.pool.SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    host=checkout_db_host,
    port='5432',
    database=checkout_db_name,
    user=checkout_db_user,
    password=checkout_db_password
)


def db_write_last_synced_block(last_synced_block):
    position = last_synced_block
    query = """
    UPDATE checkpoints."checkpoint"
    SET position = %s
    WHERE "chain" = 'ethereum';
    """
    try:
        connection = connection_pool.getconn() 
        cursor = connection.cursor() 
        cursor.execute(query, (position,)) 
        connection.commit() 

    except (psycopg2.Error, Exception) as error:
        print(f"Error occurred: {error}")

    finally:
        if cursor:
            cursor.close() 
        if connection:
            connection_pool.putconn(connection)  


def db_read_last_synced_block():
     
     query = """
    SELECT position FROM checkpoints."checkpoint" WHERE "chain" = 'ethereum'
    """
     try:
        connection = connection_pool.getconn()  
        cursor = connection.cursor()  
        cursor.execute(query)  
        result = cursor.fetchone() 
        return result[0] if result else None

     except (psycopg2.Error, Exception) as error:
        print(f"Error occurred: {error}")

     finally:
        if cursor:
            cursor.close()  
        if connection:
            connection_pool.putconn(connection) 
 