import asyncio
import json
import time

from ollama import AsyncClient
from pydantic import ValidationError

from ..core.config import Config
from ..core.logging_config import get_logger
from ..core.models import (
    LLMRelevanceResponse,
    Paper,
    PaperRelevanceResult,
    RelevanceRating,
)


class RelevanceJudge:
    def __init__(self, config: Config):
        self.config = config
        self.client = None
        self.logger = get_logger("judge")

    async def initialize_client(self):
        """Initialize the ollama client"""
        self.logger.info(
            f"Initializing ollama client for: {self.config.llm.ollama_url}"
        )
        self.logger.info(f"Model: {self.config.llm.model_name}")

        try:
            self.client = AsyncClient(host=self.config.llm.ollama_url)

            # Test the connection
            models = (await self.client.list()).models
            available_models = [m.model for m in models if m.model]
            self.logger.debug(f"Available models: {available_models}")

            if self.config.llm.model_name not in available_models:
                self.logger.warning(
                    f"Model {self.config.llm.model_name} not found in available models"
                )
                if len(available_models) > 0:
                    self.logger.warning(
                        f"Using first available model: {available_models[0]}"
                    )
                    self.config.llm.model_name = available_models[0]
                else:
                    raise RuntimeError("No models available in Ollama")

            self.logger.info(
                f"Client initialized successfully with model: {self.config.llm.model_name}"
            )

        except Exception as e:
            self.logger.error(f"Failed to initialize client: {e}")
            raise RuntimeError(
                f"Could not connect to Ollama API at {self.config.llm.ollama_url}: {e}"
            )

    def create_relevance_prompt(self, paper: Paper) -> str:
        """Create a structured prompt for judging paper relevance"""
        abstract = paper.abstract or "No abstract available"
        title = paper.title

        # Get the JSON schema for structured output
        schema = LLMRelevanceResponse.get_json_schema_str()

        prompt = f"""You are an expert researcher evaluating academic papers for a systematic literature review.

SURVEY TOPIC: {self.config.survey.topic}
{f"SURVEY DESCRIPTION: {self.config.survey.description}\n" if self.config.survey.description else ""}
PAPER TO EVALUATE:
Title: {title}
Abstract: {abstract}
Conference: {paper.conference_name} {paper.publication_year}

TASK: Evaluate this paper's relevance to the survey topic.

RATING GUIDELINES:
- High: Directly addresses the survey topic, core contribution aligns with survey scope
- Medium: Related to topic but not central, partial overlap or tangential relevance
- Low: Minimal connection, outside survey scope, or unrelated

INSTRUCTIONS:
1. Analyze the paper's title and abstract carefully
2. Determine relevance level based on topic alignment
3. Provide confidence score (0.0-1.0) based on how certain you are
4. Give brief reasoning for your decision (2-3 sentences)

You MUST respond with valid JSON matching this exact schema:
{schema}

Response:"""

        return prompt

    def parse_llm_response(
        self, response_text: str
    ) -> tuple[RelevanceRating, float | None, str | None]:
        """Parse LLM response using pydantic validation for robust structured output"""
        response_text = response_text.strip()

        # Check if this is a thinking model response
        has_thinking_tags = (
            "<think>" in response_text.lower() or "</think>" in response_text.lower()
        )
        if has_thinking_tags:
            self.logger.debug(
                "Detected thinking model response, extracting JSON after thinking..."
            )

        # Try to extract JSON from various formats
        json_candidates = self._extract_json_candidates(response_text)

        if has_thinking_tags:
            self.logger.debug(
                f"Found {len(json_candidates)} JSON candidates after thinking tag processing"
            )

        for i, json_str in enumerate(json_candidates):
            try:
                # First attempt: standard JSON parsing with pydantic
                response_obj = LLMRelevanceResponse.model_validate_json(json_str)
                if has_thinking_tags:
                    self.logger.debug(
                        f"Successfully parsed JSON candidate {i + 1} from thinking model"
                    )
                return (
                    response_obj.to_relevance_rating_enum(),
                    response_obj.confidence_score,
                    response_obj.reasoning,
                )
            except ValidationError as e:
                self.logger.debug(
                    f"Pydantic validation failed for candidate {i + 1}: {e}"
                )
                self.logger.debug(f"JSON candidate was: {json_str[:200]}...")
                continue
            except json.JSONDecodeError as e:
                self.logger.debug(f"JSON decode error for candidate {i + 1}: {e}")
                self.logger.debug(f"JSON candidate was: {json_str[:200]}...")
                continue

        # Enhanced error message for thinking models
        if has_thinking_tags:
            cleaned_text = self._remove_thinking_tags(response_text)
            error_msg = f"Failed to parse thinking model response. Cleaned text (first 300 chars): {cleaned_text[:300]}..."
        else:
            error_msg = f"Failed to parse standard response (first 300 chars): {response_text[:300]}..."

        raise ValueError(error_msg)

    def _extract_json_candidates(self, text: str) -> list[str]:
        """Extract potential JSON strings from LLM response using multiple patterns"""
        import re

        # First, handle thinking models by extracting content outside <think></think> tags
        text_without_thinking = self._remove_thinking_tags(text)

        # Prioritized patterns for thinking models and structured output
        json_patterns = [
            # Patterns for content after thinking tags (highest priority)
            r"</think>\s*(\{.*?\})",  # JSON directly after </think>
            r"</think>[^{]*(\{.*?\"relevance_rating\".*?\})",  # JSON with relevance_rating after </think>
            # Standard structured patterns
            r"```json\s*(\{.*?\})\s*```",  # Markdown JSON block
            r"```\s*(\{.*?\})\s*```",  # Generic code block
            r"<response>\s*(\{.*?\})\s*</response>",  # XML-wrapped
            r"Response:\s*(\{.*?\})",  # After "Response:" label
            # Patterns with relevance_rating (medium priority)
            r'\{[^{}]*"relevance_rating"[^{}]*\}',  # Simple JSON on one line
            r'\{(?:[^{}]|\{[^{}]*\})*"relevance_rating"(?:[^{}]|\{[^{}]*\})*\}',  # Nested braces
            # Generic patterns (lowest priority)
            r"(\{.*?\})\s*$",  # JSON at end of response
            r"(\{.*?\})",  # Any JSON-like structure
        ]

        candidates = []

        # First try patterns on text without thinking tags (higher priority)
        for pattern in json_patterns:
            matches = re.findall(
                pattern, text_without_thinking, re.DOTALL | re.IGNORECASE
            )
            for match in matches:
                json_str = (
                    match if isinstance(match, str) else match[0] if match else ""
                )
                if json_str and json_str not in candidates:
                    candidates.append(json_str.strip())

        # Then try patterns on original text (lower priority, for fallback)
        for pattern in json_patterns:
            matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
            for match in matches:
                json_str = (
                    match if isinstance(match, str) else match[0] if match else ""
                )
                if json_str and json_str not in candidates:
                    candidates.append(json_str.strip())

        # Try the whole text without thinking tags if it looks like JSON
        text_stripped = text_without_thinking.strip()
        if text_stripped.startswith("{") and text_stripped.endswith("}"):
            if text_stripped not in candidates:
                candidates.append(text_stripped)

        # Fallback: try the original text if it looks like pure JSON
        original_stripped = text.strip()
        if original_stripped.startswith("{") and original_stripped.endswith("}"):
            if original_stripped not in candidates:
                candidates.append(original_stripped)

        return candidates

    def _remove_thinking_tags(self, text: str) -> str:
        """Remove <think></think> content from text to extract actual response"""
        import re

        # Remove content between <think> and </think> tags (case insensitive)
        cleaned = re.sub(
            r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE
        )

        # Also remove standalone thinking tags that might be left
        cleaned = re.sub(r"</?think>", "", cleaned, flags=re.IGNORECASE)

        return cleaned.strip()

    async def judge_papers(self, papers: list[Paper]) -> list[PaperRelevanceResult]:
        """Judge relevance for a batch of papers with robust error handling"""
        if not self.client:
            await self.initialize_client()

        tasks = [self.judge_single_paper_with_retry(paper) for paper in papers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        results = [
            (
                res
                if isinstance(res, PaperRelevanceResult)
                else PaperRelevanceResult(
                    title=paper.title,
                    authors=paper.authors,
                    conference=paper.conference_name,
                    year=paper.publication_year,
                    relevance_rating=RelevanceRating.UNKNOWN,
                    confidence_score=0.0,
                    reasoning="Unexpected error happened - unable to determine relevance",
                    file_source="",
                )
            )
            for res, paper in zip(results, papers)
        ]

        for i, (paper, result) in enumerate(zip(papers, results)):
            self.logger.info(
                f"Paper {i + 1}/{len(papers)}: {result.relevance_rating.value} - {paper.title} - {result.reasoning or 'No reasoning provided'}"
            )

        return results

    async def judge_single_paper_with_retry(self, paper: Paper) -> PaperRelevanceResult:
        """Judge a single paper with retry logic for robustness"""
        for attempt in range(self.config.llm.max_retries):
            try:
                prompt = self.create_relevance_prompt(paper)
                assert self.client

                response = await self.client.chat(
                    model=self.config.llm.model_name,
                    messages=[{"role": "user", "content": prompt}],
                )

                response_text = response.message.content or "<empty/>"
                rating, confidence, reasoning = self.parse_llm_response(response_text)

                # If we get here, pydantic validation passed, so we have a valid response
                return PaperRelevanceResult(
                    title=paper.title,
                    authors=paper.authors,
                    conference=paper.conference_name,
                    year=paper.publication_year,
                    relevance_rating=rating,
                    confidence_score=confidence,
                    reasoning=reasoning,
                    file_source="",  # Will be set by the paper loader
                )

            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1} failed: {e}")

                # Only log response details if response_text is available
                if "response_text" in locals():
                    self.logger.debug(f"Full LLM response: {response_text!r}")
                    self.logger.debug(f"Response length: {len(response_text)} chars")
                    self.logger.debug(f"First 500 chars: {response_text[:500]}")
                else:
                    self.logger.debug("Error occurred before getting LLM response")

                if attempt < self.config.llm.max_retries - 1:
                    self.logger.info(
                        f"Retrying in {self.config.llm.retry_delay} seconds..."
                    )
                    time.sleep(self.config.llm.retry_delay)
                else:
                    self.logger.error(
                        "All attempts failed, marking as UNKNOWN relevance"
                    )

        # Fallback: return unknown rating if all attempts failed
        return PaperRelevanceResult(
            title=paper.title,
            authors=paper.authors,
            conference=paper.conference_name,
            year=paper.publication_year,
            relevance_rating=RelevanceRating.UNKNOWN,
            confidence_score=0.0,
            reasoning="Failed to get valid LLM response after multiple attempts - unable to determine relevance",
            file_source="",
        )
