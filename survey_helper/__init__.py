"""
SurveyHelper - Academic Paper Relevance Analysis Tool

A two-stage system for downloading and analyzing academic papers:
1. Fetch papers from ML conferences (ICLR, ICML, NeurIPS)
2. Analyze papers for relevance to research topics using LLMs
"""

__version__ = "0.2.0"
__author__ = "SurveyHelper Team"

from .core.config import Config
from .core.models import Paper, PaperRelevanceResult, RelevanceRating

__all__ = ["Config", "Paper", "PaperRelevanceResult", "RelevanceRating"]
