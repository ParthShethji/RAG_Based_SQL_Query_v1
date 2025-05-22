import json
import sys
import os

# Add the project root directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from database.sql_executor import SQLExecutor

# Initialize SQL executor without explicit config
executor = SQLExecutor()

# Define the table name you want to extract
table_name = "loan"

# Fetch column info from MySQL
columns = executor.execute_query(f"SHOW FULL COLUMNS FROM `{table_name}`;")

# Create `table_registry.json`
table_registry = [{
    "table_name": table_name,
    "description": "Table containing loan details, payment history, and associated metadata"
}]

# Create `column_registry.json`
column_registry = []
for col in columns:
    column_registry.append({
        "table_name": table_name,
        "column_name": col['Field'],
        "type": col['Type'],
        "nullable": col['Null'] == "YES",
        "description": col['Comment'] if col['Comment'] else "TODO: Add description"
    })

# Optional: Create `relational_mapping.json` (empty if no foreign keys)
relations = executor.execute_query(f"""
    SELECT column_name, referenced_table_name, referenced_column_name
    FROM information_schema.key_column_usage
    WHERE table_name = '{table_name}'
      AND table_schema = DATABASE()
      AND referenced_table_name IS NOT NULL;
""")

related_tables = list({rel['referenced_table_name'] for rel in relations})

relational_mapping = {
    table_name: {
        "related_tables": related_tables,
        "relationships": [{
            "local_column": rel['column_name'],
            "related_table": rel['referenced_table_name'],
            "related_column": rel['referenced_column_name']
        } for rel in relations]
    }
}

# Get the backend directory path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Save to files in the backend directory
with open(os.path.join(backend_dir, "table_registry.json"), "w") as f:
    json.dump(table_registry, f, indent=4)

with open(os.path.join(backend_dir, "column_registry.json"), "w") as f:
    json.dump(column_registry, f, indent=4)

with open(os.path.join(backend_dir, "relational_mapping.json"), "w") as f:
    json.dump(relational_mapping, f, indent=4)

print("Registry files have been generated successfully!")
print(f"Files saved in: {backend_dir}")

# Close connection
executor.close()
