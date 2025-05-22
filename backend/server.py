import sys
import os
import traceback

# Add the project root directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, request, jsonify
from utils.logger import logging
from utils.exception import CustomException
from services.nlp_to_SQL import execute_nlp_to_sql
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}})

@app.route('/')
def index():
    return "Welcome to the RAG-Based SQL Query API"

@app.route('/api/nlp-to-sql', methods=['POST'])
def nlp_to_sql():
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            raise CustomException("Query is required in request body", sys.exc_info())
        
        user_query = data['query']
        logging.info(f"Received query: {user_query}")
        
        result = execute_nlp_to_sql(user_query)
        
        if "error" in result:
            logging.error(f"Error processing query: {result['error']}")
            return jsonify({"error": result["error"]}), 500
            
        logging.info("Successfully processed query")
        return jsonify(result), 200
        
    except CustomException as e:
        logging.error(str(e))
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": "An unexpected error occurred"}), 500

if __name__ == "__main__":
    logging.info("Starting Flask server")
    app.run(debug=True, port=5000)