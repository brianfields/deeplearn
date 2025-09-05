/**
 * Search policy for topic catalog.
 *
 * Contains business rules for filtering, sorting, and organizing topics.
 */

import {
  TopicSummary,
  TopicFilters,
  TopicSortOptions,
} from '../entities/topic-summary';

export class SearchPolicy {
  /**
   * Apply filters to a list of topics.
   */
  static applyFilters(
    topics: TopicSummary[],
    filters: TopicFilters
  ): TopicSummary[] {
    let filtered = [...topics];

    // Apply query filter
    if (filters.query) {
      filtered = filtered.filter(topic =>
        this.matchesQuery(topic, filters.query!)
      );
    }

    // Apply user level filter
    if (filters.userLevel) {
      filtered = filtered.filter(
        topic => topic.userLevel === filters.userLevel
      );
    }

    // Apply duration filters
    if (filters.minDuration !== undefined) {
      filtered = filtered.filter(
        topic => topic.estimatedDuration >= filters.minDuration!
      );
    }

    if (filters.maxDuration !== undefined) {
      filtered = filtered.filter(
        topic => topic.estimatedDuration <= filters.maxDuration!
      );
    }

    // Apply readiness filter
    if (filters.readyOnly === true) {
      filtered = filtered.filter(topic => topic.isReadyForLearning);
    }

    return filtered;
  }

  /**
   * Sort topics based on sort options.
   */
  static sortTopics(
    topics: TopicSummary[],
    sortOptions: TopicSortOptions
  ): TopicSummary[] {
    const sorted = [...topics];

    sorted.sort((a, b) => {
      let comparison = 0;

      switch (sortOptions.sortBy) {
        case 'title':
          comparison = a.title.localeCompare(b.title);
          break;
        case 'duration':
          comparison = a.estimatedDuration - b.estimatedDuration;
          break;
        case 'userLevel': {
          const levelOrder = { beginner: 1, intermediate: 2, advanced: 3 };
          comparison = levelOrder[a.userLevel] - levelOrder[b.userLevel];
          break;
        }
        case 'relevance':
        default:
          // Sort by component count (more components = more relevant)
          comparison = b.componentCount - a.componentCount;
          break;
      }

      return sortOptions.sortOrder === 'desc' ? -comparison : comparison;
    });

    return sorted;
  }

  /**
   * Apply pagination to topics.
   */
  static applyPagination(
    topics: TopicSummary[],
    limit: number,
    offset: number = 0
  ): TopicSummary[] {
    return topics.slice(offset, offset + limit);
  }

  /**
   * Check if a topic matches a search query.
   */
  private static matchesQuery(topic: TopicSummary, query: string): boolean {
    const searchTerm = query.toLowerCase().trim();

    return (
      topic.title.toLowerCase().includes(searchTerm) ||
      topic.coreConcept.toLowerCase().includes(searchTerm) ||
      topic.keyConcepts.some(concept =>
        concept.toLowerCase().includes(searchTerm)
      ) ||
      topic.learningObjectives.some(objective =>
        objective.toLowerCase().includes(searchTerm)
      )
    );
  }

  /**
   * Get popular topics (ready topics with most components).
   */
  static getPopularTopics(
    topics: TopicSummary[],
    limit: number = 10
  ): TopicSummary[] {
    return topics
      .filter(topic => topic.isReadyForLearning)
      .sort((a, b) => b.componentCount - a.componentCount)
      .slice(0, limit);
  }

  /**
   * Get recommended topics for a user level.
   */
  static getRecommendedTopics(
    topics: TopicSummary[],
    userLevel: 'beginner' | 'intermediate' | 'advanced',
    limit: number = 5
  ): TopicSummary[] {
    const levelHierarchy = { beginner: 1, intermediate: 2, advanced: 3 };
    const targetLevel = levelHierarchy[userLevel];

    return topics
      .filter(topic => {
        const topicLevel = levelHierarchy[topic.userLevel];
        return topicLevel <= targetLevel && topic.isReadyForLearning;
      })
      .sort((a, b) => {
        // Prioritize topics at the user's exact level
        const aExactMatch = a.userLevel === userLevel ? 1 : 0;
        const bExactMatch = b.userLevel === userLevel ? 1 : 0;

        if (aExactMatch !== bExactMatch) {
          return bExactMatch - aExactMatch;
        }

        // Then sort by component count
        return b.componentCount - a.componentCount;
      })
      .slice(0, limit);
  }

  /**
   * Validate search filters.
   */
  static validateFilters(filters: TopicFilters): string[] {
    const errors: string[] = [];

    if (filters.minDuration !== undefined && filters.minDuration < 0) {
      errors.push('Minimum duration cannot be negative');
    }

    if (filters.maxDuration !== undefined && filters.maxDuration < 0) {
      errors.push('Maximum duration cannot be negative');
    }

    if (
      filters.minDuration !== undefined &&
      filters.maxDuration !== undefined &&
      filters.minDuration > filters.maxDuration
    ) {
      errors.push('Minimum duration cannot be greater than maximum duration');
    }

    return errors;
  }
}
