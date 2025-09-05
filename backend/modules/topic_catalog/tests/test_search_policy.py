"""
Unit tests for Search Policy.

These tests focus on the business rules for filtering and sorting topics.
"""

import pytest

from modules.topic_catalog.domain.entities.topic_summary import TopicSummary
from modules.topic_catalog.domain.policies.search_policy import SearchPolicy


class TestSearchPolicy:
    """Test cases for SearchPolicy."""

    @pytest.fixture
    def sample_topics(self):
        """Create sample topics for testing."""
        return [
            TopicSummary(
                topic_id="topic_1",
                title="Python Variables",
                core_concept="Understanding variable declaration",
                user_level="beginner",
                learning_objectives=["Declare variables", "Assign values"],
                key_concepts=["variable", "assignment"],
                estimated_duration=15,
                component_count=3,
                is_ready_for_learning=True,
            ),
            TopicSummary(
                topic_id="topic_2",
                title="JavaScript Functions",
                core_concept="Creating and using functions",
                user_level="intermediate",
                learning_objectives=["Define functions", "Call functions"],
                key_concepts=["function", "parameter", "return"],
                estimated_duration=25,
                component_count=5,
                is_ready_for_learning=True,
            ),
            TopicSummary(
                topic_id="topic_3",
                title="Advanced Python Decorators",
                core_concept="Understanding decorators",
                user_level="advanced",
                learning_objectives=["Create decorators", "Use built-in decorators"],
                key_concepts=["decorator", "wrapper", "metadata"],
                estimated_duration=45,
                component_count=7,
                is_ready_for_learning=False,
            ),
            TopicSummary(
                topic_id="topic_4",
                title="Python Data Structures",
                core_concept="Working with lists and dictionaries",
                user_level="beginner",
                learning_objectives=["Use lists", "Use dictionaries"],
                key_concepts=["list", "dictionary", "indexing"],
                estimated_duration=20,
                component_count=4,
                is_ready_for_learning=True,
            ),
        ]

    @pytest.fixture
    def search_policy(self):
        """Create a search policy instance."""
        return SearchPolicy()

    def test_apply_filters_no_filters(self, search_policy, sample_topics):
        """Test applying filters with no filter criteria."""
        # Act
        result = search_policy.apply_filters(sample_topics)

        # Assert
        assert len(result) == 4
        assert result == sample_topics

    def test_apply_filters_with_query(self, search_policy, sample_topics):
        """Test applying filters with search query."""
        # Act
        python_topics = search_policy.apply_filters(sample_topics, query="Python")
        function_topics = search_policy.apply_filters(sample_topics, query="function")
        decorator_topics = search_policy.apply_filters(sample_topics, query="decorator")

        # Assert
        assert len(python_topics) == 3  # All Python-related topics
        assert all("Python" in topic.title or "python" in topic.core_concept.lower() for topic in python_topics)

        assert len(function_topics) == 1
        assert function_topics[0].title == "JavaScript Functions"

        assert len(decorator_topics) == 1
        assert decorator_topics[0].title == "Advanced Python Decorators"

    def test_apply_filters_with_user_level(self, search_policy, sample_topics):
        """Test applying filters with user level."""
        # Act
        beginner_topics = search_policy.apply_filters(sample_topics, user_level="beginner")
        intermediate_topics = search_policy.apply_filters(sample_topics, user_level="intermediate")
        advanced_topics = search_policy.apply_filters(sample_topics, user_level="advanced")

        # Assert
        assert len(beginner_topics) == 2
        assert all(topic.user_level == "beginner" for topic in beginner_topics)

        assert len(intermediate_topics) == 1
        assert intermediate_topics[0].user_level == "intermediate"

        assert len(advanced_topics) == 1
        assert advanced_topics[0].user_level == "advanced"

    def test_apply_filters_ready_only(self, search_policy, sample_topics):
        """Test applying filters for ready topics only."""
        # Act
        ready_topics = search_policy.apply_filters(sample_topics, ready_only=True)
        all_topics = search_policy.apply_filters(sample_topics, ready_only=False)

        # Assert
        assert len(ready_topics) == 3  # 3 topics are ready
        assert all(topic.is_ready_for_learning for topic in ready_topics)

        assert len(all_topics) == 4  # All topics returned when ready_only=False

    def test_apply_filters_combined(self, search_policy, sample_topics):
        """Test applying multiple filters together."""
        # Act
        result = search_policy.apply_filters(sample_topics, query="Python", user_level="beginner", ready_only=True)

        # Assert
        assert len(result) == 2  # Python Variables and Python Data Structures
        assert all("Python" in topic.title for topic in result)
        assert all(topic.user_level == "beginner" for topic in result)
        assert all(topic.is_ready_for_learning for topic in result)

    def test_apply_filters_no_matches(self, search_policy, sample_topics):
        """Test applying filters that result in no matches."""
        # Act
        result = search_policy.apply_filters(sample_topics, query="Ruby", user_level="beginner")

        # Assert
        assert len(result) == 0

    def test_sort_by_relevance_default(self, search_policy, sample_topics):
        """Test sorting by relevance (default: component count descending)."""
        # Act
        sorted_topics = search_policy.sort_by_relevance(sample_topics)

        # Assert
        assert len(sorted_topics) == 4
        # Should be sorted by component count descending
        assert sorted_topics[0].component_count == 7  # Advanced Python Decorators
        assert sorted_topics[1].component_count == 5  # JavaScript Functions
        assert sorted_topics[2].component_count == 4  # Python Data Structures
        assert sorted_topics[3].component_count == 3  # Python Variables

    def test_sort_by_relevance_with_query_boost(self, search_policy, sample_topics):
        """Test sorting by relevance with query-based boosting."""
        # Act
        sorted_topics = search_policy.sort_by_relevance(sample_topics, query="Python")

        # Assert
        # Python topics should be boosted to the top
        python_topics = [topic for topic in sorted_topics if "Python" in topic.title]
        non_python_topics = [topic for topic in sorted_topics if "Python" not in topic.title]

        # All Python topics should come before non-Python topics
        assert len(python_topics) == 3
        assert len(non_python_topics) == 1

        # Within Python topics, should still be sorted by component count
        assert python_topics[0].component_count >= python_topics[1].component_count
        assert python_topics[1].component_count >= python_topics[2].component_count

    def test_sort_by_duration_ascending(self, search_policy, sample_topics):
        """Test sorting by duration in ascending order."""
        # Act
        sorted_topics = search_policy.sort_by_duration(sample_topics, ascending=True)

        # Assert
        durations = [topic.estimated_duration for topic in sorted_topics]
        assert durations == [15, 20, 25, 45]

    def test_sort_by_duration_descending(self, search_policy, sample_topics):
        """Test sorting by duration in descending order."""
        # Act
        sorted_topics = search_policy.sort_by_duration(sample_topics, ascending=False)

        # Assert
        durations = [topic.estimated_duration for topic in sorted_topics]
        assert durations == [45, 25, 20, 15]

    def test_sort_by_user_level(self, search_policy, sample_topics):
        """Test sorting by user level (beginner -> intermediate -> advanced)."""
        # Act
        sorted_topics = search_policy.sort_by_user_level(sample_topics)

        # Assert
        levels = [topic.user_level for topic in sorted_topics]
        # Should group by level: beginner topics first, then intermediate, then advanced
        beginner_count = levels.count("beginner")
        intermediate_count = levels.count("intermediate")
        advanced_count = levels.count("advanced")

        assert beginner_count == 2
        assert intermediate_count == 1
        assert advanced_count == 1

        # Check that beginner topics come first
        assert levels[:beginner_count] == ["beginner"] * beginner_count
        assert levels[beginner_count : beginner_count + intermediate_count] == ["intermediate"] * intermediate_count
        assert levels[beginner_count + intermediate_count :] == ["advanced"] * advanced_count

    def test_apply_pagination(self, search_policy, sample_topics):
        """Test pagination application."""
        # Act
        page_1 = search_policy.apply_pagination(sample_topics, limit=2, offset=0)
        page_2 = search_policy.apply_pagination(sample_topics, limit=2, offset=2)
        page_3 = search_policy.apply_pagination(sample_topics, limit=2, offset=4)

        # Assert
        assert len(page_1) == 2
        assert len(page_2) == 2
        assert len(page_3) == 0  # Beyond available topics

        # Ensure no overlap
        page_1_ids = {topic.topic_id for topic in page_1}
        page_2_ids = {topic.topic_id for topic in page_2}
        assert page_1_ids.isdisjoint(page_2_ids)

    def test_apply_pagination_partial_page(self, search_policy, sample_topics):
        """Test pagination with partial last page."""
        # Act
        result = search_policy.apply_pagination(sample_topics, limit=3, offset=3)

        # Assert
        assert len(result) == 1  # Only 1 topic left on the last page

    def test_apply_pagination_no_limit(self, search_policy, sample_topics):
        """Test pagination with no limit."""
        # Act
        result = search_policy.apply_pagination(sample_topics, limit=None, offset=1)

        # Assert
        assert len(result) == 3  # All topics except the first one

    def test_is_valid_user_level(self, search_policy):
        """Test user level validation."""
        # Act & Assert
        assert search_policy.is_valid_user_level("beginner")
        assert search_policy.is_valid_user_level("intermediate")
        assert search_policy.is_valid_user_level("advanced")
        assert not search_policy.is_valid_user_level("expert")
        assert not search_policy.is_valid_user_level("novice")
        assert not search_policy.is_valid_user_level("")
        assert not search_policy.is_valid_user_level(None)

    def test_get_user_level_priority(self, search_policy):
        """Test user level priority mapping."""
        # Act & Assert
        assert search_policy.get_user_level_priority("beginner") == 0
        assert search_policy.get_user_level_priority("intermediate") == 1
        assert search_policy.get_user_level_priority("advanced") == 2

    def test_calculate_relevance_score_no_query(self, search_policy, sample_topics):
        """Test relevance score calculation without query."""
        # Act
        scores = [search_policy.calculate_relevance_score(topic) for topic in sample_topics]

        # Assert
        # Without query, score should be based on component count
        assert scores[2] > scores[1] > scores[3] > scores[0]  # Ordered by component count

    def test_calculate_relevance_score_with_query(self, search_policy, sample_topics):
        """Test relevance score calculation with query."""
        # Act
        scores = [search_policy.calculate_relevance_score(topic, query="Python") for topic in sample_topics]

        # Assert
        # Python topics should have higher scores
        python_indices = [0, 2, 3]  # Topics with "Python" in title
        non_python_indices = [1]  # JavaScript topic

        for python_idx in python_indices:
            for non_python_idx in non_python_indices:
                assert scores[python_idx] > scores[non_python_idx]
