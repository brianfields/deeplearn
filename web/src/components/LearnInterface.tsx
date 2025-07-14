'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Plus,
  BookOpen,
  MessageSquare,
  Play,
  Clock,
  Brain,
  Target,
  Search,
  Filter,
  MoreVertical,
  ArrowRight,
  Users,
  Star,
  CheckCircle,
  Circle,
  Loader2
} from 'lucide-react'
import { useLearningPaths } from '@/hooks/useLearningPaths'
import { LearningPath, Topic } from '@/types'
import { EnhancedLearningPath } from '@/services'
import ConversationInterface from './ConversationInterface'

interface LearnInterfaceProps {}

export default function LearnInterface({}: LearnInterfaceProps) {
  const {
    learningPaths: rawLearningPaths,
    isLoading,
    error,
    searchFilters,
    searchPaths,
    createPath,
    getLearningPath,
    isCreating,
    refreshPaths,
    filteredPaths
  } = useLearningPaths()

  // Ensure learningPaths is always an array to prevent undefined errors
  const learningPaths = rawLearningPaths || []

  const [showCreateForm, setShowCreateForm] = useState(false)
    const [selectedPath, setSelectedPath] = useState<EnhancedLearningPath | null>(null)
  const [selectedTopic, setSelectedTopic] = useState<Topic | null>(null)
  const [showConversation, setShowConversation] = useState(false)

  // Create new learning path form
  const [newTopic, setNewTopic] = useState('')
  const [userLevel, setUserLevel] = useState<'beginner' | 'intermediate' | 'advanced'>('beginner')

  const handleCreateLearningPath = async () => {
    if (!newTopic.trim()) return

    try {
      const newPath = await createPath({ topic: newTopic.trim(), userLevel: userLevel })

      // Reset form
      setNewTopic('')
      setUserLevel('beginner')
      setShowCreateForm(false)

      // Automatically open the new learning path
      if (newPath) {
        const fullPath = await getLearningPath(newPath.id)
        setSelectedPath(fullPath)
      }
    } catch (error) {
      console.error('Error creating learning path:', error)
    }
  }

  const openLearningPath = async (pathId: string) => {
    try {
      const fullPath = await getLearningPath(pathId)
      setSelectedPath(fullPath)
    } catch (error) {
      console.error('Error loading learning path:', error)
    }
  }

  const startConversation = (topic: Topic) => {
    setSelectedTopic(topic)
    setShowConversation(true)
  }

  if (showConversation && selectedPath && selectedTopic) {
    return (
      <div className="h-[calc(100vh-4rem)] -mt-6 -mx-4 sm:-mx-6 lg:-mx-8">
        <ConversationInterface
          pathId={selectedPath.id}
          topicId={selectedTopic.id}
          topicTitle={selectedTopic.title}
          onClose={() => {
            setShowConversation(false)
            setSelectedTopic(null)
          }}
        />
      </div>
    )
  }

  if (selectedPath) {
    return (
      <div className="space-y-6">
        {/* Learning Path Header */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <button
                onClick={() => {
                  setSelectedPath(null)
                  setSelectedTopic(null)
                }}
                className="text-blue-600 hover:text-blue-700 text-sm font-medium mb-4 flex items-center"
              >
                ← Back to Learning Paths
              </button>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">{selectedPath.topic_name}</h1>
              <p className="text-gray-600 mb-4">{selectedPath.description}</p>

              <div className="flex items-center space-x-6 text-sm text-gray-500">
                <div className="flex items-center space-x-1">
                  <BookOpen className="h-4 w-4" />
                  <span>{selectedPath.topics?.length || 0} topics</span>
                </div>
                <div className="flex items-center space-x-1">
                  <Clock className="h-4 w-4" />
                  <span>{selectedPath.estimated_total_hours || 0}h estimated</span>
                </div>
                <div className="flex items-center space-x-1">
                  <Target className="h-4 w-4" />
                  <span>{selectedPath.progressPercentage || 0}% complete</span>
                </div>
              </div>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="mt-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">Overall Progress</span>
              <span className="text-sm text-gray-500">
                {selectedPath.completedTopics || 0} of {selectedPath.topics?.length || 0} topics
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${selectedPath.progressPercentage || 0}%` }}
              />
            </div>
          </div>
        </div>

        {/* Bite-Sized Content Summary */}
        {selectedPath.bite_sized_content_info && (
          <div className="bg-gradient-to-r from-emerald-50 to-teal-50 rounded-xl border border-emerald-200 shadow-sm">
            <div className="p-6">
              <div className="flex items-center space-x-2 mb-4">
                <div className="h-8 w-8 bg-emerald-100 rounded-full flex items-center justify-center">
                  <svg className="h-5 w-5 text-emerald-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-emerald-900">Enhanced Learning Content</h3>
                  <p className="text-sm text-emerald-700">Rich, interactive content available for select topics</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-white/70 rounded-lg p-4 border border-emerald-200/50">
                  <div className="text-2xl font-bold text-emerald-800 mb-1">
                    {selectedPath.bite_sized_content_info.total_generated}
                  </div>
                  <div className="text-sm text-emerald-600">Topics with enhanced content</div>
                </div>
                <div className="bg-white/70 rounded-lg p-4 border border-emerald-200/50">
                  <div className="text-sm font-medium text-emerald-800 mb-1">Content Strategy</div>
                  <div className="text-xs text-emerald-600 capitalize">
                    {selectedPath.bite_sized_content_info.creation_strategy.replace('_', ' ')}
                  </div>
                </div>
                <div className="bg-white/70 rounded-lg p-4 border border-emerald-200/50">
                  <div className="text-sm font-medium text-emerald-800 mb-1">Optimized For</div>
                  <div className="text-xs text-emerald-600 capitalize">
                    {selectedPath.bite_sized_content_info.user_level} level
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Topics List */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="p-6 border-b border-gray-100">
            <h2 className="text-xl font-semibold text-gray-900">Learning Topics</h2>
            <p className="text-gray-600 mt-1">Click on any topic to start a conversation with the AI tutor</p>
          </div>

          <div className="p-6">
            <div className="space-y-4">
              {(selectedPath.topics || []).map((topic, index) => (
                <motion.div
                  key={topic.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.1 }}
                                    className={`p-4 rounded-lg border transition-all duration-200 hover:shadow-md cursor-pointer ${
                    topic.status === 'completed' || topic.status === 'in_progress'
                      ? 'border-blue-200 bg-blue-50/50 hover:bg-blue-50'
                      : 'border-gray-200 bg-gray-50/50 hover:bg-gray-50'
                  }`}
                  onClick={() => startConversation(topic)}
                >
                  <div className="flex items-start space-x-4">
                    <div className="flex-shrink-0 mt-1">
                      {topic.status === 'completed' ? (
                        <CheckCircle className="h-5 w-5 text-green-500" />
                      ) : topic.status === 'in_progress' ? (
                        <Play className="h-5 w-5 text-blue-500" />
                      ) : (
                        <Circle className="h-5 w-5 text-gray-400" />
                      )}
                    </div>

                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <h3 className="font-medium text-gray-900">{topic.title}</h3>
                          {topic.has_bite_sized_content && (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800 border border-emerald-200">
                              <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                              </svg>
                              Enhanced Content
                            </span>
                          )}
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className="text-sm text-gray-500">{topic.estimated_duration}min</span>
                          <ArrowRight className="h-4 w-4 text-gray-400" />
                        </div>
                      </div>
                      <p className="text-sm text-gray-600 mt-1">{topic.description}</p>

                      {topic.learning_objectives && topic.learning_objectives.length > 0 && (
                        <div className="mt-3">
                          <p className="text-xs font-medium text-gray-700 mb-2">Learning Objectives:</p>
                          <ul className="text-xs text-gray-600 space-y-1">
                            {(topic.learning_objectives || []).slice(0, 3).map((objective: string, i: number) => (
                              <li key={i} className="flex items-center space-x-2">
                                <div className="w-1 h-1 bg-gray-400 rounded-full flex-shrink-0" />
                                <span>{objective}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header with Search and Create */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AI Learning Paths</h1>
          <p className="text-gray-600 mt-1">Personalized learning journeys powered by AI</p>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors"
        >
          <Plus className="h-4 w-4" />
          <span>Create Learning Path</span>
        </button>
      </div>

      {/* Search and Filters */}
      <div className="flex items-center space-x-4">
        <div className="flex-1 relative">
          <Search className="h-5 w-5 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search learning paths..."
            value={searchFilters.searchTerm}
            onChange={(e) => searchPaths({ searchTerm: e.target.value })}
            className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        <button className="p-2 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
          <Filter className="h-5 w-5 text-gray-600" />
        </button>
      </div>

      {/* Create Learning Path Form */}
      <AnimatePresence>
        {showCreateForm && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden"
          >
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Create New Learning Path</h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    What would you like to learn?
                  </label>
                  <input
                    type="text"
                    value={newTopic}
                    onChange={(e) => setNewTopic(e.target.value)}
                    placeholder="e.g., Machine Learning, Web Development, Data Science..."
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Your current level
                  </label>
                  <select
                    value={userLevel}
                    onChange={(e) => setUserLevel(e.target.value as 'beginner' | 'intermediate' | 'advanced')}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="beginner">Beginner</option>
                    <option value="intermediate">Intermediate</option>
                    <option value="advanced">Advanced</option>
                  </select>
                </div>

                <div className="flex items-center space-x-3 pt-4">
                  <button
                    onClick={handleCreateLearningPath}
                    disabled={!newTopic.trim() || isCreating}
                    className="bg-blue-500 hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors"
                  >
                    {isCreating ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        <span>Creating...</span>
                      </>
                    ) : (
                      <>
                        <Plus className="h-4 w-4" />
                        <span>Create Path</span>
                      </>
                    )}
                  </button>
                  <button
                    onClick={() => setShowCreateForm(false)}
                    className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <Circle className="h-5 w-5 text-red-500 flex-shrink-0" />
            <span className="text-red-700">{error}</span>
          </div>
          <button
            onClick={refreshPaths}
            className="mt-2 px-4 py-2 bg-red-100 hover:bg-red-200 text-red-700 rounded-lg transition-colors"
          >
            Retry
          </button>
        </div>
      )}

      {/* Learning Paths Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 animate-pulse">
              <div className="h-4 bg-gray-200 rounded mb-4"></div>
              <div className="h-3 bg-gray-200 rounded mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-2/3"></div>
            </div>
          ))}
        </div>
      ) : learningPaths.length === 0 ? (
        <div className="text-center py-12">
          <BookOpen className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No learning paths yet</h3>
                    <p className="text-gray-500 mb-4">
            {searchFilters.searchTerm
              ? `No results found for "${searchFilters.searchTerm}". Try a different search term.`
              : "Create your first learning path to begin your AI-powered learning journey."
            }
          </p>
          {!searchFilters.searchTerm && (
            <button
              onClick={() => setShowCreateForm(true)}
              className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center space-x-2 mx-auto transition-colors"
            >
              <Plus className="h-4 w-4" />
              <span>Create Learning Path</span>
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {(learningPaths || []).map((path, index) => (
            <motion.div
              key={path.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: index * 0.1 }}
              className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 hover:shadow-md transition-all duration-200 cursor-pointer"
              onClick={() => openLearningPath(path.id)}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900 mb-2">{path.topic_name}</h3>
                  <p className="text-sm text-gray-600 mb-3">{path.description}</p>
                </div>
                <button className="p-1 hover:bg-gray-100 rounded">
                  <MoreVertical className="h-4 w-4 text-gray-400" />
                </button>
              </div>

              <div className="space-y-3">
                {/* Progress Bar */}
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-medium text-gray-700">Progress</span>
                    <span className="text-xs text-gray-500">
                      {path.total_topics > 0 ? Math.round((path.progress_count / path.total_topics) * 100) : 0}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-1.5">
                    <div
                      className="bg-blue-500 h-1.5 rounded-full transition-all duration-300"
                      style={{
                        width: `${path.total_topics > 0 ? Math.round((path.progress_count / path.total_topics) * 100) : 0}%`
                      }}
                    />
                  </div>
                </div>

                {/* Stats */}
                <div className="flex items-center justify-between text-sm text-gray-500">
                  <div className="flex items-center space-x-1">
                    <BookOpen className="h-4 w-4" />
                    <span>{path.total_topics || 0} topics</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Clock className="h-4 w-4" />
                    <span>{path.estimated_total_hours || 0}h</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Target className="h-4 w-4" />
                    <span>{path.progress_count || 0}/{path.total_topics || 0}</span>
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  )
}