#!/bin/bash

# Voice Teaching Agent - Quick Start Script

echo "🎓 Voice Teaching Agent Demo"
echo "============================"
echo ""

# Check if .env exists
if [ ! -f backend/.env ]; then
    echo "⚠️  .env file not found in backend/"
    echo "   Creating from template..."
    cp backend/.env.example backend/.env
    echo "   Please edit backend/.env with your API keys"
    echo ""
fi

# Create Python virtual environment if it doesn't exist
if [ ! -d backend/venv ]; then
    echo "📦 Creating Python virtual environment..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    echo "   Installing dependencies..."
    pip install -r requirements.txt
    cd ..
else
    cd backend
    source venv/bin/activate
    cd ..
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the demo:"
echo ""
echo "Terminal 1 - Backend:"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  python -m uvicorn main:app --reload --port 8000"
echo ""
echo "Terminal 2 - Frontend:"
echo "  cd frontend"
echo "  python -m http.server 8001"
echo ""
echo "Then open: http://localhost:8001"
echo ""
