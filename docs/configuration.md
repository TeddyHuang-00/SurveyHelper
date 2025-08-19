# Configuration Guide

Advanced configuration options for power users and specific research needs. All configuration is done through command-line arguments.

## Command Line Configuration

### Survey Configuration

```bash
# Basic topic
uv run analyze.py --survey.topic "Large Language Models"

# Detailed topic with context
uv run analyze.py \
  --survey.topic "Vision Transformers" \
  --survey.description "Focus on transformer architectures applied to computer vision tasks, including ViT, DeiT, and hybrid CNN-transformer models"
```

### Processing Options

```bash
# Adjust batch size for your hardware
uv run analyze.py --survey.topic "Topic" --processing.batch 20

# Custom input/output paths
uv run analyze.py \
  --survey.topic "Topic" \
  --processing.input "my_papers/" \
  --processing.output "my_results.csv"

# Disable checkpointing (not recommended for large datasets)
uv run analyze.py --survey.topic "Topic" --no-processing.save-every-batch
```

### LLM Configuration

```bash
# Use different model
uv run analyze.py --survey.topic "Topic" --llm.model "qwen2.5:7b"

# Remote Ollama server
uv run analyze.py --survey.topic "Topic" --llm.ollama-url "http://remote-server:11434"

# Adjust retry settings for unreliable connections or less powerful LLMs
uv run analyze.py --survey.topic "Topic" --llm.max-retries 5 --llm.retry-delay 2.0
```

### Filtering Options

```bash
# Filter by years (inclusive range) - note the quotes around the brackets
uv run analyze.py --survey.topic "Topic" --filter.years '[2022,2024]'

# Filter by conferences
uv run analyze.py --survey.topic "Topic" --filter.conferences '["ICLR","ICML"]'

# Combine filters
uv run analyze.py \
  --survey.topic "Topic" \
  --filter.years '[2023,2024]' \
  --filter.conferences '["NeurIPS"]'
```

## Advanced Filtering

### Multi-Stage Filtering Workflow

```bash
# Stage 1: Broad topic analysis
uv run analyze.py --survey.topic "Machine Learning" --processing.output "broad_ml.csv"

# Stage 2: Focus on high-relevance papers from Stage 1
# (manually filter broad_ml.csv to high-relevance papers, save as high_rel_papers.json)

# Stage 3: Detailed analysis with specific subtopic
uv run analyze.py \
  --survey.topic "Graph Neural Networks for Drug Discovery" \
  --processing.input "high_rel_papers/" \
  --processing.output "focused_gnn.csv"
```

### Custom Paper Selection

```bash
# Analyze only specific paper files
uv run analyze.py \
  --survey.topic "Topic" \
  --processing.input "data/my_conference_collections/"

# Process multiple specific files
mkdir filtered_papers
cp data/papers/icml_2024_papers.json filtered_papers/
cp data/papers/neurips_2024_papers.json filtered_papers/
uv run analyze.py --survey.topic "Topic" --processing.input "filtered_papers/"
```

## Output Customization

### Multiple Output Formats

```bash
# Create filtered CSV files by relevance level
uv run analyze.py --survey.topic "Topic" --app.create-separate-csvs

# Results in:
# - relevance_index.csv (all papers)
# - relevance_index_high.csv (high relevance only)
# - relevance_index_medium.csv (medium relevance only)
# - relevance_index_low.csv (low relevance only)
# - relevance_index.summary.csv (statistics by conference/year)
```

### Custom Output Locations

```bash
# Organize by project
mkdir -p projects/vision-transformers/results
uv run analyze.py \
  --survey.topic "Vision Transformers" \
  --processing.output "projects/vision-transformers/results/vit_analysis.csv"

# Date-stamped outputs
DATE=$(date +%Y%m%d)
uv run analyze.py \
  --survey.topic "Topic" \
  --processing.output "results_${DATE}.csv"
```

