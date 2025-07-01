#!/bin/bash

echo "🚀 Setting up TINA Chatbot with RAG System"
echo "=========================================="

# Check if .env file exists
if [ ! -f "backend/.env" ]; then
    echo "📝 Creating .env file..."
    cat > backend/.env << EOF
# Database Configuration
MYSQL_HOST=localhost
MYSQL_USER=your_mysql_user
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=your_mysql_database

# OpenAI Configuration (Required for RAG feature)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo
EOF
    echo "✅ Created backend/.env file"
    echo "⚠️  Please edit backend/.env with your actual credentials"
else
    echo "✅ .env file already exists"
fi

# Check if virtual environment exists
if [ ! -d "backend/venv" ]; then
    echo "🐍 Creating virtual environment..."
    cd backend
    python3 -m venv venv
    echo "✅ Virtual environment created"
    cd ..
else
    echo "✅ Virtual environment already exists"
fi

# Install dependencies
echo "📦 Installing dependencies..."
cd backend
source venv/bin/activate
pip install -r requirements.txt
cd ..

echo ""
echo "🎉 Setup completed!"
echo ""
echo "Next steps:"
echo "1. Edit backend/.env with your actual database and OpenAI credentials"
echo "2. Run: cd backend && python test_rag.py (to test RAG system)"
echo "3. Run: ./start.sh (to start the chatbot)"
echo ""
echo "For OpenAI API key, visit: https://platform.openai.com/api-keys" 