#!/usr/bin/env python3
"""
SurveyHelper - Paper Fetching Stage

Downloads academic papers from ML conferences (ICLR, ICML, NeurIPS).
This is Stage 1 of the SurveyHelper pipeline.

Usage:
    python fetch_papers.py --conferences ICML ICLR --start-year 2023 --end-year 2024
    python fetch_papers.py --help

Examples:
    # Download all conferences for recent years
    python fetch_papers.py --start-year 2023 --end-year 2024

    # Download only ICML papers
    python fetch_papers.py --conferences ICML --start-year 2022 --end-year 2024

    # Save to custom directory
    python fetch_papers.py --output-dir my_papers/
"""

import logging

from pydantic import ValidationError

from survey_helper.core.config import FetchConfig
from survey_helper.fetch.downloader import MLConferenceDownloader


def main():
    """Main entry point for paper fetching."""
    # Set up basic logging first
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )

    try:
        # Parse configuration from CLI args and env vars
        config = FetchConfig()

        logging.info(
            f"🚀 Starting ML conference download for {', '.join(config.conferences)}"
        )
        logging.info(f"📅 Years: {config.start_year}-{config.end_year}")
        logging.info(f"📂 Output directory: {config.output_dir}")

        # Create downloader and fetch papers
        downloader = MLConferenceDownloader(
            config.conferences, config.start_year, config.end_year
        )
        results = downloader.download_all(config.output_dir)

        # Print summary
        logging.info("\n📊 DOWNLOAD SUMMARY")
        logging.info("===================")
        grand_total = 0

        for conference, years in results.items():
            logging.info(f"\n{conference}:")
            conference_total = 0
            for year, count in years.items():
                logging.info(f"  {year}: {count:,} papers")
                conference_total += count
            logging.info(f"  Total: {conference_total:,} papers")
            grand_total += conference_total

        logging.info(f"\n🎉 Grand Total: {grand_total:,} papers downloaded")
        logging.info("✅ Download completed successfully!")

        if grand_total > 0:
            logging.info(f"\nNext step: Analyze papers with:")
            logging.info(f"  uv run analyze.py --survey-topic 'Your Research Topic'")

    except ValidationError as e:
        logging.error("❌ Configuration validation error:")
        for error in e.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            message = error["msg"]
            logging.error(f"  {field}: {message}")
        logging.info("\nUse --help for usage information.")
        return 1
    except ValueError as e:
        logging.error(f"❌ Configuration error: {e}")
        logging.info("Use --help for usage information.")
        return 1
    except Exception as e:
        logging.error(f"❌ Unexpected error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
