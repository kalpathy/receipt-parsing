#!/bin/bash

# Receipt Parser App Setup Script
echo "🔧 Setting up Receipt Parser App..."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment and install packages
echo "📋 Installing Python packages..."
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Make sure your Azure credentials are in ~/.secrets:"
echo "   export AZURE_FORM_RECOGNIZER_ENDPOINT=\"your_endpoint\""
echo "   export AZURE_FORM_RECOGNIZER_KEY=\"your_key\""
echo ""
echo "2. Run the app with: ./run_app.sh"
