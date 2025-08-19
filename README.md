# SurveyHelper

**Automatically find relevant research papers for your literature reviews using AI.**

SurveyHelper downloads thousands of papers from top ML conferences (ICLR, ICML, NeurIPS) and uses large language models to evaluate their relevance to your research topic.

## Quick Start

```bash
# Install
git clone <repository-url> && cd SurveyHelper && uv sync

# 1. Download papers
uv run fetch.py --start-year 2020

# 2. Find relevant papers
uv run analyze.py --survey.topic "Large Language Models"

# 3. Open results.csv - papers ranked by relevance with AI explanations
```

## What You Get

- **24k+ papers** from ICLR, ICML, NeurIPS (2020-2025)
- **AI relevance scoring** with confidence levels and explanations
- **CSV output** ready for Excel/Google Sheets analysis
- **Automatic checkpointing** - resume interrupted analysis

## Core Commands

```bash
# Download papers from specific conferences and years
uv run fetch.py --conferences '["ICML", "ICLR"]' --start-year 2023 --end-year 2024

# Analyze papers for your research topic
uv run analyze.py --survey.topic "Computer Vision Transformers"

# Filter by conference and years during analysis
uv run analyze.py --survey.topic "NLP" --filter.conferences '["ICLR"]' --filter.years '[2023, 2024]'

# Get help
uv run fetch.py --help
uv run analyze.py --help
```

## Output

Results saved as `data/results/relevance_index.csv`:

| Title                       | Conference | Year | Relevance | Confidence | Reasoning                                              |
| --------------------------- | ---------- | ---- | --------- | ---------- | ------------------------------------------------------ |
| "Attention Is All You Need" | NeurIPS    | 2017 | High      | 0.95       | Foundational transformer paper directly relevant to... |

## Requirements

- **[uv](https://docs.astral.sh/uv/)** (handles Python 3.8+ automatically)
- **[Ollama](https://ollama.ai/)** running locally with a language model

## Documentation

- **[Getting Started Guide](docs/getting_started.md)** - Complete setup walkthrough
- **[FAQ](docs/faq.md)** - Remote Ollama, custom conferences, troubleshooting
- **[Configuration](docs/configuration.md)** - Advanced filtering and processing options

## Why SurveyHelper?

- **Save weeks of manual paper screening** - Process thousands of papers in hours
- **Consistent evaluation criteria** - AI provides uniform relevance assessment
- **Never miss important papers** - Comprehensive conference coverage
- **Focus on what matters** - Spend time reading, not searching

---

_Built for researchers who want to focus on insights, not data collection._
