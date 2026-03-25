"""Feedback Storage System for ITC Form Generator.

Stores user feedback on generated forms and provides context for AI
to improve future form generation based on learned patterns.
"""

import json
import os
import time
import logging
from dataclasses import dataclass, asdict
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Default feedback storage location
DEFAULT_FEEDBACK_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    'feedback_data.json'
)


@dataclass
class FeedbackEntry:
    """A single feedback entry from a user."""
    id: str
    timestamp: float
    system_type: str  # e.g., "AHU", "Chiller", "FCU", etc.
    system_name: str
    form_type: str  # e.g., "ITC", "PFI", "FPT"
    section_name: Optional[str]  # Specific section if applicable
    check_item_id: Optional[str]  # Specific check item if applicable
    check_item_description: Optional[str]
    feedback_type: str  # "positive", "negative", "suggestion", "correction"
    feedback_text: str
    suggested_improvement: Optional[str]
    user_id: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'FeedbackEntry':
        return cls(**data)


class FeedbackStore:
    """Persistent storage for user feedback on generated forms.

    Feedback is used to:
    1. Track common issues with generated forms
    2. Provide context to AI for improved generation
    3. Learn patterns about what works well for different system types
    """

    def __init__(self, storage_path: Optional[str] = None):
        """Initialize feedback store.

        Args:
            storage_path: Path to JSON file for storing feedback.
                         Uses default location if not specified.
        """
        self.storage_path = storage_path or DEFAULT_FEEDBACK_FILE
        self._feedback: list[FeedbackEntry] = []
        self._load()

    def _load(self) -> None:
        """Load feedback from storage file."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._feedback = [
                        FeedbackEntry.from_dict(entry)
                        for entry in data.get('feedback', [])
                    ]
                logger.info(f"Loaded {len(self._feedback)} feedback entries")
            except Exception as e:
                logger.error(f"Failed to load feedback: {e}")
                self._feedback = []
        else:
            self._feedback = []

    def _save(self) -> None:
        """Save feedback to storage file."""
        try:
            # Ensure directory exists
            Path(self.storage_path).parent.mkdir(parents=True, exist_ok=True)

            data = {
                'version': '1.0',
                'last_updated': time.time(),
                'feedback_count': len(self._feedback),
                'feedback': [entry.to_dict() for entry in self._feedback]
            }

            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Saved {len(self._feedback)} feedback entries")
        except Exception as e:
            logger.error(f"Failed to save feedback: {e}")

    def add_feedback(self, feedback: FeedbackEntry) -> None:
        """Add a new feedback entry.

        Args:
            feedback: FeedbackEntry to add
        """
        self._feedback.append(feedback)
        self._save()
        logger.info(f"Added feedback: {feedback.feedback_type} for {feedback.system_type}")

    def get_feedback_for_system_type(self, system_type: str, limit: int = 10) -> list[FeedbackEntry]:
        """Get recent feedback for a specific system type.

        Args:
            system_type: Type of system (e.g., "AHU", "Chiller")
            limit: Maximum number of entries to return

        Returns:
            List of relevant feedback entries, most recent first
        """
        # Normalize system type for matching
        system_type_lower = system_type.lower()

        relevant = [
            entry for entry in self._feedback
            if system_type_lower in entry.system_type.lower() or
               system_type_lower in entry.system_name.lower()
        ]

        # Sort by timestamp, most recent first
        relevant.sort(key=lambda x: x.timestamp, reverse=True)

        return relevant[:limit]

    def get_feedback_for_section(self, section_name: str, limit: int = 5) -> list[FeedbackEntry]:
        """Get feedback related to a specific form section.

        Args:
            section_name: Name of the section
            limit: Maximum number of entries to return

        Returns:
            List of relevant feedback entries
        """
        section_lower = section_name.lower()

        relevant = [
            entry for entry in self._feedback
            if entry.section_name and section_lower in entry.section_name.lower()
        ]

        relevant.sort(key=lambda x: x.timestamp, reverse=True)
        return relevant[:limit]

    def get_all_feedback(self, limit: int = 50) -> list[FeedbackEntry]:
        """Get all feedback entries.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of all feedback entries, most recent first
        """
        sorted_feedback = sorted(
            self._feedback,
            key=lambda x: x.timestamp,
            reverse=True
        )
        return sorted_feedback[:limit]

    def get_improvement_suggestions(self, system_type: str) -> list[str]:
        """Get improvement suggestions for a system type.

        Args:
            system_type: Type of system

        Returns:
            List of suggested improvements
        """
        feedback = self.get_feedback_for_system_type(system_type, limit=20)

        suggestions = []
        for entry in feedback:
            if entry.suggested_improvement:
                suggestions.append(entry.suggested_improvement)
            if entry.feedback_type in ['suggestion', 'correction'] and entry.feedback_text:
                suggestions.append(entry.feedback_text)

        return suggestions[:10]  # Return top 10 suggestions

    def get_positive_patterns(self, system_type: str) -> list[str]:
        """Get positive feedback patterns for a system type.

        These represent things that work well and should be continued.

        Args:
            system_type: Type of system

        Returns:
            List of positive feedback descriptions
        """
        feedback = self.get_feedback_for_system_type(system_type, limit=20)

        positive = [
            entry.feedback_text
            for entry in feedback
            if entry.feedback_type == 'positive' and entry.feedback_text
        ]

        return positive[:5]

    def get_negative_patterns(self, system_type: str) -> list[str]:
        """Get negative feedback patterns to avoid.

        Args:
            system_type: Type of system

        Returns:
            List of issues to avoid
        """
        feedback = self.get_feedback_for_system_type(system_type, limit=20)

        negative = [
            entry.feedback_text
            for entry in feedback
            if entry.feedback_type == 'negative' and entry.feedback_text
        ]

        return negative[:5]

    def generate_ai_context(self, system_type: str, system_name: str) -> str:
        """Generate context string for AI prompts based on feedback.

        This context helps the AI learn from past feedback to generate
        better forms.

        Args:
            system_type: Type of system
            system_name: Name of the specific system

        Returns:
            Formatted context string for AI prompts
        """
        positive = self.get_positive_patterns(system_type)
        negative = self.get_negative_patterns(system_type)
        suggestions = self.get_improvement_suggestions(system_type)

        if not positive and not negative and not suggestions:
            return ""

        context_parts = [
            f"\n--- LEARNED FEEDBACK FOR {system_type.upper()} SYSTEMS ---"
        ]

        if positive:
            context_parts.append("\nThings that work well (continue doing):")
            for i, item in enumerate(positive, 1):
                context_parts.append(f"  {i}. {item}")

        if negative:
            context_parts.append("\nIssues to avoid:")
            for i, item in enumerate(negative, 1):
                context_parts.append(f"  {i}. {item}")

        if suggestions:
            context_parts.append("\nSuggested improvements:")
            for i, item in enumerate(suggestions, 1):
                context_parts.append(f"  {i}. {item}")

        context_parts.append("--- END FEEDBACK ---\n")

        return "\n".join(context_parts)

    def get_stats(self) -> dict:
        """Get statistics about stored feedback.

        Returns:
            Dict with feedback statistics
        """
        if not self._feedback:
            return {
                'total_entries': 0,
                'by_type': {},
                'by_system': {},
                'recent_count': 0
            }

        # Count by feedback type
        by_type = {}
        for entry in self._feedback:
            by_type[entry.feedback_type] = by_type.get(entry.feedback_type, 0) + 1

        # Count by system type
        by_system = {}
        for entry in self._feedback:
            by_system[entry.system_type] = by_system.get(entry.system_type, 0) + 1

        # Count recent (last 7 days)
        week_ago = time.time() - (7 * 24 * 60 * 60)
        recent_count = sum(1 for e in self._feedback if e.timestamp > week_ago)

        return {
            'total_entries': len(self._feedback),
            'by_type': by_type,
            'by_system': by_system,
            'recent_count': recent_count
        }


# Global feedback store instance
_feedback_store: Optional[FeedbackStore] = None


def get_feedback_store() -> FeedbackStore:
    """Get the global feedback store instance.

    Returns:
        FeedbackStore instance
    """
    global _feedback_store
    if _feedback_store is None:
        _feedback_store = FeedbackStore()
    return _feedback_store


def create_feedback_entry(
    system_type: str,
    system_name: str,
    form_type: str,
    feedback_type: str,
    feedback_text: str,
    section_name: Optional[str] = None,
    check_item_id: Optional[str] = None,
    check_item_description: Optional[str] = None,
    suggested_improvement: Optional[str] = None,
    user_id: Optional[str] = None
) -> FeedbackEntry:
    """Create a new feedback entry with auto-generated ID and timestamp.

    Args:
        system_type: Type of system (e.g., "AHU")
        system_name: Name of the system
        form_type: Type of form
        feedback_type: Type of feedback (positive/negative/suggestion/correction)
        feedback_text: The actual feedback text
        section_name: Optional section name
        check_item_id: Optional check item ID
        check_item_description: Optional check item description
        suggested_improvement: Optional suggested improvement
        user_id: Optional user identifier

    Returns:
        New FeedbackEntry instance
    """
    import uuid

    return FeedbackEntry(
        id=str(uuid.uuid4())[:8],
        timestamp=time.time(),
        system_type=system_type,
        system_name=system_name,
        form_type=form_type,
        section_name=section_name,
        check_item_id=check_item_id,
        check_item_description=check_item_description,
        feedback_type=feedback_type,
        feedback_text=feedback_text,
        suggested_improvement=suggested_improvement,
        user_id=user_id
    )
