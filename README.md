# T.I.M.E. Chatbot - AI-Powered Educational Assistant

A full-stack chatbot application for T.I.M.E. (Triumphant Institute of Management Education) that provides intelligent assistance to students with course information, exam details, and general queries.

## 🚀 Features

### Dual Chat Modes
- **Flow-Based Chat**: Guided conversation with predefined categories and questions
- **RAG-Based Chat**: AI-powered chat using OpenAI GPT with database retrieval

### Key Capabilities
- Course fee and pricing information
- Exam details and eligibility criteria
- Study material and batch information
- Real-time database queries
- Modern, responsive UI
- City-based course recommendations

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **MySQL** - Database for course and exam data
- **OpenAI GPT-3.5** - AI-powered responses
- **Python 3.8+** - Core programming language

### Frontend
- **HTML/CSS/JavaScript** - Modern web interface
- **Responsive Design** - Works on all devices
- **Real-time Chat UI** - Interactive conversation interface

## 📁 Project Structure

```
TIME_chatbot/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── db_connect.py        # Database connection and queries
│   ├── rag_system.py        # RAG (Retrieval-Augmented Generation) system
│   ├── config.py            # Configuration settings
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── index.html           # Main chat interface
│   ├── styles.css           # Styling
│   └── script.js            # Frontend logic
├── sql/
│   └── database_setup.sql   # Database schema and sample data
├── .env.example             # Environment variables template
└── README.md               # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- MySQL database
- OpenAI API key

### 1. Clone the Repository
```bash
git clone https://github.com/Avinashhmavi/chat.git
cd chat
```

### 2. Backend Setup
```bash
cd backend
pip install -r requirements.txt
```

### 3. Database Setup
1. Create a MySQL database
2. Import the schema: `mysql -u username -p database_name < ../sql/database_setup.sql`

### 4. Environment Configuration
```bash
cp .env.example .env
# Edit .env with your database and OpenAI credentials
```

### 5. Start the Backend
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Open Frontend
Open `frontend/index.html` in your browser or serve it using a local server.

## 🔧 Configuration

### Environment Variables (.env)
```env
# Database Configuration
DB_HOST=localhost
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=your_database

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
```

## 💬 Usage

### Flow-Based Chat
1. Select your city
2. Choose a course (CAT, GMAT, etc.)
3. Select exam year
4. Browse through predefined categories and questions

### RAG-Based Chat
1. Toggle to "AI Chat" mode
2. Ask any question about courses, fees, or exams
3. Get AI-powered responses with database context

## 🎯 Key Features Explained

### Intelligent Fee Retrieval
- Automatically detects fee-related queries
- Retrieves exact pricing from database
- Provides both regular and offer prices
- Formats prices with ₹ symbol

### Multi-Strategy Search
- Full query search
- Keyword-based search
- Course price-specific search
- Aggregates and deduplicates results

### Context-Aware Responses
- Uses relevant database information
- Provides accurate, non-generic answers
- Graceful fallback when information is unavailable

## 🔍 API Endpoints

- `GET /` - Health check
- `POST /chat` - Flow-based chat
- `POST /rag-chat` - RAG-based AI chat
- `GET /categories` - Get all categories
- `GET /questions/{category_id}` - Get questions by category

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions, please open an issue on GitHub or contact the development team.

---

**Built with ❤️ for T.I.M.E. students**
