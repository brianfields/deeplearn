"""
Unit tests for Topic Catalog domain entities.

These tests focus on domain logic and entity behavior.
"""

from datetime import UTC, datetime

import pytest

from modules.topic_catalog.domain.entities.catalog import Catalog, InvalidCatalogError
from modules.topic_catalog.domain.entities.topic_summary import InvalidTopicSummaryError, TopicSummary


class TestTopicSummary:
    """Test cases for TopicSummary entity."""

    def test_create_topic_summary_success(self):
        """Test successful topic summary creation."""
        # Arrange & Act
        topic = TopicSummary(
            topic_id="topic_123",
            title="Python Variables",
            core_concept="Understanding variable declaration and usage",
            user_level="beginner",
            learning_objectives=["Declare variables", "Assign values", "Use different data types"],
            key_concepts=["variable", "assignment", "data type"],
            estimated_duration=15,
            component_count=3,
            is_ready_for_learning=True,
        )

        # Assert
        assert topic.topic_id == "topic_123"
        assert topic.title == "Python Variables"
        assert topic.core_concept == "Understanding variable declaration and usage"
        assert topic.user_level == "beginner"
        assert len(topic.learning_objectives) == 3
        assert len(topic.key_concepts) == 3
        assert topic.estimated_duration == 15
        assert topic.component_count == 3
        assert topic.is_ready_for_learning is True

    def test_topic_summary_validation_empty_title(self):
        """Test topic summary validation with empty title."""
        with pytest.raises(InvalidTopicSummaryError, match="Topic title cannot be empty"):
            TopicSummary(
                topic_id="topic_123",
                title="",
                core_concept="Some concept",
                user_level="beginner",
                learning_objectives=["Learn something"],
                key_concepts=["concept"],
                estimated_duration=15,
                component_count=3,
                is_ready_for_learning=True,
            )

    def test_topic_summary_validation_empty_core_concept(self):
        """Test topic summary validation with empty core concept."""
        with pytest.raises(InvalidTopicSummaryError, match="Core concept cannot be empty"):
            TopicSummary(
                topic_id="topic_123",
                title="Python Variables",
                core_concept="",
                user_level="beginner",
                learning_objectives=["Learn something"],
                key_concepts=["concept"],
                estimated_duration=15,
                component_count=3,
                is_ready_for_learning=True,
            )

    def test_topic_summary_validation_invalid_user_level(self):
        """Test topic summary validation with invalid user level."""
        with pytest.raises(InvalidTopicSummaryError, match="User level must be beginner, intermediate, or advanced"):
            TopicSummary(
                topic_id="topic_123",
                title="Python Variables",
                core_concept="Some concept",
                user_level="expert",  # Invalid level
                learning_objectives=["Learn something"],
                key_concepts=["concept"],
                estimated_duration=15,
                component_count=3,
                is_ready_for_learning=True,
            )

    def test_topic_summary_validation_empty_learning_objectives(self):
        """Test topic summary allows empty learning objectives."""
        # This should not raise an error - empty learning objectives are allowed
        topic = TopicSummary(
            topic_id="topic_123",
            title="Python Variables",
            core_concept="Some concept",
            user_level="beginner",
            learning_objectives=[],
            key_concepts=["concept"],
            estimated_duration=15,
            component_count=3,
            is_ready_for_learning=True,
        )
        assert topic.learning_objectives == []

    def test_topic_summary_validation_empty_key_concepts(self):
        """Test topic summary allows empty key concepts."""
        # This should not raise an error - empty key concepts are allowed
        topic = TopicSummary(
            topic_id="topic_123",
            title="Python Variables",
            core_concept="Some concept",
            user_level="beginner",
            learning_objectives=["Learn something"],
            key_concepts=[],
            estimated_duration=15,
            component_count=3,
            is_ready_for_learning=True,
        )
        assert topic.key_concepts == []

    def test_topic_summary_validation_negative_duration(self):
        """Test topic summary validation with negative duration."""
        with pytest.raises(InvalidTopicSummaryError, match="Estimated duration cannot be negative"):
            TopicSummary(
                topic_id="topic_123",
                title="Python Variables",
                core_concept="Some concept",
                user_level="beginner",
                learning_objectives=["Learn something"],
                key_concepts=["concept"],
                estimated_duration=-5,
                component_count=3,
                is_ready_for_learning=True,
            )

    def test_topic_summary_validation_negative_component_count(self):
        """Test topic summary validation with negative component count."""
        with pytest.raises(InvalidTopicSummaryError, match="Component count cannot be negative"):
            TopicSummary(
                topic_id="topic_123",
                title="Python Variables",
                core_concept="Some concept",
                user_level="beginner",
                learning_objectives=["Learn something"],
                key_concepts=["concept"],
                estimated_duration=15,
                component_count=-1,
                is_ready_for_learning=True,
            )

    def test_topic_summary_matches_query_case_insensitive(self):
        """Test topic summary query matching is case insensitive."""
        # Arrange
        topic = TopicSummary(
            topic_id="topic_123",
            title="Python Variables",
            core_concept="Understanding variable declaration",
            user_level="beginner",
            learning_objectives=["Learn variables"],
            key_concepts=["variable"],
            estimated_duration=15,
            component_count=3,
            is_ready_for_learning=True,
        )

        # Act & Assert
        assert topic.matches_query("python")
        assert topic.matches_query("PYTHON")
        assert topic.matches_query("Variable")
        assert topic.matches_query("declaration")

    def test_topic_summary_matches_query_in_key_concepts(self):
        """Test topic summary query matching in key concepts."""
        # Arrange
        topic = TopicSummary(
            topic_id="topic_123",
            title="Data Structures",
            core_concept="Understanding data organization",
            user_level="intermediate",
            learning_objectives=["Learn structures"],
            key_concepts=["list", "dictionary", "tuple"],
            estimated_duration=30,
            component_count=5,
            is_ready_for_learning=True,
        )

        # Act & Assert
        assert topic.matches_query("list")
        assert topic.matches_query("dictionary")
        assert topic.matches_query("tuple")
        assert not topic.matches_query("array")

    def test_topic_summary_no_match(self):
        """Test topic summary when query doesn't match."""
        # Arrange
        topic = TopicSummary(
            topic_id="topic_123",
            title="Python Variables",
            core_concept="Understanding variable declaration",
            user_level="beginner",
            learning_objectives=["Learn variables"],
            key_concepts=["variable"],
            estimated_duration=15,
            component_count=3,
            is_ready_for_learning=True,
        )

        # Act & Assert
        assert not topic.matches_query("javascript")
        assert not topic.matches_query("function")


