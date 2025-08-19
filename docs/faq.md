# Frequently Asked Questions

## Remote and Advanced Setup

### Using Remote Ollama Server

```bash
# Point to remote Ollama instance
uv run analyze.py --llm.ollama-url "http://your-server:11434" --survey.topic "Topic"

# Or via port forwarding
ssh -L 11434:localhost:11434 user@your-server
```

### Docker Ollama Setup

```bash
# Run Ollama in Docker
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama

# Pull model
docker exec -it ollama ollama pull qwen2.5:7b
```

### GPU Configuration

Ollama automatically uses available GPUs. For multiple GPUs:

```bash
# Set specific GPU
CUDA_VISIBLE_DEVICES=0 ollama serve

# Use all GPUs
ollama serve
```

## Custom Conferences and Data

### Adding New Conferences

Currently supports ICLR, ICML, NeurIPS. To add others:

1. **Check for JSON APIs**: Look for `conference-year-papers.json` endpoints
2. **Modify configuration**: Edit `survey_helper/fetch/downloader.py`
3. **Add conference mapping**: Update `CONFERENCE_CONFIGS` dictionary

### Using Custom Paper Data

If you have papers in JSON format:

```bash
# Place JSON files in data/papers/
cp my_papers.json data/papers/

# Run analysis on all files in directory
uv run analyze.py --survey.topic "Topic" --processing.input data/papers
```

Required JSON format:

```json
[
  {
    "title": "Paper Title",
    "authors": ["Author One", "Author Two"],
    "abstract": "Paper abstract text...",
    "publication_year": 2024,
    "conference_name": "VENUE",
    "venue_type": "Conference"
  }
]
```

## Performance and Optimization

### Processing Large Datasets

For 20k+ papers:

```bash
# Use largest batch size your system can handle
uv run analyze.py --survey.topic "Topic" --processing.batch 30

# Process overnight with logging
uv run analyze.py --survey.topic "Topic" --logging.file analysis.log &

# Monitor progress
tail -f analysis.log
```

## Output and Integration

### Creating Filtered Outputs

```bash
# Create separate CSV files by relevance level
uv run analyze.py --survey.topic "Topic" --app.create-separate-csvs

# Results in:
# - relevance_index_high.csv (only high relevance papers)
# - relevance_index_medium.csv
# - relevance_index_low.csv
```

### Programmatic Usage

```python
from survey_helper.fetch import MLConferenceDownloader
from survey_helper.analyze import RelevanceJudge
from survey_helper.core import Config

# Download papers programmatically
downloader = MLConferenceDownloader(
    conferences=["ICML"],
    start_year=2024,
    end_year=2024
)
results = downloader.download_all("my_papers/")

# Analyze papers programmatically
config = Config()
config.survey.topic = "Machine Learning"
config.llm.model_name = "qwen3:1.7b"

judge = RelevanceJudge(config)
relevance_results = await judge.judge_papers(papers)
```

## Data and Privacy

### Local Processing

- **All analysis runs locally** - no data sent to external services
- **Ollama runs locally** - your research topics stay private
- **Papers downloaded directly** from conference websites

### Data Storage

- **Papers**: Stored in `data/papers/` as JSON files
- **Results**: Saved in `data/results/` as CSV files
- **Checkpoints**: Progress saved in `data/checkpoints/` for resuming

### Cleanup

```bash
# Remove downloaded papers (keep results)
rm -rf data/papers/

# Remove analysis results (keep papers)
rm -rf data/results/

# Remove checkpoints (fresh start)
rm -rf data/checkpoints/
```

## Development and Contribution

### Code Organization

```
survey_helper/
├── core/        # Shared models and config
├── fetch/       # Paper downloading
├── analyze/     # Relevance analysis
└── utils/       # Utilities
```

### Running in Development

```bash
# Format code
just format

# Lint code
just lint

# Run with development logging
uv run analyze.py --logging.level DEBUG --survey.topic "Topic"
```
