"""Core functionality shared between fetching and analysis stages."""

from .config import Config
from .logging_config import setup_logging
from .models import Paper, PaperRelevanceResult, RelevanceRating

__all__ = [
    "Config",
    "Paper",
    "PaperRelevanceResult",
    "RelevanceRating",
    "setup_logging",
]
