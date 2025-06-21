# TINA Chatbot

Welcome to the TINA (TIME Instant Neural Assistant) Chatbot project! This is a web-based chatbot application designed to assist users with course-related queries, such as exam details, training types, and more. The application features a registration process with OTP verification, a conversational flow, and dynamic prompts for user interaction.

This README provides detailed steps to set up and run the project locally for testing purposes.

---

## Project Structure

The repository contains the following key directories and files:

- **backend/**: Contains the backend code.
  - `app.py`: Main application file.
  - `chatbot_engine.py`: Core chatbot logic for managing user context and interactions.
  - `db_connect.py`: Database connection classes (`MySQLDB`).
  - `config.py`: Configuration file for database credentials.
  - `requirements.txt`: Python dependencies for the backend.
- **sql_scripts_db3/**: Contains SQL scripts for chatbot tables
  - `creating_db_schema.sql`: SQL script to set up the database schema.
  - `adding_data.sql`: SQL script to add data in the tables
  - `delete_chatbot_tables.sql`: SQL script to remove tables in case any changes are made.
- **frontend/**: Contains the frontend code.
  - `index.html`: Main HTML file for the chatbot interface.
  - `script.js`: JavaScript file handling frontend logic and API interactions.
  - `style.css`: CSS file for styling the chatbot interface.
- **README.md**: This file.
- **start.sh**
---

## Setup Instructions

Follow these steps to set up and run the TINA Chatbot locally.

### Step 1: Clone the Repository

Clone the repository to your local machine using Git:

```bash
git clone https://github.com/your-username/TIME_chatbot.git
cd TIME_chatbot
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

### Step 3: Make the scripts executable:
```bash
chmod +x start.sh
```

### Step 4: Start the Chatbot
#### FOR WINDOWS (use gitbash terminal)
- Execute startup script
```bash
./start.sh
```

#### For other OS (Linux etc)
- Edit the code of start.sh file for environment activation `source venv/bin/activate`
```bash
./start.sh
```
Access the chatbot at `http://localhost:5000`.
