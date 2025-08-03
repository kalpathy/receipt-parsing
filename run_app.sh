#!/bin/bash

# Receipt Parser App Launcher
echo "🚀 Starting Receipt Parser App..."

# Load Azure credentials
if [ -f ~/.secrets ]; then
    echo "📋 Loading Azure credentials..."
    source ~/.secrets
else
    echo "⚠️  Warning: ~/.secrets file not found"
    echo "   Make sure your Azure credentials are set as environment variables"
fi

# Check if credentials are loaded
if [ -z "$AZURE_FORM_RECOGNIZER_ENDPOINT" ] || [ -z "$AZURE_FORM_RECOGNIZER_KEY" ]; then
    echo "❌ Error: Azure credentials not found"
    echo "   Please make sure ~/.secrets contains:"
    echo "   export AZURE_FORM_RECOGNIZER_ENDPOINT=\"your_endpoint\""
    echo "   export AZURE_FORM_RECOGNIZER_KEY=\"your_key\""
    exit 1
fi

# Navigate to app directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Error: Virtual environment not found"
    echo "   Please run the setup first or create a virtual environment"
    exit 1
fi

# Start the app
echo "🌐 Starting Streamlit app..."
echo "   App will be available at: http://localhost:8501"
echo "   Press Ctrl+C to stop the app"
echo ""

.venv/bin/streamlit run receipt_app.py
