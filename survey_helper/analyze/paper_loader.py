import json
import logging
from collections.abc import Generator
from pathlib import Path
from typing import Any

from ..core.models import Paper


class PaperLoader:
    def __init__(self, input_dir: str = "output"):
        self.input_dir = Path(input_dir)
        self.logger = logging.getLogger(f"paper_relevance.{self.__class__.__name__}")
        if not self.input_dir.exists():
            raise FileNotFoundError(f"Input directory {input_dir} does not exist")

    def get_paper_files(self) -> list[Path]:
        """Get all JSON paper files from the input directory"""
        paper_files = list(self.input_dir.glob("*.json"))
        paper_files.sort()  # Ensure consistent ordering
        return paper_files

    def load_papers_from_file(self, file_path: Path) -> list[Paper]:
        """Load papers from a single JSON file"""
        try:
            with open(file_path, encoding="utf-8") as f:
                raw_papers = json.load(f)

            papers = []
            for raw_paper in raw_papers:
                try:
                    paper = Paper(**raw_paper)
                    papers.append(paper)
                except Exception as e:
                    self.logger.error(f"Error parsing paper from {file_path}: {e}")
                    self.logger.debug(f"Raw paper data: {raw_paper}")
                    continue

            self.logger.info(f"Loaded {len(papers)} papers from {file_path.name}")
            return papers

        except json.JSONDecodeError as e:
            self.logger.error(f"Error decoding JSON from {file_path}: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Error loading papers from {file_path}: {e}")
            return []

    def load_all_papers(self) -> Generator[tuple[list[Paper], str], None, None]:
        """Generator that yields batches of papers with their source file"""
        paper_files = self.get_paper_files()

        if not paper_files:
            self.logger.warning(f"No JSON files found in {self.input_dir}")
            return

        self.logger.info(f"Found {len(paper_files)} paper files:")
        for file_path in paper_files:
            self.logger.debug(f"  - {file_path.name}")

        for file_path in paper_files:
            papers = self.load_papers_from_file(file_path)
            if papers:
                yield papers, file_path.name

    def get_papers_summary(self) -> dict[str, Any]:
        """Get a summary of all papers in the directory"""
        summary = {
            "total_papers": 0,
            "files_processed": 0,
            "papers_by_conference": {},
            "papers_by_year": {},
            "file_details": [],
        }

        for papers, filename in self.load_all_papers():
            summary["files_processed"] += 1
            summary["total_papers"] += len(papers)

            file_info = {
                "filename": filename,
                "paper_count": len(papers),
                "conferences": set(),
                "years": set(),
            }

            for paper in papers:
                # Update conference counts
                if paper.conference_name not in summary["papers_by_conference"]:
                    summary["papers_by_conference"][paper.conference_name] = 0
                summary["papers_by_conference"][paper.conference_name] += 1

                # Update year counts
                if paper.publication_year not in summary["papers_by_year"]:
                    summary["papers_by_year"][paper.publication_year] = 0
                summary["papers_by_year"][paper.publication_year] += 1

                # Track file info
                file_info["conferences"].add(paper.conference_name)
                file_info["years"].add(paper.publication_year)

            # Convert sets to lists for JSON serialization
            file_info["conferences"] = list(file_info["conferences"])
            file_info["years"] = list(file_info["years"])
            summary["file_details"].append(file_info)

        return summary

    def filter_papers_by_year(
        self,
        papers: list[Paper],
        min_year: int | None = None,
        max_year: int | None = None,
    ) -> list[Paper]:
        """Filter papers by publication year"""
        filtered_papers = papers

        if min_year is not None:
            filtered_papers = [
                p for p in filtered_papers if p.publication_year >= min_year
            ]

        if max_year is not None:
            filtered_papers = [
                p for p in filtered_papers if p.publication_year <= max_year
            ]

        return filtered_papers

    def filter_papers_by_conference(
        self, papers: list[Paper], conferences: list[str]
    ) -> list[Paper]:
        """Filter papers by conference name"""
        if not conferences:
            return papers
        conference_set = {conf.upper() for conf in conferences}
        filtered = [p for p in papers if p.conference_name.upper() in conference_set]
        self.logger.debug(
            f"Conference filter: looking for {conferences} in papers with conferences {set(p.conference_name for p in papers[:5])}"
        )
        return filtered
