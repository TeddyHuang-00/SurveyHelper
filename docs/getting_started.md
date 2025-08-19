# Getting Started Guide

Complete walkthrough to set up and use SurveyHelper for your research.

## Prerequisites

### 1. Install uv (includes Python management)

```bash
# Install uv (handles Python versions automatically)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or on macOS with Homebrew
brew install uv

# Verify installation
uv --version
```

### 2. Install Ollama

Download and install from [ollama.ai](https://ollama.ai/)

### 3. Install a Language Model

```bash
# Install recommended model (5.2GB)
ollama pull qwen3:8b

# OR for faster processing with more VRAM (19GB)
ollama pull qwen3:30b-a3b

# Verify installation
ollama list
```

## Installation

### Clone and Setup

```bash
git clone <repository-url>
cd SurveyHelper
uv sync
```

### Verify Installation

```bash
# Test fetch functionality
uv run fetch.py --help

# Test analysis functionality
uv run analyze.py --help
```

## Your First Analysis

### Step 1: Download Papers

Start with a small dataset to test the system:

```bash
# Download recent ICML papers (this will fetch ~2800 papers)
uv run fetch.py --conferences '["ICML"]' --start-year 2024 --end-year 2024

# Check what was downloaded
ls data/papers/
```

### Step 2: Analyze for Relevance

```bash
# Analyze papers for your research topic
uv run analyze.py --survey.topic "Large Language Models"

# This will:
# - Process papers in batches of 10
# - Save progress automatically (safe to interrupt)
# - Show relevance ratings in real-time
```

### Step 3: Review Results

```bash
# Open the results in your preferred spreadsheet app
open data/results/relevance_index.csv

# Or view summary statistics
open data/results/relevance_index.summary.csv
```

## Understanding the Output

Your CSV file contains:

- **title**: Paper title
- **authors**: Paper authors (semicolon separated)
- **conference**: Source conference
- **year**: Publication year
- **relevance_rating**: High/Medium/Low relevance to your topic
- **confidence_score**: AI confidence (0.0-1.0)
- **reasoning**: Explanation for the relevance rating
- **file_source**: Source JSON file

## Scaling Up

Once you're comfortable with the basic workflow:

### Download More Conferences

```bash
# Download all conferences for recent years
uv run fetch.py --conferences '["ICLR", "ICML", "NeurIPS"]' --start-year 2022 --end-year 2024
```

### Use Advanced Filtering

```bash
# Only analyze recent papers
uv run analyze.py --survey.topic "Computer Vision" --filter.years '[2023,2024]'

# Focus on specific conferences
uv run analyze.py --survey.topic "NLP" --filter.conferences '["ICLR", "NeurIPS"]'
```

## Performance Tips

### For Large Datasets (10k+ papers):

- Use larger batch sizes: `--processing.batch 20`
- Process overnight - analysis takes time
- Enable progress saving (default): checkpoints every batch

### For Faster Testing:

- Use smaller models: `--llm.model qwen3:1.7b`
- Test with recent years only: `--filter.years '[2024,2024]'`
- Use dry run first: `--app.dry-run`

## Troubleshooting

### "Connection refused" errors:

```bash
# Start Ollama service
ollama serve

# Verify it's running
curl http://localhost:11434/api/tags
```

### "Model not found" errors:

```bash
# List available models
ollama list

# Pull required model
ollama pull [model]
```

### Memory issues:

```bash
# Reduce batch size
uv run analyze.py --survey.topic "Topic" --processing.batch 5

# Use smaller model
uv run analyze.py --survey.topic "Topic" --llm.model qwen3:1.7b
```

## Next Steps

- **[Configuration Guide](configuration.md)** - Advanced options and customization
- **[FAQ](faq.md)** - Remote setup, custom conferences
