import csv
import logging
from pathlib import Path

from ..core.models import PaperRelevanceResult, RelevanceRating


class CSVExporter:
    def __init__(self, output_file: str = "relevance_index.csv"):
        self.output_file = Path(output_file)
        self.logger = logging.getLogger(f"paper_relevance.{self.__class__.__name__}")

    def export_results(self, results: list[PaperRelevanceResult]) -> None:
        """Export relevance results to CSV file"""
        fieldnames = [
            "title",
            "authors",
            "conference",
            "year",
            "relevance_rating",
            "confidence_score",
            "reasoning",
            "file_source",
        ]

        with open(self.output_file, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for result in results:
                # Convert authors list to string
                authors_str = "; ".join(result.authors)

                row = {
                    "title": result.title,
                    "authors": authors_str,
                    "conference": result.conference,
                    "year": result.year,
                    "relevance_rating": result.relevance_rating.value,
                    "confidence_score": (
                        result.confidence_score
                        if result.confidence_score is not None
                        else ""
                    ),
                    "reasoning": result.reasoning or "",
                    "file_source": result.file_source,
                }
                writer.writerow(row)

        self.logger.info(f"Exported {len(results)} results to {self.output_file}")

    def export_summary_stats(
        self,
        results: list[PaperRelevanceResult],
        summary_file: Path | str | None = None,
    ) -> None:
        """Export summary statistics to a separate CSV file"""
        if summary_file is None:
            summary_file = self.output_file.with_suffix(".summary.csv")
        else:
            summary_file = Path(summary_file)

        # Calculate statistics
        total_papers = len(results)
        high_count = sum(
            1 for r in results if r.relevance_rating == RelevanceRating.HIGH
        )
        medium_count = sum(
            1 for r in results if r.relevance_rating == RelevanceRating.MEDIUM
        )
        low_count = sum(1 for r in results if r.relevance_rating == RelevanceRating.LOW)
        unknown_count = sum(
            1 for r in results if r.relevance_rating == RelevanceRating.UNKNOWN
        )

        # Group by conference
        conference_stats = {}
        for result in results:
            conf = result.conference
            if conf not in conference_stats:
                conference_stats[conf] = {
                    "total": 0,
                    "high": 0,
                    "medium": 0,
                    "low": 0,
                    "unknown": 0,
                }

            conference_stats[conf]["total"] += 1
            if result.relevance_rating == RelevanceRating.HIGH:
                conference_stats[conf]["high"] += 1
            elif result.relevance_rating == RelevanceRating.MEDIUM:
                conference_stats[conf]["medium"] += 1
            elif result.relevance_rating == RelevanceRating.LOW:
                conference_stats[conf]["low"] += 1
            else:  # UNKNOWN
                conference_stats[conf]["unknown"] += 1

        # Group by year
        year_stats = {}
        for result in results:
            year = result.year
            if year not in year_stats:
                year_stats[year] = {
                    "total": 0,
                    "high": 0,
                    "medium": 0,
                    "low": 0,
                    "unknown": 0,
                }

            year_stats[year]["total"] += 1
            if result.relevance_rating == RelevanceRating.HIGH:
                year_stats[year]["high"] += 1
            elif result.relevance_rating == RelevanceRating.MEDIUM:
                year_stats[year]["medium"] += 1
            elif result.relevance_rating == RelevanceRating.LOW:
                year_stats[year]["low"] += 1
            else:  # UNKNOWN
                year_stats[year]["unknown"] += 1

        # Write summary CSV
        with open(summary_file, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)

            # Overall statistics
            writer.writerow(["Overall Statistics"])
            writer.writerow(["Metric", "Count", "Percentage"])
            writer.writerow(["Total Papers", total_papers, "100.0%"])
            writer.writerow(
                [
                    "High Relevance",
                    high_count,
                    f"{high_count / total_papers * 100:.1f}%",
                ]
            )
            writer.writerow(
                [
                    "Medium Relevance",
                    medium_count,
                    f"{medium_count / total_papers * 100:.1f}%",
                ]
            )
            writer.writerow(
                ["Low Relevance", low_count, f"{low_count / total_papers * 100:.1f}%"]
            )
            if unknown_count > 0:
                writer.writerow(
                    [
                        "Unknown Relevance",
                        unknown_count,
                        f"{unknown_count / total_papers * 100:.1f}%",
                    ]
                )
            writer.writerow([])

            # Conference breakdown
            writer.writerow(["Conference Breakdown"])
            writer.writerow(
                ["Conference", "Total", "High", "Medium", "Low", "Unknown", "High%"]
            )
            for conf, stats in sorted(conference_stats.items()):
                high_pct = (
                    f"{stats['high'] / stats['total'] * 100:.1f}%"
                    if stats["total"] > 0
                    else "0.0%"
                )
                writer.writerow(
                    [
                        conf,
                        stats["total"],
                        stats["high"],
                        stats["medium"],
                        stats["low"],
                        stats["unknown"],
                        high_pct,
                    ]
                )
            writer.writerow([])

            # Year breakdown
            writer.writerow(["Year Breakdown"])
            writer.writerow(
                ["Year", "Total", "High", "Medium", "Low", "Unknown", "High%"]
            )
            for year, stats in sorted(year_stats.items()):
                high_pct = (
                    f"{stats['high'] / stats['total'] * 100:.1f}%"
                    if stats["total"] > 0
                    else "0.0%"
                )
                writer.writerow(
                    [
                        year,
                        stats["total"],
                        stats["high"],
                        stats["medium"],
                        stats["low"],
                        stats["unknown"],
                        high_pct,
                    ]
                )

        self.logger.info(f"Exported summary statistics to {summary_file}")
        summary_msg = f"Overall relevance distribution: High={high_count}, Medium={medium_count}, Low={low_count}"
        if unknown_count > 0:
            summary_msg += f", Unknown={unknown_count}"
        self.logger.info(summary_msg)

    def create_filtered_csv(
        self,
        results: list[PaperRelevanceResult],
        relevance_filter: RelevanceRating,
        output_suffix: str = "_filtered",
    ) -> None:
        """Create a filtered CSV with only papers of specified relevance"""
        filtered_results = [
            r for r in results if r.relevance_rating == relevance_filter
        ]

        if not filtered_results:
            self.logger.warning(
                f"No papers found with {relevance_filter.value} relevance"
            )
            return

        # Create filtered filename
        filtered_file = self.output_file.with_suffix(f"{output_suffix}.csv")

        # Use the same export function with filtered results
        temp_exporter = CSVExporter(str(filtered_file))
        temp_exporter.export_results(filtered_results)

        self.logger.info(
            f"Created filtered CSV with {len(filtered_results)} {relevance_filter.value} relevance papers"
        )
