#!/bin/bash

# Navigate to the client directory
cd "$(dirname "$0")"

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "Error: npm is not installed. Please install Node.js and npm first."
    exit 1
fi

echo "📦 Installing dependencies..."
npm install

# Check if installation was successful
if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to install dependencies."
    exit 1
fi

echo "✅ Setup completed successfully!"
echo ""
echo "To start the client application, run:"
echo "  cd src/client"
echo "  npm start"
echo ""
echo "Make sure the server is running on port 9000 before starting the client." 