class TestCatalog:
    """Test cases for Catalog entity."""

    @pytest.fixture
    def sample_topics(self):
        """Create sample topics for testing."""
        return [
            TopicSummary(
                topic_id="topic_1",
                title="Python Variables",
                core_concept="Variable basics",
                user_level="beginner",
                learning_objectives=["Learn variables"],
                key_concepts=["variable"],
                estimated_duration=15,
                component_count=3,
                is_ready_for_learning=True,
            ),
            TopicSummary(
                topic_id="topic_2",
                title="Python Functions",
                core_concept="Function basics",
                user_level="intermediate",
                learning_objectives=["Learn functions"],
                key_concepts=["function"],
                estimated_duration=25,
                component_count=5,
                is_ready_for_learning=True,
            ),
        ]

    def test_create_catalog_success(self, sample_topics):
        """Test successful catalog creation."""
        # Arrange
        last_updated = datetime.now(UTC)

        # Act
        catalog = Catalog(topics=sample_topics, last_updated=last_updated, total_count=2)

        # Assert
        assert len(catalog.topics) == 2
        assert catalog.last_updated == last_updated
        assert catalog.total_count == 2

    def test_catalog_validation_negative_total_count(self, sample_topics):
        """Test catalog validation with negative total count."""
        with pytest.raises(InvalidCatalogError, match="Total count must be non-negative"):
            Catalog(topics=sample_topics, last_updated=datetime.now(UTC), total_count=-1)

    def test_catalog_filter_by_user_level(self, sample_topics):
        """Test catalog filtering by user level."""
        # Arrange
        catalog = Catalog(topics=sample_topics, last_updated=datetime.now(UTC), total_count=2)

        # Act
        beginner_topics = catalog.filter_by_user_level("beginner")

        # Assert
        assert len(beginner_topics) == 1
        assert beginner_topics[0].user_level == "beginner"
        assert beginner_topics[0].title == "Python Variables"

    def test_catalog_filter_by_readiness(self, sample_topics):
        """Test catalog filtering by readiness."""
        # Arrange
        # Add a not-ready topic
        not_ready_topic = TopicSummary(
            topic_id="topic_3",
            title="Advanced Topic",
            core_concept="Advanced concept",
            user_level="advanced",
            learning_objectives=["Advanced learning"],
            key_concepts=["advanced"],
            estimated_duration=60,
            component_count=10,
            is_ready_for_learning=False,
        )
        all_topics = sample_topics + [not_ready_topic]
        catalog = Catalog(topics=all_topics, last_updated=datetime.now(UTC), total_count=3)

        # Act
        ready_topics = catalog.filter_by_readiness(ready_only=True)
        all_topics_result = catalog.filter_by_readiness(ready_only=False)

        # Assert
        assert len(ready_topics) == 2
        assert all(topic.is_ready_for_learning for topic in ready_topics)
        assert len(all_topics_result) == 3

    def test_catalog_search_topics(self, sample_topics):
        """Test catalog topic search."""
        # Arrange
        catalog = Catalog(topics=sample_topics, last_updated=datetime.now(UTC), total_count=2)

        # Act
        python_topics = catalog.search_topics("Python")
        function_topics = catalog.search_topics("function")
        no_match_topics = catalog.search_topics("javascript")

        # Assert
        assert len(python_topics) == 2  # Both topics contain "Python"
        assert len(function_topics) == 1  # Only one topic contains "function"
        assert function_topics[0].title == "Python Functions"
        assert len(no_match_topics) == 0

    def test_catalog_get_statistics(self, sample_topics):
        """Test catalog statistics generation."""
        # Arrange
        catalog = Catalog(topics=sample_topics, last_updated=datetime.now(UTC), total_count=2)

        # Act
        stats = catalog.get_statistics()

        # Assert
        assert stats["total_topics"] == 2
        assert stats["topics_by_user_level"]["beginner"] == 1
        assert stats["topics_by_user_level"]["intermediate"] == 1
        assert stats["topics_by_readiness"]["ready"] == 2
        assert stats["topics_by_readiness"]["not_ready"] == 0
        assert stats["average_duration"] == (15 + 25) / 2

    def test_catalog_is_stale(self, sample_topics):
        """Test catalog staleness detection."""
        # Arrange
        old_time = datetime(2023, 1, 1, tzinfo=UTC)
        recent_time = datetime.now(UTC)

        old_catalog = Catalog(topics=sample_topics, last_updated=old_time, total_count=2)
        recent_catalog = Catalog(topics=sample_topics, last_updated=recent_time, total_count=2)

        # Act & Assert
        assert old_catalog.is_stale(max_age_hours=1)
        assert not recent_catalog.is_stale(max_age_hours=24)
