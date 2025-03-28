#!/bin/bash
# Script to set up dev-knot environment with UV

# Check if UV is installed
if ! command -v uv &> /dev/null; then
    echo "UV is not installed. Installing UV..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Add uv to the current shell session
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Create virtual environment and install dependencies
echo "Creating virtual environment and installing dependencies..."
uv venv
source .venv/bin/activate
uv pip install -e .

# Prompt for OpenAI API key if not already set
if [ ! -f .openaiapi_key ]; then
    echo "Please enter your OpenAI API key:"
    read api_key
    echo $api_key > .openaiapi_key
    echo "API key saved to .openaiapi_key"
else
    echo "OpenAI API key already exists in .openaiapi_key"
fi

echo "Setup complete! You can now run the code with:"
echo "source .venv/bin/activate"
echo "python main.py"