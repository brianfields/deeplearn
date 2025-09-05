/**
 * TopicSummary domain entity for topic catalog.
 *
 * Represents a lightweight topic view optimized for browsing and discovery.
 */

export interface TopicSummary {
  readonly id: string;
  readonly title: string;
  readonly coreConcept: string;
  readonly userLevel: 'beginner' | 'intermediate' | 'advanced';
  readonly learningObjectives: string[];
  readonly keyConcepts: string[];
  readonly estimatedDuration: number; // minutes
  readonly componentCount: number;
  readonly isReadyForLearning: boolean;
  readonly createdAt: string;
  readonly updatedAt: string;
  readonly difficultyLevel: string;
  readonly durationDisplay: string;
  readonly readinessStatus: string;
  readonly tags: string[];
}

export interface TopicFilters {
  readonly query?: string;
  readonly userLevel?: 'beginner' | 'intermediate' | 'advanced';
  readonly minDuration?: number;
  readonly maxDuration?: number;
  readonly readyOnly?: boolean;
}

export interface TopicSortOptions {
  readonly sortBy: 'relevance' | 'duration' | 'userLevel' | 'title';
  readonly sortOrder: 'asc' | 'desc';
}

/**
 * Business rules for topic summaries.
 */
export class TopicSummaryRules {
  /**
   * Check if a topic matches search criteria.
   */
  static matchesQuery(topic: TopicSummary, query: string): boolean {
    if (!query.trim()) return true;

    const searchTerm = query.toLowerCase();
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
   * Check if a topic is suitable for a user level.
   */
  static isSuitableForUserLevel(
    topic: TopicSummary,
    userLevel: 'beginner' | 'intermediate' | 'advanced'
  ): boolean {
    const levelHierarchy = { beginner: 1, intermediate: 2, advanced: 3 };
    const topicLevel = levelHierarchy[topic.userLevel];
    const targetLevel = levelHierarchy[userLevel];

    // Allow topics at or below user's level
    return topicLevel <= targetLevel;
  }

  /**
   * Get display-friendly duration text.
   */
  static formatDuration(minutes: number): string {
    if (minutes < 60) {
      return `${minutes} min`;
    }

    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;

    if (remainingMinutes === 0) {
      return `${hours} hr`;
    }

    return `${hours} hr ${remainingMinutes} min`;
  }

  /**
   * Get difficulty level display text.
   */
  static formatDifficultyLevel(userLevel: string): string {
    const levelMap: Record<string, string> = {
      beginner: 'Beginner',
      intermediate: 'Intermediate',
      advanced: 'Advanced',
    };
    return levelMap[userLevel] || 'Unknown';
  }

  /**
   * Get readiness status display text.
   */
  static formatReadinessStatus(topic: TopicSummary): string {
    if (topic.isReadyForLearning) {
      return 'Ready';
    } else if (topic.componentCount > 0) {
      return 'In Progress';
    } else {
      return 'Draft';
    }
  }
}
