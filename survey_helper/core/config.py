"""Unified configuration for both fetch and analyze stages."""

from datetime import datetime
from pathlib import Path

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .models import Conference

CURRENT_YEAR = datetime.now().year


class FetchConfig(BaseSettings):
    """Configuration for paper fetching stage."""

    conferences: list[Conference] = Field(
        validation_alias=AliasChoices("conferences", "c"),
        default_factory=lambda: [Conference.ICLR, Conference.ICML, Conference.NeurIPS],
        description="List of conferences to download",
    )
    start_year: int = Field(
        validation_alias=AliasChoices("start_year", "s"),
        default=CURRENT_YEAR - 5,
        description="Starting year for downloads",
    )
    end_year: int = Field(
        validation_alias=AliasChoices("end_year", "e"),
        default=CURRENT_YEAR,
        description="Ending year for downloads",
    )
    output_dir: str = Field(
        validation_alias=AliasChoices("output_dir", "o"),
        default="data/papers",
        description="Output directory for downloaded papers",
    )

    @field_validator("conferences")
    @classmethod
    def validate_conferences(cls, v):
        """Validate that all conferences are supported."""
        valid_conferences = set(Conference)
        for conf in v:
            if conf not in valid_conferences:
                raise ValueError(f"Unsupported conference: {conf}")
        return v

    @field_validator("end_year")
    @classmethod
    def validate_year_range(cls, v, info):
        """Validate that end_year >= start_year."""
        if info.data.get("start_year") and v < info.data["start_year"]:
            raise ValueError("end_year must be >= start_year")
        return v

    model_config = SettingsConfigDict(
        cli_parse_args=True,
        cli_kebab_case=True,
        case_sensitive=False,
        # Enable help generation
        cli_hide_none_type=True,
        cli_use_class_docs_for_groups=True,
    )


class LLMConfig(BaseSettings):
    """Configuration for LLM-based relevance analysis."""

    # Ollama API settings
    ollama_url: str = Field(
        default="http://localhost:11434",
        description="Ollama base URL",
    )
    model_name: str = Field(
        validation_alias=AliasChoices("model"),
        default="hf.co/unsloth/Qwen3-30B-A3B-GGUF:latest",
        description="Model name",
    )
    max_retries: int = Field(
        default=3, description="Maximum retries for failed responses"
    )
    retry_delay: float = Field(
        default=1.0, description="Delay between retries in seconds"
    )


class SurveyConfig(BaseSettings):
    """Configuration for survey topic and scope."""

    topic: str = Field(
        default="",
        description="Survey topic for relevance judging",
    )
    description: str = Field(
        default="",
        description="Detailed description of survey scope",
    )
    keywords: list[str] = Field(
        default_factory=list,
        description="Key terms and concepts",
    )


class ProcessingConfig(BaseSettings):
    """Configuration for paper analysis processing."""

    input_dir: str = Field(
        validation_alias=AliasChoices("input"),
        default="data/papers",
        description="Directory containing paper JSON files",
    )
    output_file: str = Field(
        validation_alias=AliasChoices("output"),
        default="data/results/relevance_index.csv",
        description="Output CSV file",
    )
    batch_size: int = Field(
        validation_alias=AliasChoices("batch"),
        default=10,
        description="Batch size for processing papers",
    )
    checkpoint_file: str = Field(
        validation_alias=AliasChoices("checkpoint"),
        default="data/checkpoints/processing_checkpoint.json",
        description="File to save intermediate results for resuming",
    )
    save_every_batch: bool = Field(
        default=True,
        description="Save intermediate results after every batch",
    )


class LoggingConfig(BaseSettings):
    """Configuration for logging."""

    log_level: str = Field(
        validation_alias=AliasChoices("level"),
        default="INFO",
        description="Set logging level",
    )
    log_file: Path | None = Field(
        validation_alias=AliasChoices("file"),
        default=None,
        description="Log to file (in addition to console)",
    )
    verbose: bool = Field(
        default=False,
        description="Enable verbose logging (equivalent to --log-level DEBUG)",
    )


class FilterConfig(BaseSettings):
    """Configuration for filtering papers during analysis."""

    years: tuple[int, int] | None = Field(
        default=None,
        description="Filter papers by year range (e.g., [2020,2023])",
    )
    conferences: list[str] | None = Field(
        default=None,
        description="Filter papers by conferences (e.g., ['ICML','NeurIPS'])",
    )

    @field_validator("years")
    @classmethod
    def validate_years(cls, v):
        """Validate that the year range is valid."""
        if v and (v[0] > v[1]):
            raise ValueError("Invalid year range: start year is greater than end year.")
        return v


class AppConfig(BaseSettings):
    """General application configuration."""

    dry_run: bool = Field(
        default=False,
        description="Show summary without processing",
    )
    create_separate_csvs: bool = Field(
        default=False,
        description="Create separate CSV files for each relevance level",
    )


class Config(BaseSettings):
    """Unified configuration for the entire SurveyHelper system."""

    # Core configs
    survey: SurveyConfig = Field(default_factory=SurveyConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    filter: FilterConfig = Field(default_factory=FilterConfig)
    app: AppConfig = Field(default_factory=AppConfig)

    model_config = SettingsConfigDict(
        cli_parse_args=True,
        cli_kebab_case=True,
        case_sensitive=False,
        cli_hide_none_type=True,
        cli_use_class_docs_for_groups=True,
        cli_avoid_json=True,
        cli_implicit_flags=True,  # Allow implicit flags for boolean fields
    )
