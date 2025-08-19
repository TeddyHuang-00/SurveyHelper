"""Paper filtering utilities."""


class PaperFilters:
    """Utility class for filtering papers by various criteria."""

    @staticmethod
    def filter_by_year(papers: list[dict], min_year: int, max_year: int) -> list[dict]:
        """Filter papers by publication year range."""
        return [
            paper
            for paper in papers
            if min_year <= paper.get("publication_year", 0) <= max_year
        ]

    @staticmethod
    def filter_by_conferences(papers: list[dict], conferences: list[str]) -> list[dict]:
        """Filter papers by conference names."""
        # Convert to uppercase for case-insensitive matching
        conferences_upper = [conf.upper() for conf in conferences]
        return [
            paper
            for paper in papers
            if paper.get("conference_name", "").upper() in conferences_upper
        ]

    @staticmethod
    def filter_by_keywords(
        papers: list[dict], keywords: list[str], search_fields: list[str] | None = None
    ) -> list[dict]:
        """Filter papers by keywords in title, abstract, or other fields."""
        if search_fields is None:
            search_fields = ["title", "abstract"]

        keywords_lower = [kw.lower() for kw in keywords]
        filtered_papers = []

        for paper in papers:
            found_keyword = False
            for field in search_fields:
                field_value = paper.get(field, "")
                if field_value and isinstance(field_value, str):
                    field_lower = field_value.lower()
                    if any(kw in field_lower for kw in keywords_lower):
                        found_keyword = True
                        break

            if found_keyword:
                filtered_papers.append(paper)

        return filtered_papers
