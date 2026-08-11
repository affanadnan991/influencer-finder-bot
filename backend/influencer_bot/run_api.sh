#!/bin/bash
echo "Starting Influencer Finder API..."
echo ""
echo "API will be available at: http://localhost:8000"
echo "Docs at: http://localhost:8000/docs"
echo ""

# Activate virtual environment if it exists and is not active
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -d "venv" ]; then
        echo "Activating virtual environment (venv)..."
        source venv/bin/activate
    elif [ -d ".venv" ]; then
        echo "Activating virtual environment (.venv)..."
        source .venv/bin/activate
    else
        echo "⚠️ Virtual environment not found or active. Running with system python/uvicorn."
    fi
fi

# Run the API server using uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
