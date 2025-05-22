

##  Backend Setup

### 1. Navigate to the Backend Directory
```bash
cd backend
````

### 2. Configure the SQL Database

* Open the `config` folder.
* Add your SQL database connection details (host, port, user, password, database name).

### 3. Add Gemini API Key
* Go to `backend/services`.
* Create a `.env` file and add your Gemini API key:

### 4. Create and Activate a Virtual Environment

    python -m venv venv

### 5. Install Dependencies

    pip install -r requirements.txt


### 6. Generate Schema JSON from the Database

    python services/schema_to_json.py

### 7. Start the Backend Server

    python server.py

---

##  Frontend Setup

### 1. Navigate to the Frontend Directory

    cd frontend


### 2. Install Dependencies

    npm install


### 3. Start the Development Server

    npm run dev




now go to http://localhost:5173/ 

