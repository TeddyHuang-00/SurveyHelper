#!/usr/bin/env python3
"""
SurveyHelper - Paper Analysis Stage

Analyzes downloaded papers for relevance to your research topic using LLMs.
This is Stage 2 of the SurveyHelper pipeline.

Usage:
    python analyze.py --survey-topic "Your Research Topic"
    python analyze.py --help

Examples:
    # Basic analysis
    python analyze.py --survey-topic "Large Language Models"

    # With filters
    python analyze.py --survey-topic "Computer Vision" --filter-years '[2023,2024]'

    # Custom input/output
    python analyze.py --survey-topic "NLP" --input data/papers --output results.csv

    # Dry run to see what would be processed
    python analyze.py --survey-topic "ML" --dry-run
"""

import asyncio
import time

from survey_helper.analyze.exporter import CSVExporter
from survey_helper.analyze.judge import RelevanceJudge
from survey_helper.analyze.paper_loader import PaperLoader
from survey_helper.core.config import Config
from survey_helper.core.logging_config import setup_logging
from survey_helper.core.models import RelevanceRating
from survey_helper.utils.checkpoint import CheckpointManager


def batch_papers(papers: list, batch_size: int):
    """Split papers into batches for processing."""
    for i in range(0, len(papers), batch_size):
        yield papers[i : i + batch_size]


