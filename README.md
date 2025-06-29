# TINA Chatbot

Welcome to the TINA (TIME Instant Neural Assistant) Chatbot project! This is a web-based chatbot application designed to assist users with course-related queries, such as exam details, training types, and more. The application features a registration process with OTP verification, a conversational flow, and dynamic prompts for user interaction.

**NEW: AI-Powered RAG Chatbot Feature**
The chatbot now includes an AI-powered RAG (Retrieval-Augmented Generation) system that can answer natural language questions using OpenAI's GPT models. Users can toggle between the traditional flow-based chat and the new AI chat mode.

This README provides detailed steps to set up and run the project locally for testing purposes.

---

## Project Structure

The repository contains the following key directories and files:

- **backend/**: Contains the backend code.
  - `app.py`: Main application file with both flow-based and RAG-based chat endpoints.
  - `chatbot_engine.py`: Core chatbot logic for managing user context and interactions.
  - `rag_system.py`: NEW - RAG system for AI-powered responses using OpenAI.
  - `db_connect.py`: Database connection classes (`MySQLDB`) with search methods for RAG.
  - `config.py`: Configuration file for database and OpenAI credentials.
  - `requirements.txt`: Python dependencies for the backend.
- **sql_scripts_db3/**: Contains SQL scripts for chatbot tables
  - `creating_db_schema.sql`: SQL script to set up the database schema.
  - `adding_data.sql`: SQL script to add data in the tables
  - `delete_chatbot_tables.sql`: SQL script to remove tables in case any changes are made.
- **frontend/**: Contains the frontend code.
  - `index.html`: Main HTML file for the chatbot interface with chat mode toggle.
  - `script.js`: JavaScript file handling frontend logic, API interactions, and chat mode switching.
  - `style.css`: CSS file for styling the chatbot interface including mode toggle styles.
- **README.md**: This file.
- **start.sh**
---

## Features

### Traditional Flow-Based Chat
- User registration with OTP verification
- Step-by-step course selection process
- City-based course filtering
- Dynamic option buttons
- Context-aware responses

### NEW: AI-Powered RAG Chat
- Natural language question answering
- Retrieval from database knowledge base
- OpenAI GPT integration
- Context-aware responses using user's selected course/city
- Seamless switching between chat modes

---

## Setup Instructions

Follow these steps to set up and run the TINA Chatbot locally.

### Step 1: Clone the Repository

Clone the repository to your local machine using Git:

```bash
git clone https://github.com/your-username/TIME_chatbot.git
cd TIME_chatbot
```

### Step 2: Environment Configuration

Create a `.env` file in the `backend/` directory with the following variables:

```env
# Database Configuration
MYSQL_HOST=your_mysql_host
MYSQL_USER=your_mysql_user
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=your_mysql_database

# OpenAI Configuration (Required for RAG feature)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo
```

**Note:** You need a valid OpenAI API key to use the RAG feature. Get one from [OpenAI's platform](https://platform.openai.com/api-keys).

### Step 3: Setup the Backend

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

### Step 4: Make the scripts executable:
```bash
chmod +x start.sh
```

### Step 5: Start the Chatbot
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

---

## Usage

### Flow-Based Chat
1. Click the chatbot button to open the interface
2. Register with your name and mobile number
3. Verify OTP
4. Follow the step-by-step process to select city, course, and exam year
5. Get specific information about your selected course

### AI-Powered RAG Chat
1. Click the "Flow Chat" button in the header to switch to "AI Chat" mode
2. Ask natural language questions like:
   - "What are the eligibility criteria for CAT?"
   - "Tell me about MBA advantages"
   - "What are the exam dates for GMAT?"
   - "How much does the classroom course cost?"
3. Get AI-generated responses based on the database knowledge base

### Switching Between Modes
- Use the toggle button in the chatbot header to switch between Flow Chat and AI Chat
- Each mode maintains its own conversation context
- Switching modes will clear the current conversation

---

## API Endpoints

### Flow-Based Chat
- `POST /register` - User registration
- `POST /verify-otp` - OTP verification
- `POST /chat` - Flow-based chat responses

### NEW: RAG-Based Chat
- `POST /rag-chat` - AI-powered chat responses using OpenAI

### Database APIs
- Various GET endpoints for course data, cities, categories, etc.

---

## Technical Details

### RAG System Architecture
1. **Query Processing**: User questions are processed and analyzed
2. **Context Retrieval**: Relevant information is retrieved from the database using semantic search
3. **Response Generation**: OpenAI GPT generates contextual responses using retrieved information
4. **User Context Integration**: User's selected course/city information is included in responses

### Database Search Methods
- `search_categories_and_questions()` - Searches Q&A database
- `search_exam_info()` - Searches exam information
- `search_static_answers()` - Searches static answer database

---

## Troubleshooting

### Common Issues
1. **OpenAI API Error**: Ensure your API key is valid and has sufficient credits
2. **Database Connection**: Check your MySQL credentials in the `.env` file
3. **Dependencies**: Make sure all requirements are installed correctly

### Logs
Check the console logs for detailed error messages and debugging information.
# TINA Chatbot - AI-Powered Educational Assistant
