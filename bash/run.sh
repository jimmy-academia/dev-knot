
#!/bin/bash
# Script to run dev-knot with UV

# Ensure virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Run the main script with parameters passed to this script
uv run python main.py "$@"