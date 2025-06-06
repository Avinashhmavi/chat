# TINA Chatbot

Welcome to the TINA (TIME Instant Neural Assistant) Chatbot project! This is a web-based chatbot application designed to assist users with course-related queries, such as exam details, training types, and more. The application features a registration process with OTP verification, a conversational flow, and dynamic prompts for user interaction.

This README provides detailed steps to set up and run the project locally for testing purposes.

---

## Project Structure

The repository contains the following key directories and files:

- **backend/**: Contains the Flask backend code.
  - `app.py`: Main Flask application file.
  - `chatbot_engine.py`: Core chatbot logic for managing user context and interactions.
  - `db_connect.py`: Database connection classes (`MySQLDB`, `MSSQLDB`, `DB3`).
  - `config.py`: Configuration file for database credentials.
  - `creating_db_schema.sql`: SQL script to set up the database schema (if needed).
  - `requirements.txt`: Python dependencies for the backend.
- **frontend/**: Contains the frontend code.
  - `index.html`: Main HTML file for the chatbot interface.
  - `script.js`: JavaScript file handling frontend logic and API interactions.
  - `style.css`: CSS file for styling the chatbot interface.
- **README.md**: This file.

---

## Setup Instructions

Follow these steps to set up and run the TINA Chatbot locally.

### Step 1: Clone the Repository

Clone the repository to your local machine using Git:

```bash
git clone https://github.com/your-username/tina-chatbot.git
cd tina-chatbot
```
Follow these steps to setup and run TINA

### Step 2: Setup the Backend

1. Navigate to the Backend Directory

```bash
cd backend
```

2. Create a Virtual Environment

```bash
python -m venv venv
venv/scripts/activate
```

3. Install Dependencies
```bash
pip install -r requirements.txt
```
4. Create a `.env` file outside the `backend folder` and add the Db credentials
```.env
# DB1 (Remote MySQL)
MYSQL_HOST=
MYSQL_USER=
MYSQL_PASSWORD=""
MYSQL_DATABASE=

# DB2 (Remote MSSQL)
MSSQL_SERVER=
MSSQL_DATABASE=
MSSQL_USERNAME=
MSSQL_PASSWORD=""

# DB3 (Local MySQL)
DB3_HOST=
DB3_USER=
DB3_PASSWORD=""
DB3_DATABASE=
```
5. Create DB3

Db3 is a `mySQL` database which stores the flow of the chatbot

- Run the file `creating_db_schema.sql` proceeded by `adding_data.sql`

### Step 3: Start the Chatbot
#### Run Backend:

1. Open a terminal activate our environment
```bash
cd backend
venv/scripts/activate
```
2. Start the Flask Server
```bash
python app.py
```
The flask server will run at `http://localhost:5000`.

#### Run Frontend:

<b>Now, Start a new terminal (Do not close the previous one</b>

1. Navigate to the frontend directory
```bash
cd frontend
```

2. Serve the frontend files
```bash
python -m http.server 8000
```
Access it at `http://localhost:8000`.
