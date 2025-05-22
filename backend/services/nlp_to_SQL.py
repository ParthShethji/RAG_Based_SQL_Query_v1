import os
import json
import sys
import traceback
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

# Add the project root directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from database.sql_executor import SQLExecutor
from utils.logger import logging
from utils.exception import CustomException

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    logging.error("GOOGLE_API_KEY environment variable is not set")
    raise CustomException("GOOGLE_API_KEY environment variable is not set", sys.exc_info())

# Initialize SQL executor
executor = SQLExecutor()

# Get the services directory path
services_dir = os.path.dirname(os.path.abspath(__file__))

# Load registries
try:
    logging.info("Loading registry files...")
    with open(os.path.join(services_dir, "table_registry.json")) as f:
        table_registry = json.load(f)

    with open(os.path.join(services_dir, "column_registry.json")) as f:
        column_registry = json.load(f)

    with open(os.path.join(services_dir, "relational_mapping.json")) as f:
        relational_mapping = json.load(f)
    logging.info("Registry files loaded successfully")
except FileNotFoundError as e:
    logging.error(f"Registry file not found: {e}")
    raise CustomException(f"Registry file not found: {e}", sys.exc_info())
except json.JSONDecodeError as e:
    logging.error(f"Invalid JSON in registry file: {e}")
    raise CustomException(f"Invalid JSON in registry file: {e}", sys.exc_info())

# Embedding + Vectorstore
try:
    logging.info("Initializing AI components...")
    embedding = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GOOGLE_API_KEY)

    table_vecstore = Chroma.from_texts(
        texts=[f"{t['table_name']}: {t['description']}" for t in table_registry],
        embedding=embedding,
        collection_name="table_registry"
    )

    column_vecstore = Chroma.from_texts(
        texts=[f"{c['table_name']}.{c['column_name']}" for c in column_registry],
        embedding=embedding,
        collection_name="column_registry"
    )

    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GOOGLE_API_KEY)
    logging.info("AI components initialized successfully")
except Exception as e:
    logging.error(f"Error initializing AI components: {e}")
    raise CustomException(f"Error initializing AI components: {e}", sys.exc_info())

# RAG Logic
def get_top_tables(query, k=3):
    """Get top k tables relevant to the query"""
    try:
        docs = table_vecstore.similarity_search(query, k=k)
        return [doc.page_content.split(":")[0] for doc in docs]
    except Exception as e:
        logging.error(f"Error in get_top_tables: {e}")
        raise CustomException(f"Error finding relevant tables: {e}", sys.exc_info())

def get_top_columns(query, tables, k=5):
    """Get top k*len(tables) columns relevant to the query and tables"""
    try:
        docs = column_vecstore.similarity_search(query, k=k * len(tables))
        return [doc.page_content for doc in docs if any(t in doc.page_content for t in tables)]
    except Exception as e:
        logging.error(f"Error in get_top_columns: {e}")
        raise CustomException(f"Error finding relevant columns: {e}", sys.exc_info())

def expand_tables(tables):
    """Expand table list with related tables from relational mapping"""
    try:
        expanded = set(tables)
        for t in tables:
            if t in relational_mapping:
                expanded.update(relational_mapping[t].get("related_tables", []))
        return list(expanded)
    except Exception as e:
        logging.error(f"Error in expand_tables: {e}")
        raise CustomException(f"Error expanding table relationships: {e}", sys.exc_info())

def construct_context(tables, columns):
    """Construct context information for the LLM prompt"""
    try:
        context = "### Tables:\n"
        for t in table_registry:
            if t["table_name"] in tables:
                context += f"{t['table_name']}: {t['description']}\n"
        
        context += "\n### Columns:\n"
        for c in column_registry:
            if c["table_name"] in tables and f"{c['table_name']}.{c['column_name']}" in columns:
                context += f"{c['table_name']}.{c['column_name']} ({c['type']}): {c['description']}\n"
        
        context += "\n### Relationships:\n"
        for t in tables:
            if t in relational_mapping:
                relations = relational_mapping[t].get("relationships", [])
                for relation in relations:
                    if relation["related_table"] in tables:
                        context += f"{t}.{relation['local_column']} -> {relation['related_table']}.{relation['related_column']}\n"
        
        return context
    except Exception as e:
        logging.error(f"Error in construct_context: {e}")
        raise CustomException(f"Error constructing context: {e}", sys.exc_info())

