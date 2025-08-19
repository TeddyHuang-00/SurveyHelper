"""Paper data processors for cleaning and normalizing conference data."""

from datetime import datetime


class PaperProcessor:
    """Processes raw paper data into clean, normalized format."""

    def process_papers(
        self, papers: list[dict], conference: str, year: int
    ) -> list[dict]:
        """Process raw paper data into clean format."""
        processed_papers = []

        for paper_data in papers:
            processed_paper = self.process_single_paper(paper_data, conference, year)
            if processed_paper:
                processed_papers.append(processed_paper)

        return processed_papers

    def process_single_paper(
        self, paper_data: dict, conference: str, year: int
    ) -> dict | None:
        """Process a single paper into clean format."""
        # Extract title
        title = paper_data.get("name", None)

        # Extract authors
        authors = self._extract_authors(paper_data.get("authors", []))

        # Skip if missing essential data
        if not title or not authors:
            return None

        # Extract abstract
        abstract = paper_data.get("abstract", None)

        # Extract URLs
        paper_url = paper_data.get("paper_url", None)
        pdf_url = self._extract_pdf_url(paper_data, paper_url)

        # Extract additional metadata
        decision = paper_data.get("decision", None)
        session = paper_data.get("session", None)
        topic = paper_data.get("topic", None)

        # Create processed paper entry
        return {
            "title": title,
            "authors": authors,
            "abstract": abstract.strip() if abstract else None,
            "publication_year": year,
            "conference_name": conference,
            "venue_type": "Conference",
            "track": decision.strip() if decision else None,
            "session": session.strip() if session else None,
            "topic": topic.strip() if topic else None,
            "pdf_url": pdf_url.strip() if pdf_url else None,
            "abstract_url": paper_url.strip() if paper_url else None,
            "openreview_url": (
                paper_url.strip()
                if paper_url and "openreview.net" in paper_url
                else None
            ),
            "scraped_at": datetime.now().isoformat(),
        }

    def _extract_authors(self, author_data: list) -> list[str]:
        """Extract author names from various formats."""
        authors = []

        for author in author_data:
            if isinstance(author, dict):
                fullname = author.get("fullname", None)
                if fullname:
                    authors.append(fullname)
            elif isinstance(author, str):
                authors.append(author.strip())

        return authors

    def _extract_pdf_url(self, paper_data: dict, paper_url: str | None) -> str | None:
        """Extract or generate PDF URL."""
        pdf_url = paper_data.get("paper_pdf_url", None)

        # Generate PDF URL from OpenReview URL if not provided
        if not pdf_url and paper_url and "openreview.net/forum?id=" in paper_url:
            paper_id = paper_url.split("forum?id=")[-1]
            pdf_url = f"https://openreview.net/pdf?id={paper_id}"

        return pdf_url
