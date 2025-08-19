"""ML Conference paper downloader."""

import json
import logging
from datetime import datetime
from pathlib import Path

import requests

from ..core.models import Conference

# Conference base URLs and configurations
CONFERENCE_CONFIGS = {
    Conference.ICLR: {"domain": "iclr.cc", "name_pattern": "iclr"},
    Conference.ICML: {"domain": "icml.cc", "name_pattern": "icml"},
    Conference.NeurIPS: {"domain": "neurips.cc", "name_pattern": "neurips"},
}
CURRENT_YEAR = datetime.now().year


class MLConferenceDownloader:
    """Direct ML conference paper data downloader."""

    def __init__(
        self,
        conferences: list[Conference] | None = None,
        start_year: int = CURRENT_YEAR,
        end_year: int = CURRENT_YEAR,
    ):
        self.conferences = conferences or [
            Conference.ICLR,
            Conference.ICML,
            Conference.NeurIPS,
        ]
        self.start_year = start_year
        self.end_year = end_year
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "ML-Conference-Downloader/1.0 (Academic Research)"}
        )

    def generate_url(self, conference: Conference, year: int) -> str:
        """Generate conference data URL dynamically."""
        config = CONFERENCE_CONFIGS.get(conference)
        if not config:
            return ""

        domain = config["domain"]
        name_pattern = config["name_pattern"]

        return f"https://{domain}/static/virtual/data/{name_pattern}-{year}-orals-posters.json"

    def download_conference_year(self, conference: Conference, year: int) -> list[dict]:
        """Download papers for a specific conference and year."""
        from .processors import PaperProcessor

        url = self.generate_url(conference, year)
        if not url:
            logging.error(f"No URL pattern available for {conference}")
            return []

        logging.info(f"Downloading {conference} {year} papers from {url}")

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            data = response.json()
            papers = data.get("results", [])

            if not papers:
                logging.warning(
                    f"No papers found for {conference} {year} (empty results)"
                )
                return []

            logging.info(f"Found {len(papers)} papers for {conference} {year}")

            processor = PaperProcessor()
            return processor.process_papers(papers, conference, year)

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logging.warning(
                    f"Data not available for {conference} {year} (404 Not Found)"
                )
            else:
                logging.error(f"HTTP error downloading {conference} {year} data: {e}")
            return []
        except requests.RequestException as e:
            logging.error(f"Network error downloading {conference} {year} data: {e}")
            return []
        except json.JSONDecodeError as e:
            logging.error(f"JSON parsing error for {conference} {year}: {e}")
            return []
        except Exception as e:
            logging.error(f"Unexpected error for {conference} {year}: {e}")
            return []

    def download_all(
        self, output_dir: str = "data/papers"
    ) -> dict[str, dict[int, int]]:
        """Download papers for all specified conferences and years."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        results = {}

        for conference in self.conferences:
            logging.info(f"\n🎯 Processing {conference} conference...")
            conference_results = {}

            for year in range(self.start_year, self.end_year + 1):
                papers = self.download_conference_year(conference, year)
                # Check if there are papers in the file
                if len(papers) == 0:
                    logging.warning(
                        f"No papers found for {conference} {year}, skipping..."
                    )
                    continue
                conference_results[year] = len(papers)

                # Save individual year file
                year_file = output_path / f"{conference.lower()}_{year}_papers.json"
                with open(year_file, "w") as f:
                    json.dump(papers, f, indent=2, ensure_ascii=False)

                logging.info(f"Saved {len(papers)} papers to {year_file}")

            results[conference] = conference_results

        return results
