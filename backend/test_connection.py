import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database.sql_executor import SQLExecutor

executor = SQLExecutor()
if executor.connect():
    print("Connection successful!")
    executor.close()
else:
    print("Connection failed!")