## Performance Tuning

### Hardware-Specific Optimization

**For CPU-only systems:**

```bash
uv run analyze.py \
  --survey.topic "Topic" \
  --processing.batch 8 \
  --llm.model "qwen3:1.7b"
```

**For GPU systems (8GB+ VRAM):**

```bash
uv run analyze.py \
  --survey.topic "Topic" \
  --processing.batch 25 \
  --llm.model "qwen3:8b"
```

**For high-memory systems (32GB+ RAM):**

```bash
uv run analyze.py \
  --survey.topic "Topic" \
  --processing.batch 50 \
  --llm.model "qwen3:30b-a3b"
```

### Speed vs Quality Trade-offs

**Maximum speed (testing):**

```bash
uv run analyze.py \
  --survey.topic "Topic" \
  --llm.model "qwen3:1.7b" \
  --processing.batch 30 \
  --filter.years '[2024,2024]'
```

**Balanced (production):**

```bash
uv run analyze.py \
  --survey.topic "Topic" \
  --llm.model "qwen3:8b" \
  --processing.batch 15
```

**Maximum quality (research):**

```bash
uv run analyze.py \
  --survey.topic "Topic" \
  --llm.model "qwen3:30b-a3b" \
  --processing.batch 10 \
  --llm.max-retries 5
```

## Logging and Monitoring

### Debug Mode

```bash
# Verbose logging to console
uv run analyze.py --survey.topic "Topic" --logging.verbose

# Log to file for later analysis
uv run analyze.py \
  --survey.topic "Topic" \
  --logging.level DEBUG \
  --logging.file "analysis.log"
```

### Progress Monitoring

```bash
# Run in background with logging
uv run analyze.py --survey.topic "Topic" --logging.file "progress.log" &

# Monitor progress in real-time
tail -f progress.log

# Check checkpoint status
ls -la data/checkpoints/
```

## Resuming and Recovery

### Checkpoint Management

```bash
# Analysis automatically saves progress every batch
# To resume after interruption, simply re-run the same command,
# and enter 'y' when prompted:
uv run analyze.py --survey.topic "Topic"

# To force start fresh (ignore existing checkpoints):
rm -f data/checkpoints/processing_checkpoint.json
uv run analyze.py --survey.topic "Topic"
```

### Handling Errors

```bash
# If analysis fails, check logs:
uv run analyze.py --survey.topic "Topic" --logging.level DEBUG

# Common fixes:
# 1. Restart Ollama: ollama serve
# 2. Reduce batch size: --processing.batch 5
# 3. Switch to smaller model: --llm.model "qwen3:1.7b"
```

## Integration Workflows

### Academic Workflow

```bash
# 1. Initial broad survey
uv run fetch.py --conferences '["ICLR","ICML","NeurIPS"]' --start-year 2022 --end-year 2024
uv run analyze.py --survey.topic "Broad Topic" --processing.output "initial_survey.csv"

# 2. Focus on high-relevance papers
uv run analyze.py \
  --survey.topic "Specific Subtopic" \
  --filter.years '[2024,2024]' \
  --processing.output "focused_analysis.csv"

# 3. Generate summary statistics
# Open relevance_index.summary.csv for conference/year breakdown
```

### Industry Workflow

```bash
# Focus on practical applications
uv run analyze.py \
  --survey.topic "Production Machine Learning Systems" \
  --filter.conferences '["ICML"]' \
  --filter.years '[2023,2024]' \
  --app.create-separate-csvs
```

### Comparative Analysis

```bash
# Compare different research areas
uv run analyze.py --survey.topic "Computer Vision" --processing.output "cv_papers.csv"
uv run analyze.py --survey.topic "Natural Language Processing" --processing.output "nlp_papers.csv"
uv run analyze.py --survey.topic "Reinforcement Learning" --processing.output "rl_papers.csv"

# Analyze results across topics in your spreadsheet application
```
