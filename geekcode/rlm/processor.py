"""
GeekCode RLM Processor - Document processing with semantic understanding.

This module provides RLM (Recursive Language Model) processing for
complex documents, including semantic TOC building, section navigation,
and override/negation detection.
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path


@dataclass
class DocumentSection:
    """Represents a section in a document."""

    title: str
    level: int
    content: str
    start_position: int
    end_position: int
    children: List["DocumentSection"] = field(default_factory=list)
    parent: Optional["DocumentSection"] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert section to dictionary."""
        return {
            "title": self.title,
            "level": self.level,
            "content_preview": self.content[:200] + "..." if len(self.content) > 200 else self.content,
            "start_position": self.start_position,
            "end_position": self.end_position,
            "children": [c.to_dict() for c in self.children],
            "metadata": self.metadata,
        }


@dataclass
class Citation:
    """Represents a citation to a document section."""

    section_title: str
    page: Optional[int]
    position: int
    quote: str
    confidence: float


@dataclass
class ProcessingResult:
    """Result from RLM processing."""

    answer: str
    citations: List[Citation]
    sections_used: List[str]
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class RLMProcessor:
    """
    RLM Processor for semantic document analysis.

    Provides:
    - Document loading and parsing
    - Semantic TOC (Table of Contents) building
    - Section navigation
    - Override and negation detection
    - Structured answers with citations

    Example:
        >>> processor = RLMProcessor()
        >>> processor.load_document("policy.md")
        >>> result = processor.query("What are the coverage limits?")
    """

    # Patterns for detecting section headers
    MARKDOWN_HEADER_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
    NUMBERED_HEADER_PATTERN = re.compile(r"^(\d+(?:\.\d+)*)\s+(.+)$", re.MULTILINE)

    # Patterns for override/negation detection
    OVERRIDE_PATTERNS = [
        r"notwithstanding\s+(?:the\s+)?(?:foregoing|above|previous)",
        r"supersedes?\s+(?:any\s+)?(?:prior|previous|earlier)",
        r"takes?\s+precedence\s+over",
        r"overrides?\s+(?:any\s+)?(?:other|conflicting)",
        r"except\s+as\s+(?:otherwise\s+)?(?:provided|stated|specified)",
        r"in\s+lieu\s+of",
    ]

    NEGATION_PATTERNS = [
        r"does\s+not\s+(?:apply|include|cover)",
        r"shall\s+not\s+(?:be|include|apply)",
        r"exclud(?:es?|ing)\s+(?:from|any)",
        r"is\s+not\s+(?:covered|included|applicable)",
        r"except\s+(?:for|that|when|where)",
        r"unless\s+(?:otherwise|specifically|expressly)",
    ]

    def __init__(self):
        """Initialize the RLM Processor."""
        self.document: Optional[str] = None
        self.sections: List[DocumentSection] = []
        self.toc: List[DocumentSection] = []
        self._section_index: Dict[str, DocumentSection] = {}

    def load_document(self, path: str) -> None:
        """
        Load a document from file.

        Args:
            path: Path to the document file.
        """
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {path}")

        self.document = file_path.read_text()
        self._build_structure()

    def load_text(self, text: str) -> None:
        """
        Load document from text string.

        Args:
            text: The document text.
        """
        self.document = text
        self._build_structure()

    def _build_structure(self) -> None:
        """Build the document structure (TOC and sections)."""
        if not self.document:
            return

        self.sections = []
        self.toc = []
        self._section_index = {}

        # Find all headers
        headers = self._find_headers()

        # Build section tree
        current_position = 0
        section_stack: List[DocumentSection] = []

        for header_match, level, title in headers:
            start_pos = header_match.start()

            # Close previous section
            if section_stack:
                section_stack[-1].end_position = start_pos
                section_stack[-1].content = self.document[
                    section_stack[-1].start_position : start_pos
                ].strip()

            # Create new section
            section = DocumentSection(
                title=title,
                level=level,
                content="",
                start_position=start_pos,
                end_position=len(self.document),
            )

            # Find parent
            while section_stack and section_stack[-1].level >= level:
                section_stack.pop()

            if section_stack:
                section.parent = section_stack[-1]
                section_stack[-1].children.append(section)
            else:
                self.toc.append(section)

            section_stack.append(section)
            self.sections.append(section)
            self._section_index[title.lower()] = section

        # Close last section
        if section_stack:
            section_stack[-1].end_position = len(self.document)
            section_stack[-1].content = self.document[
                section_stack[-1].start_position :
            ].strip()

    def _find_headers(self) -> List[Tuple[re.Match, int, str]]:
        """Find all headers in the document."""
        headers = []

        # Markdown headers
        for match in self.MARKDOWN_HEADER_PATTERN.finditer(self.document):
            level = len(match.group(1))
            title = match.group(2).strip()
            headers.append((match, level, title))

        # Numbered headers (e.g., "1.2.3 Section Title")
        for match in self.NUMBERED_HEADER_PATTERN.finditer(self.document):
            # Count dots to determine level
            numbering = match.group(1)
            level = numbering.count(".") + 1
            title = f"{numbering} {match.group(2).strip()}"
            headers.append((match, level, title))

        # Sort by position
        headers.sort(key=lambda x: x[0].start())
        return headers

    def get_toc(self) -> List[Dict[str, Any]]:
        """
        Get the document table of contents.

        Returns:
            List of section dictionaries with nested structure.
        """
        return [section.to_dict() for section in self.toc]

    def get_section(self, title: str) -> Optional[DocumentSection]:
        """
        Get a section by title.

        Args:
            title: The section title (case-insensitive).

        Returns:
            DocumentSection if found, None otherwise.
        """
        return self._section_index.get(title.lower())

    def find_sections(self, query: str) -> List[DocumentSection]:
        """
        Find sections matching a query.

        Args:
            query: Search query for section titles/content.

        Returns:
            List of matching sections.
        """
        query_lower = query.lower()
        matches = []

        for section in self.sections:
            if query_lower in section.title.lower():
                matches.append(section)
            elif query_lower in section.content.lower():
                matches.append(section)

        return matches

    def detect_overrides(self) -> List[Tuple[int, str, str]]:
        """
        Detect override clauses in the document.

        Returns:
            List of (position, matched_text, pattern_type) tuples.
        """
        if not self.document:
            return []

        overrides = []
        for pattern in self.OVERRIDE_PATTERNS:
            for match in re.finditer(pattern, self.document, re.IGNORECASE):
                # Get surrounding context
                start = max(0, match.start() - 50)
                end = min(len(self.document), match.end() + 50)
                context = self.document[start:end]

                overrides.append((match.start(), match.group(), "override"))

        return overrides

    def detect_negations(self) -> List[Tuple[int, str, str]]:
        """
        Detect negation clauses in the document.

        Returns:
            List of (position, matched_text, pattern_type) tuples.
        """
        if not self.document:
            return []

        negations = []
        for pattern in self.NEGATION_PATTERNS:
            for match in re.finditer(pattern, self.document, re.IGNORECASE):
                negations.append((match.start(), match.group(), "negation"))

        return negations

    def query(
        self,
        question: str,
        include_citations: bool = True,
    ) -> ProcessingResult:
        """
        Query the document with a question.

        Args:
            question: The question to answer.
            include_citations: Whether to include citations.

        Returns:
            ProcessingResult with answer and citations.
        """
        if not self.document:
            return ProcessingResult(
                answer="No document loaded.",
                citations=[],
                sections_used=[],
                confidence=0.0,
            )

        # Find relevant sections
        relevant_sections = self.find_sections(question)

        if not relevant_sections:
            # Fall back to searching the whole document
            if question.lower() in self.document.lower():
                return ProcessingResult(
                    answer="Information found in document. Please refine your query for specific sections.",
                    citations=[],
                    sections_used=[],
                    confidence=0.5,
                )
            return ProcessingResult(
                answer="No relevant information found.",
                citations=[],
                sections_used=[],
                confidence=0.0,
            )

        # Build answer from relevant sections
        answer_parts = []
        citations = []
        sections_used = []

        for section in relevant_sections[:3]:  # Limit to top 3 sections
            sections_used.append(section.title)

            # Extract relevant quote
            quote = section.content[:300].strip()
            if len(section.content) > 300:
                quote += "..."

            answer_parts.append(f"**{section.title}**: {quote}")

            if include_citations:
                citations.append(
                    Citation(
                        section_title=section.title,
                        page=None,  # Would need page info from PDF
                        position=section.start_position,
                        quote=quote,
                        confidence=0.8,
                    )
                )

        answer = "\n\n".join(answer_parts)

        return ProcessingResult(
            answer=answer,
            citations=citations,
            sections_used=sections_used,
            confidence=0.8 if relevant_sections else 0.3,
        )

    def navigate_to(self, section_path: str) -> Optional[str]:
        """
        Navigate to a section by path (e.g., "Chapter 1 > Section 2").

        Args:
            section_path: Path to the section separated by ">".

        Returns:
            Section content if found, None otherwise.
        """
        parts = [p.strip() for p in section_path.split(">")]

        current_sections = self.toc
        target_section = None

        for part in parts:
            part_lower = part.lower()
            found = False

            for section in current_sections:
                if part_lower in section.title.lower():
                    target_section = section
                    current_sections = section.children
                    found = True
                    break

            if not found:
                return None

        return target_section.content if target_section else None
