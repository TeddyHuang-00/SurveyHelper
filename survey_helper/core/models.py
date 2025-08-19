"""Core data models shared between fetch and analyze stages."""

import json
from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class RelevanceRating(str, Enum):
    """Enum for paper relevance ratings."""

    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    UNKNOWN = "Unknown"


class Conference(str, Enum):
    """Supported ML conferences for fetching."""

    ICLR = "ICLR"
    ICML = "ICML"
    NeurIPS = "NeurIPS"


class Paper(BaseModel):
    """Model representing an academic paper with metadata."""

    title: str
    authors: list[str]
    abstract: str | None = None
    publication_year: int
    conference_name: str
    venue_type: str
    track: str | None = None
    session: str | None = None
    topic: str | None = None
    pdf_url: str | None = None
    abstract_url: str | None = None
    openreview_url: str | None = None
    scraped_at: datetime


class LLMRelevanceResponse(BaseModel):
    """Pydantic model for validating LLM relevance judgment responses."""

    relevance_rating: Literal["High", "Medium", "Low"] = Field(
        description="The relevance rating of the paper to the survey topic"
    )
    confidence_score: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0"
    )
    reasoning: str = Field(
        min_length=10,
        description="Brief explanation of the rating decision",
    )

    @field_validator("relevance_rating")
    @classmethod
    def validate_rating(cls, v):
        """Validate that rating is one of the allowed values."""
        if v not in ["High", "Medium", "Low"]:
            raise ValueError(f"Rating must be 'High', 'Medium', or 'Low', got '{v}'")
        return v

    @field_validator("reasoning")
    @classmethod
    def validate_reasoning(cls, v):
        """Ensure reasoning is meaningful."""
        if not v or len(v.strip()) < 5:
            raise ValueError("Reasoning must be at least 5 characters long")
        return v.strip()

    @model_validator(mode="after")
    def validate_consistency(self):
        """Validate consistency between rating and confidence."""
        # High ratings should generally have higher confidence
        if self.relevance_rating == "High" and self.confidence_score < 0.3:
            self.confidence_score = max(0.3, self.confidence_score)
        elif self.relevance_rating == "Low" and self.confidence_score > 0.8:
            self.confidence_score = min(0.8, self.confidence_score)
        return self

    @classmethod
    def get_json_schema_str(cls) -> str:
        """Get JSON schema as string for inclusion in LLM prompts."""
        return json.dumps(cls.model_json_schema(), indent=2)

    def to_relevance_rating_enum(self) -> RelevanceRating:
        """Convert string rating to enum."""
        mapping = {
            "High": RelevanceRating.HIGH,
            "Medium": RelevanceRating.MEDIUM,
            "Low": RelevanceRating.LOW,
            "Unknown": RelevanceRating.UNKNOWN,
        }
        return mapping[self.relevance_rating]


class PaperRelevanceResult(BaseModel):
    """Final result combining paper data with relevance judgment."""

    title: str
    authors: list[str]
    conference: str
    year: int
    relevance_rating: RelevanceRating
    confidence_score: float | None = None
    reasoning: str | None = None
    file_source: str


class ProcessingCheckpoint(BaseModel):
    """Model for saving and loading processing checkpoints."""

    survey_topic: str
    processed_files: list[str] = Field(default_factory=list)
    current_file: str | None = None
    current_batch_index: int = 0
    results: list[PaperRelevanceResult] = Field(default_factory=list)
    total_processed: int = 0
    timestamp: datetime = Field(default_factory=datetime.now)
