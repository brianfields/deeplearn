"""
Search policies for topic catalog.

This module contains business rules and policies for topic search and filtering.
"""

from typing import Any

from ..entities.topic_summary import TopicSummary


class SearchPolicy:
    """
    Business rules and policies for topic search and discovery.

    This class encapsulates the business logic for filtering, ranking,
    and organizing topics for optimal discovery experience.
    """

    # Search configuration
    MAX_SEARCH_RESULTS = 100
    DEFAULT_SEARCH_LIMIT = 20
    MIN_QUERY_LENGTH = 2

    # Ranking weights
    TITLE_MATCH_WEIGHT = 3.0
    CORE_CONCEPT_WEIGHT = 2.0
    KEY_CONCEPT_WEIGHT = 1.5
    LEARNING_OBJECTIVE_WEIGHT = 1.0

    @classmethod
    def apply_filters(
        cls,
        topics: list[TopicSummary],
        query: str | None = None,
        user_level: str | None = None,
        min_duration: int | None = None,
        max_duration: int | None = None,
        ready_only: bool | None = None,
        component_count_min: int | None = None,
    ) -> list[TopicSummary]:
        """
        Apply search filters to a list of topics.

        Args:
            topics: List of topics to filter
            query: Text search query
            user_level: Filter by user level
            min_duration: Minimum duration in minutes
            max_duration: Maximum duration in minutes
            ready_only: Filter by readiness status
            component_count_min: Minimum number of components

        Returns:
            Filtered list of topics
        """
        filtered_topics = topics.copy()

        # Apply text search filter
        if query and len(query.strip()) >= cls.MIN_QUERY_LENGTH:
            filtered_topics = cls._filter_by_query(filtered_topics, query)

        # Apply user level filter
        if user_level:
            filtered_topics = cls._filter_by_user_level(filtered_topics, user_level)

        # Apply duration filters
        if min_duration is not None or max_duration is not None:
            filtered_topics = cls._filter_by_duration(filtered_topics, min_duration, max_duration)

        # Apply readiness filter
        if ready_only is True:
            filtered_topics = [topic for topic in filtered_topics if topic.is_ready_for_learning]

        # Apply component count filter
        if component_count_min is not None:
            filtered_topics = cls._filter_by_component_count(filtered_topics, component_count_min)

        return filtered_topics

    @classmethod
    def _filter_by_query(cls, topics: list[TopicSummary], query: str) -> list[TopicSummary]:
        """Filter topics by search query."""
        query_lower = query.lower().strip()
        matching_topics = []

        for topic in topics:
            if cls._matches_query(topic, query_lower):
                matching_topics.append(topic)

        return matching_topics

    @classmethod
    def _matches_query(cls, topic: TopicSummary, query_lower: str) -> bool:
        """Check if a topic matches a search query."""
        return query_lower in topic.title.lower() or query_lower in topic.core_concept.lower() or any(query_lower in concept.lower() for concept in topic.key_concepts) or any(query_lower in obj.lower() for obj in topic.learning_objectives)

    @classmethod
    def _filter_by_user_level(cls, topics: list[TopicSummary], user_level: str) -> list[TopicSummary]:
        """Filter topics by user level with exact matching."""
        return [topic for topic in topics if topic.user_level == user_level]

    @classmethod
    def _filter_by_duration(cls, topics: list[TopicSummary], min_duration: int | None, max_duration: int | None) -> list[TopicSummary]:
        """Filter topics by duration range."""
        filtered_topics = []

        for topic in topics:
            duration = topic.estimated_duration
            if min_duration is not None and duration < min_duration:
                continue
            if max_duration is not None and duration > max_duration:
                continue
            filtered_topics.append(topic)

        return filtered_topics

    @classmethod
    def _filter_by_readiness(cls, topics: list[TopicSummary], ready_only: bool) -> list[TopicSummary]:
        """Filter topics by readiness status."""
        return [topic for topic in topics if topic.is_ready_for_learning == ready_only]

    @classmethod
    def _filter_by_component_count(cls, topics: list[TopicSummary], min_count: int) -> list[TopicSummary]:
        """Filter topics by minimum component count."""
        return [topic for topic in topics if topic.component_count >= min_count]

    @classmethod
    def rank_search_results(cls, topics: list[TopicSummary], query: str) -> list[TopicSummary]:
        """
        Rank search results by relevance.

        Args:
            topics: List of topics to rank
            query: Original search query

        Returns:
            Topics sorted by relevance score (highest first)
        """
        if not query or len(query.strip()) < cls.MIN_QUERY_LENGTH:
            # No query - sort by readiness and recency
            return cls._sort_by_default_criteria(topics)

        query_lower = query.lower().strip()
        scored_topics = []

        for topic in topics:
            score = cls._calculate_relevance_score(topic, query_lower)
            scored_topics.append((topic, score))

        # Sort by score (descending) and return topics
        scored_topics.sort(key=lambda x: x[1], reverse=True)
        return [topic for topic, _ in scored_topics]

    @classmethod
    def _calculate_relevance_score(cls, topic: TopicSummary, query_lower: str) -> float:
        """Calculate relevance score for a topic given a query."""
        score = 0.0

        # Title match (highest weight)
        if query_lower in topic.title.lower():
            score += cls.TITLE_MATCH_WEIGHT
            # Bonus for exact title match
            if query_lower == topic.title.lower():
                score += 2.0

        # Core concept match
        if query_lower in topic.core_concept.lower():
            score += cls.CORE_CONCEPT_WEIGHT

        # Key concepts match
        for concept in topic.key_concepts:
            if query_lower in concept.lower():
                score += cls.KEY_CONCEPT_WEIGHT
                # Bonus for exact concept match
                if query_lower == concept.lower():
                    score += 0.5

        # Learning objectives match
        for objective in topic.learning_objectives:
            if query_lower in objective.lower():
                score += cls.LEARNING_OBJECTIVE_WEIGHT

        # Boost ready topics
        if topic.is_ready_for_learning:
            score += 0.5

        # Boost topics with more components
        score += min(topic.component_count * 0.1, 1.0)

        return score

    @classmethod
    def _sort_by_default_criteria(cls, topics: list[TopicSummary]) -> list[TopicSummary]:
        """Sort topics by default criteria when no search query."""
        return sorted(
            topics,
            key=lambda t: (
                -int(t.is_ready_for_learning),  # Ready topics first (negative for desc)
                -t.component_count,  # More components first
                t.user_level,  # Beginner first
                t.title.lower(),  # Alphabetical by title
            ),
        )

    @classmethod
    def get_search_suggestions(cls, topics: list[TopicSummary], query: str) -> list[str]:
        """
        Get search suggestions based on existing topics.

        Args:
            topics: Available topics
            query: Partial search query

        Returns:
            List of suggested search terms
        """
        if not query or len(query.strip()) < 2:
            return []

        query_lower = query.lower().strip()
        suggestions = set()

        for topic in topics:
            # Suggest titles that start with the query
            if topic.title.lower().startswith(query_lower):
                suggestions.add(topic.title)

            # Suggest key concepts that contain the query
            for concept in topic.key_concepts:
                if query_lower in concept.lower():
                    suggestions.add(concept)

        # Return sorted suggestions, limited to reasonable number
        return sorted(list(suggestions))[:10]

    @classmethod
    def get_popular_topics(cls, topics: list[TopicSummary], limit: int = 10) -> list[TopicSummary]:
        """
        Get popular topics for discovery.

        Args:
            topics: Available topics
            limit: Maximum number of topics to return

        Returns:
            List of popular topics
        """
        # For now, popularity is based on readiness and component count
        # In the future, this could include actual usage metrics
        popular_topics = sorted(
            topics,
            key=lambda t: (
                -int(t.is_ready_for_learning),  # Ready topics first
                -t.component_count,  # More components = more popular
                -len(t.learning_objectives),  # More objectives = more comprehensive
            ),
        )

        return popular_topics[:limit]

    @classmethod
    def get_recommended_topics(cls, topics: list[TopicSummary], user_level: str, completed_topics: list[str] | None = None, limit: int = 5) -> list[TopicSummary]:
        """
        Get recommended topics for a user.

        Args:
            topics: Available topics
            user_level: User's skill level
            completed_topics: List of completed topic IDs
            limit: Maximum number of recommendations

        Returns:
            List of recommended topics
        """
        completed_set = set(completed_topics or [])

        # Filter out completed topics and apply user level filter
        available_topics = [topic for topic in topics if topic.id not in completed_set and topic.is_suitable_for_user_level(user_level)]

        # Prioritize ready topics at appropriate level
        recommended = sorted(
            available_topics,
            key=lambda t: (
                -int(t.is_ready_for_learning),  # Ready topics first
                abs(cls._get_level_number(t.user_level) - cls._get_level_number(user_level)),  # Close to user level
                -t.component_count,  # More components
            ),
        )

        return recommended[:limit]

    @classmethod
    def _get_level_number(cls, level: str) -> int:
        """Convert user level to number for comparison."""
        level_map = {"beginner": 1, "intermediate": 2, "advanced": 3}
        return level_map.get(level, 2)

    @classmethod
    def validate_search_parameters(
        cls,
        query: str | None = None,
        user_level: str | None = None,
        min_duration: int | None = None,
        max_duration: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict[str, Any]:
        """
        Validate and normalize search parameters.

        Args:
            query: Search query
            user_level: User level filter
            min_duration: Minimum duration
            max_duration: Maximum duration
            limit: Result limit
            offset: Result offset

        Returns:
            Dictionary of validated parameters

        Raises:
            ValueError: If parameters are invalid
        """
        validated = {}

        # Validate query
        if query is not None:
            query = query.strip()
            if len(query) < cls.MIN_QUERY_LENGTH:
                query = None
            validated["query"] = query

        # Validate user level
        if user_level is not None:
            if user_level not in ["beginner", "intermediate", "advanced"]:
                raise ValueError("User level must be beginner, intermediate, or advanced")
            validated["user_level"] = user_level

        # Validate duration
        if min_duration is not None:
            if min_duration < 0:
                raise ValueError("Minimum duration cannot be negative")
            validated["min_duration"] = min_duration

        if max_duration is not None:
            if max_duration < 0:
                raise ValueError("Maximum duration cannot be negative")
            if min_duration is not None and max_duration < min_duration:
                raise ValueError("Maximum duration cannot be less than minimum duration")
            validated["max_duration"] = max_duration

        # Validate pagination
        if limit is not None:
            if limit <= 0:
                raise ValueError("Limit must be positive")
            limit = min(limit, cls.MAX_SEARCH_RESULTS)
            validated["limit"] = limit
        else:
            validated["limit"] = cls.DEFAULT_SEARCH_LIMIT

        if offset is not None:
            if offset < 0:
                raise ValueError("Offset cannot be negative")
            validated["offset"] = offset
        else:
            validated["offset"] = 0

        return validated

    def sort_by_relevance(self, topics: list[TopicSummary], query: str | None = None) -> list[TopicSummary]:
        """
        Sort topics by relevance (component count descending, with query boost if provided).

        Args:
            topics: List of topics to sort
            query: Optional search query for boosting

        Returns:
            Sorted list of topics
        """
        if query:
            return self.rank_search_results(topics, query)
        else:
            # Sort by component count descending as default relevance
            return sorted(topics, key=lambda t: t.component_count, reverse=True)

    def sort_by_duration(self, topics: list[TopicSummary], ascending: bool = True) -> list[TopicSummary]:
        """
        Sort topics by estimated duration.

        Args:
            topics: List of topics to sort
            ascending: If True, sort ascending; if False, sort descending

        Returns:
            Sorted list of topics
        """
        return sorted(topics, key=lambda t: t.estimated_duration, reverse=not ascending)

    def sort_by_user_level(self, topics: list[TopicSummary]) -> list[TopicSummary]:
        """
        Sort topics by user level (beginner -> intermediate -> advanced).

        Args:
            topics: List of topics to sort

        Returns:
            Sorted list of topics
        """
        level_order = {"beginner": 0, "intermediate": 1, "advanced": 2}
        return sorted(topics, key=lambda t: level_order.get(t.user_level, 1))

    def apply_pagination(self, topics: list[TopicSummary], limit: int | None = None, offset: int = 0) -> list[TopicSummary]:
        """
        Apply pagination to topics list.

        Args:
            topics: List of topics to paginate
            limit: Maximum number of topics to return (None for no limit)
            offset: Number of topics to skip

        Returns:
            Paginated list of topics
        """
        if offset > 0:
            topics = topics[offset:]

        if limit is not None:
            topics = topics[:limit]

        return topics

    def is_valid_user_level(self, user_level: str | None) -> bool:
        """
        Check if user level is valid.

        Args:
            user_level: User level to validate

        Returns:
            True if valid, False otherwise
        """
        if user_level is None:
            return False
        return user_level in ["beginner", "intermediate", "advanced"]

    def get_user_level_priority(self, user_level: str) -> int:
        """
        Get priority number for user level (for sorting).

        Args:
            user_level: User level

        Returns:
            Priority number (0 = highest priority)
        """
        level_priority = {"beginner": 0, "intermediate": 1, "advanced": 2}
        return level_priority.get(user_level, 1)

    def calculate_relevance_score(self, topic: TopicSummary, query: str | None = None) -> float:
        """
        Calculate relevance score for a topic.

        Args:
            topic: Topic to score
            query: Optional search query for boosting

        Returns:
            Relevance score (higher = more relevant)
        """
        # Base score from component count
        score = float(topic.component_count)

        # Query boost
        if query and topic.matches_query(query):
            score += 10.0  # Boost for query matches

        return score
