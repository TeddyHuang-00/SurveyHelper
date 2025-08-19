import json
import logging
from pathlib import Path

from ..core.models import ProcessingCheckpoint


class CheckpointManager:
    """Manages saving and loading processing checkpoints for resuming interrupted runs"""

    def __init__(self, checkpoint_file: str = "processing_checkpoint.json"):
        self.checkpoint_file = Path(checkpoint_file)
        self.logger = logging.getLogger(f"paper_relevance.{self.__class__.__name__}")

    def save_checkpoint(self, checkpoint: ProcessingCheckpoint) -> None:
        """Save the current processing state to a checkpoint file"""
        try:
            with open(self.checkpoint_file, "w", encoding="utf-8") as f:
                json.dump(checkpoint.model_dump(), f, indent=2, default=str)
            self.logger.debug(f"Checkpoint saved to {self.checkpoint_file}")
        except Exception as e:
            self.logger.error(f"Failed to save checkpoint: {e}")

    def load_checkpoint(self) -> ProcessingCheckpoint | None:
        """Load processing state from checkpoint file if it exists"""
        if not self.checkpoint_file.exists():
            self.logger.debug("No checkpoint file found")
            return None

        try:
            with open(self.checkpoint_file, encoding="utf-8") as f:
                data = json.load(f)
            checkpoint = ProcessingCheckpoint.model_validate(data)
            self.logger.info(f"Loaded checkpoint from {self.checkpoint_file}")
            self.logger.info(
                f"Previous run: {len(checkpoint.results)} papers processed"
            )
            return checkpoint
        except Exception as e:
            self.logger.error(f"Failed to load checkpoint: {e}")
            return None

    def clear_checkpoint(self) -> None:
        """Remove the checkpoint file after successful completion"""
        try:
            if self.checkpoint_file.exists():
                self.checkpoint_file.unlink()
                self.logger.info("Checkpoint file cleaned up")
        except Exception as e:
            self.logger.warning(f"Failed to clean up checkpoint file: {e}")

    def checkpoint_exists(self) -> bool:
        """Check if a checkpoint file exists"""
        return self.checkpoint_file.exists()

    def get_checkpoint_summary(self) -> dict | None:
        """Get summary information about existing checkpoint without fully loading it"""
        if not self.checkpoint_file.exists():
            return None

        try:
            with open(self.checkpoint_file, encoding="utf-8") as f:
                data = json.load(f)

            return {
                "survey_topic": data.get("survey_topic", "Unknown"),
                "total_processed": data.get("total_processed", 0),
                "num_results": len(data.get("results", [])),
                "processed_files": len(data.get("processed_files", [])),
                "current_file": data.get("current_file"),
                "timestamp": data.get("timestamp", "Unknown"),
            }
        except Exception as e:
            self.logger.error(f"Failed to read checkpoint summary: {e}")
            return None
