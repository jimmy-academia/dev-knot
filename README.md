# dev kNoT

A tool for the Knowledgeable Network of Thought (kNoT) framework for reasoning with Large Language Models.

## Installation

This project uses [UV](https://github.com/astral-sh/uv) for Python package management. You can set up the project using our setup script:

```bash
# Make the setup script executable
chmod +x setup.sh

# Run the setup script
./setup.sh
```

This will:
1. Install UV if not already installed
2. Create a virtual environment
3. Install all dependencies
4. Prompt for your OpenAI API key if not already configured

## Usage

After installation, you can run the project using our run script:

```bash
# Make the run script executable
chmod +x run.sh

# Run with default parameters
./run.sh

# Or run with custom parameters
./run.sh --task gsm_symbolic --scheme knot --worker_llm gpt-4o
```

### Using the Makefile

For convenience, a Makefile is provided with common operations:

```bash
# Set up the environment
make setup

# Run with default parameters
make run

# Run with custom parameters
make run ARGS="--task gsm_symbolic --scheme knot"

# Clean up temporary files
make clean
```

### Manual Execution

Alternatively, you can run manually:

```bash
# Activate the virtual environment
source .venv/bin/activate

# Run the main script
python main.py
```

## Parameters

- `--scheme`: The reasoning scheme to use (knot, cot, zerocot)
- `--task`: The task to solve (addition, gsm_symbolic, game24)
- `--worker_llm`: The LLM to use as worker (default: gpt-4o)
- `--planner_llm`: The LLM to use as planner (default: gpt-4o)
- `--verbose`: Verbosity level (0, 1, 2)

## Experiment Log

> insert new experiment log from the top

### 2024-12-21
- GSM works tested 1
- todo: store intermediate prompt in cache; store result; scalability test; 
- TODO: Llama! paperwriting!!

### 2024-12-17
- init code
- 1. work on reproducing addition 2. work on gsm symbolic!