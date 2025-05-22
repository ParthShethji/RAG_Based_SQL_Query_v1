import mysql.connector
from backend.config.dbconfig import DBConfig

class SQLExecutor:
    def __init__(self):
        self.db_config = DBConfig()
        self.connection = None
    
    def connect(self):
        """Establish connection to the database using parameters from DBConfig"""
        try:
            self.connection = mysql.connector.connect(**self.db_config.get_connection_params())
            return True
        except mysql.connector.Error as err:
            print(f"Error connecting to MySQL: {err}")
            return False
    
    def execute_query(self, query, params=None):
        """Execute a SELECT query and return results"""
        if not self.connection or not self.connection.is_connected():
            if not self.connect():
                raise ConnectionError("Failed to connect to the database")
            
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            result = cursor.fetchall()
            cursor.close()
            return result
        except mysql.connector.Error as err:
            print(f"Error executing query: {err}")
            return None
    
    def execute_update(self, query, params=None):
        """Execute an INSERT, UPDATE, or DELETE query"""
        if not self.connection or not self.connection.is_connected():
            self.connect()
            
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            self.connection.commit()
            affected_rows = cursor.rowcount
            cursor.close()
            return affected_rows
        except mysql.connector.Error as err:
            print(f"Error executing update: {err}")
            self.connection.rollback()
            return -1
    
    def close(self):
        """Close the database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()