async def main():
    """Main entry point for paper analysis."""
    # Load configuration from CLI args, env vars, and config file
    try:
        config = Config()
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return 1

    # Setup logging first
    logger = setup_logging(
        log_level=config.logging.log_level,
        log_file=config.logging.log_file,
        verbose=config.logging.verbose,
    )

    # Validate configuration
    if not config.survey.topic:
        logger.error(
            "Survey topic not specified. Use --survey-topic or set SURVEY__TOPIC in config"
        )
        return 1

    logger.info("📝 SurveyHelper - Paper Analysis Stage")
    logger.info(f"Survey Topic: {config.survey.topic}")
    logger.info(f"Model: {config.llm.model_name}")
    logger.info(f"Input Directory: {config.processing.input_dir}")
    logger.info(f"Output File: {config.processing.output_file}")
    logger.info(f"Batch Size: {config.processing.batch_size}")

    # Initialize components
    try:
        loader = PaperLoader(config.processing.input_dir)
        exporter = CSVExporter(config.processing.output_file)
        checkpoint_manager = CheckpointManager(config.processing.checkpoint_file)

        # Check for existing checkpoint
        existing_checkpoint = None
        if checkpoint_manager.checkpoint_exists():
            summary = checkpoint_manager.get_checkpoint_summary()
            if summary:
                logger.info(f"Found existing checkpoint from {summary['timestamp']}")
                logger.info(
                    f"Previous run: {summary['total_processed']} papers processed, {summary['num_results']} results saved"
                )
                logger.info(f"Survey topic: {summary['survey_topic']}")

                if summary["survey_topic"] == config.survey.topic:
                    response = input("Resume from checkpoint? (y/n): ").lower().strip()
                    if response == "y":
                        existing_checkpoint = checkpoint_manager.load_checkpoint()
                        logger.info("Resuming from checkpoint")
                    else:
                        logger.info("Starting fresh run")
                        checkpoint_manager.clear_checkpoint()
                else:
                    logger.warning("Survey topic changed, starting fresh run")
                    checkpoint_manager.clear_checkpoint()

        # Get paper summary
        logger.info("Analyzing paper collection...")
        summary = loader.get_papers_summary()
        logger.info(
            f"Found {summary['total_papers']} papers across {summary['files_processed']} files"
        )
        logger.info(f"Conferences: {list(summary['papers_by_conference'].keys())}")
        logger.info(f"Years: {sorted(summary['papers_by_year'].keys())}")

        if config.app.dry_run:
            logger.info("Dry run complete. Use without --dry-run to process papers.")
            return 0

        # Initialize judge (this will load the model)
        judge = RelevanceJudge(config)

        # Process papers
        from survey_helper.core.models import PaperRelevanceResult, ProcessingCheckpoint

        all_results: list[PaperRelevanceResult] = []
        total_processed = 0
        start_time = time.time()
        processed_files = []

        # Restore state from checkpoint if resuming
        if existing_checkpoint:
            all_results = existing_checkpoint.results
            total_processed = existing_checkpoint.total_processed
            processed_files = existing_checkpoint.processed_files
            logger.info(f"Restored {len(all_results)} previous results")

        for papers, filename in loader.load_all_papers():
            # Skip files that have already been processed in checkpoint
            if existing_checkpoint and filename in processed_files:
                logger.info(f"Skipping {filename} (already processed)")
                continue

            logger.info(f"Processing {filename} ({len(papers)} papers)")

            # Apply filters if specified
            if config.filter.years:
                papers = loader.filter_papers_by_year(papers, *config.filter.years)
                logger.info(f"After year filtering: {len(papers)} papers")

            if config.filter.conferences:
                papers = loader.filter_papers_by_conference(
                    papers, config.filter.conferences
                )
                logger.info(f"After conference filtering: {len(papers)} papers")

            if not papers:
                logger.warning("No papers left after filtering, skipping...")
                processed_files.append(filename)
                continue

            # Determine starting batch if resuming from checkpoint
            start_batch = 0
            if existing_checkpoint and existing_checkpoint.current_file == filename:
                start_batch = existing_checkpoint.current_batch_index
                logger.info(f"Resuming from batch {start_batch + 1}")

            # Process in batches
            for i, batch in enumerate(
                batch_papers(papers, config.processing.batch_size)
            ):
                batch_num = i + 1

                # Skip batches that were already processed in checkpoint
                if i < start_batch:
                    continue

                total_batches = (
                    len(papers) + config.processing.batch_size - 1
                ) // config.processing.batch_size
                logger.info(f"  Processing batch {batch_num}/{total_batches}")

                batch_results = await judge.judge_papers(batch)

                # Set file source for each result
                for result in batch_results:
                    result.file_source = filename

                all_results.extend(batch_results)
                total_processed += len(batch)

                # Show progress
                elapsed = time.time() - start_time
                rate = total_processed / elapsed if elapsed > 0 else 0
                logger.info(
                    f"  Progress: {total_processed} papers processed ({rate:.1f} papers/sec)"
                )

                # Save checkpoint after each batch if enabled
                if config.processing.save_every_batch:
                    current_processed_files = processed_files.copy()
                    if batch_num == total_batches:
                        # File completed, add to processed files
                        current_processed_files.append(filename)
                        current_file = None
                        current_batch = 0
                    else:
                        # File in progress
                        current_file = filename
                        current_batch = i + 1

                    checkpoint = ProcessingCheckpoint(
                        survey_topic=config.survey.topic,
                        processed_files=current_processed_files,
                        current_file=current_file,
                        current_batch_index=current_batch,
                        results=all_results,
                        total_processed=total_processed,
                    )
                    checkpoint_manager.save_checkpoint(checkpoint)

            # Mark file as completed
            processed_files.append(filename)
            # Reset existing_checkpoint to None after processing the resumed file
            if existing_checkpoint and existing_checkpoint.current_file == filename:
                existing_checkpoint = None

        if not all_results:
            logger.error(
                "No papers were processed. Check your filters and input directory."
            )
            return 1

        # Export results
        logger.info("Exporting results...")
        exporter.export_results(all_results)
        exporter.export_summary_stats(all_results)

        # Create filtered CSVs if requested
        if config.app.create_separate_csvs:
            logger.info("Creating filtered CSV files...")
            for rating in RelevanceRating:
                exporter.create_filtered_csv(
                    all_results, rating, f"_{rating.value.lower()}"
                )

        # Clean up checkpoint file on successful completion
        checkpoint_manager.clear_checkpoint()

        # Final summary
        total_time = time.time() - start_time
        high_count = sum(
            1 for r in all_results if r.relevance_rating == RelevanceRating.HIGH
        )
        medium_count = sum(
            1 for r in all_results if r.relevance_rating == RelevanceRating.MEDIUM
        )
        low_count = sum(
            1 for r in all_results if r.relevance_rating == RelevanceRating.LOW
        )
        unknown_count = sum(
            1 for r in all_results if r.relevance_rating == RelevanceRating.UNKNOWN
        )

        logger.info("=== Processing Complete ===")
        logger.info(f"Total papers processed: {len(all_results)}")
        logger.info(
            f"Processing time: {total_time:.1f} seconds ({len(all_results) / total_time:.1f} papers/sec)"
        )
        logger.info("Relevance distribution:")
        logger.info(
            f"  High: {high_count} ({high_count / len(all_results) * 100:.1f}%)"
        )
        logger.info(
            f"  Medium: {medium_count} ({medium_count / len(all_results) * 100:.1f}%)"
        )
        logger.info(f"  Low: {low_count} ({low_count / len(all_results) * 100:.1f}%)")
        if unknown_count > 0:
            logger.info(
                f"  Unknown: {unknown_count} ({unknown_count / len(all_results) * 100:.1f}%)"
            )
        logger.info(f"Results saved to: {config.processing.output_file}")

        return 0

    except KeyboardInterrupt:
        logger.warning("Processing interrupted by user")
        # Save current progress as checkpoint if we have any results
        if (
            "all_results" in locals()
            and all_results
            and config.processing.save_every_batch
        ):
            logger.info("Saving current progress...")
            try:
                from survey_helper.core.models import ProcessingCheckpoint

                checkpoint = ProcessingCheckpoint(
                    survey_topic=config.survey.topic,
                    processed_files=processed_files,
                    current_file=locals().get("filename"),
                    current_batch_index=locals().get("i", 0),
                    results=all_results,
                    total_processed=total_processed,
                )
                checkpoint_manager.save_checkpoint(checkpoint)
                logger.info(
                    f"Progress saved. Resume with same command to continue from {len(all_results)} processed papers."
                )
            except Exception as e:
                logger.error(f"Failed to save progress: {e}")
        return 1
    except Exception as e:
        logger.error(f"Error: {e}")
        logger.exception("Full traceback:")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