def generate_sql(query):
    """Generate SQL from natural language query using RAG approach"""
    try:
        logging.info(f"Generating SQL for query: {query}")
        top_tables = get_top_tables(query)
        related_tables = expand_tables(top_tables)
        top_columns = get_top_columns(query, related_tables)

        context = construct_context(related_tables, top_columns)

        prompt = f"""You are a SQL expert. Given the table context below and a natural language question, write a MySQL-compatible SQL query.

{context}

User Question: {query}

Return ONLY the SQL query without any explanation or comments:"""

        messages = [HumanMessage(content=prompt)]
        response = llm.invoke(messages).content
        
        # Clean up the response to extract just the SQL
        sql = response.strip()
        if sql.lower().startswith("```sql"):
            sql = sql[7:]
        if sql.lower().endswith("```"):
            sql = sql[:-3]
        
        logging.info(f"Generated SQL: {sql}")
        return sql.strip()
    except Exception as e:
        logging.error(f"Error in generate_sql: {e}")
        raise CustomException(f"Error generating SQL: {e}", sys.exc_info())

def execute_sql(sql_query):
    """Execute SQL query and return results"""
    try:
        logging.info(f"Executing SQL query: {sql_query}")
        results = executor.execute_query(sql_query)
        if results is None:
            logging.error("SQL query execution returned None")
            raise CustomException("Failed to execute SQL query", sys.exc_info())
        logging.info("SQL query executed successfully")
        return results if results else []
    except Exception as e:
        logging.error(f"Error in execute_sql: {e}")
        raise CustomException(f"Error executing SQL query: {e}", sys.exc_info())

def execute_nlp_to_sql(user_query):
    """Generate SQL from natural language, execute it, and explain the results"""
    try:
        logging.info(f"Processing NLP to SQL request: {user_query}")
        
        # Generate SQL from natural language
        sql = generate_sql(user_query)
        
        # Execute the SQL query
        result = execute_sql(sql)
        
        # Generate explanation using the LLM
        explanation_prompt = f"""
        The SQL query is: {sql}
        The result of the query is: {result}
        
        Please provide a summary explanation of the results in 2 lines.
        The user query is: {user_query}
        do not provide any other text like query, result, user query, etc.
        """
        
        logging.info("Generating explanation for results")
        explanation = llm.invoke([HumanMessage(content=explanation_prompt)]).content
        logging.info("Successfully generated explanation")
        
        return {
            "explanation": explanation
        }
    except CustomException as e:
        logging.error(f"Custom exception in execute_nlp_to_sql: {str(e)}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        return {"error": str(e)}
    except Exception as e:
        logging.error(f"Unexpected error in execute_nlp_to_sql: {str(e)}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        return {"error": str(e)}

# MAIN
# if __name__ == "__main__":
#     try:
#         print("NLP to SQL Converter")
#         print("--------------------")
#         user_query = input("Enter your question: ")
        
#         response = execute_nlp_to_sql(user_query)
        
#         if "error" in response:
#             print(f"\nError: {response['error']}")
#         else:
#             # print("\nGenerated SQL:")
#             # print(response["sql"])
            
#             # print("\nExecution Result:")
#             # print(response["result"])
            
#             print("\nExplanation:")
#             print(response["explanation"])
            
#     except KeyboardInterrupt:
#         print("\nOperation cancelled by user")
#     except Exception as e:
#         print(f"\nAn error occurred: {e}")
#     finally:
#         # Clean up resources
#         executor.close()
#         print("\nConnection closed")
