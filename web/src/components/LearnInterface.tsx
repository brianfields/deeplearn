'use client'

import { useState, useEffect } from 'react'
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
import { apiClient, type LearningPath, calculateProgress } from '@/lib/api'
import ConversationInterface from './ConversationInterface'

interface LearnInterfaceProps {}

export default function LearnInterface({}: LearnInterfaceProps) {
  const [learningPaths, setLearningPaths] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedPath, setSelectedPath] = useState<LearningPath | null>(null)
  const [selectedTopic, setSelectedTopic] = useState<any | null>(null)
  const [showConversation, setShowConversation] = useState(false)

  // Create new learning path form
  const [newTopic, setNewTopic] = useState('')
  const [userLevel, setUserLevel] = useState('beginner')
  const [isCreating, setIsCreating] = useState(false)

  useEffect(() => {
    loadLearningPaths()
  }, [])

  const loadLearningPaths = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const paths = await apiClient.getLearningPaths()
      setLearningPaths(paths)
    } catch (error) {
      console.error('Error loading learning paths:', error)
      setError('Failed to load learning paths. Please refresh the page.')
    } finally {
      setIsLoading(false)
    }
  }

  const createLearningPath = async () => {
    if (!newTopic.trim()) return

    try {
      setIsCreating(true)
      setError(null)

      const newPath = await apiClient.createLearningPath(newTopic.trim(), userLevel)

      // Reload learning paths to get updated list
      await loadLearningPaths()

      // Reset form
      setNewTopic('')
      setUserLevel('beginner')
      setShowCreateForm(false)

      // Automatically open the new learning path
      const fullPath = await apiClient.getLearningPath(newPath.id)
      setSelectedPath(fullPath)

    } catch (error) {
      console.error('Error creating learning path:', error)
      setError(error instanceof Error ? error.message : 'Failed to create learning path')
    } finally {
      setIsCreating(false)
    }
  }

  const openLearningPath = async (pathId: string) => {
    try {
      const fullPath = await apiClient.getLearningPath(pathId)
      setSelectedPath(fullPath)
    } catch (error) {
      console.error('Error loading learning path:', error)
      setError('Failed to load learning path details')
    }
  }

  const startConversation = (topic: any) => {
    setSelectedTopic(topic)
    setShowConversation(true)
  }

  const filteredPaths = learningPaths.filter(path =>
    path.topic_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    path.description.toLowerCase().includes(searchTerm.toLowerCase())
  )

  if (showConversation && selectedPath && selectedTopic) {
    return (
      <div className="h-[calc(100vh-4rem)] -mt-6 -mx-4 sm:-mx-6 lg:-mx-8">
        <ConversationInterface
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
                  <span>{selectedPath.topics.length} topics</span>
                </div>
                <div className="flex items-center space-x-1">
                  <Clock className="h-4 w-4" />
                  <span>{selectedPath.estimated_total_hours}h estimated</span>
                </div>
                <div className="flex items-center space-x-1">
                  <Target className="h-4 w-4" />
                  <span>{Math.round((selectedPath.current_topic_index / selectedPath.topics.length) * 100)}% complete</span>
                </div>
              </div>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="mt-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">Overall Progress</span>
              <span className="text-sm text-gray-500">
                {selectedPath.current_topic_index} of {selectedPath.topics.length} topics
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${(selectedPath.current_topic_index / selectedPath.topics.length) * 100}%` }}
              />
            </div>
          </div>
        </div>

        {/* Topics List */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="p-6 border-b border-gray-100">
            <h2 className="text-xl font-semibold text-gray-900">Learning Topics</h2>
            <p className="text-gray-600 mt-1">Click on any topic to start a conversation with the AI tutor</p>
          </div>

          <div className="p-6">
            <div className="space-y-4">
              {selectedPath.topics.map((topic, index) => (
                <motion.div
                  key={topic.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.1 }}
                  className={`p-4 rounded-lg border transition-all duration-200 hover:shadow-md cursor-pointer ${
                    index <= selectedPath.current_topic_index
                      ? 'border-blue-200 bg-blue-50/50 hover:bg-blue-50'
                      : 'border-gray-200 bg-gray-50/50 hover:bg-gray-50'
                  }`}
                  onClick={() => startConversation(topic)}
                >
                  <div className="flex items-start space-x-4">
                    <div className="flex-shrink-0">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                        index < selectedPath.current_topic_index
                          ? 'bg-green-500 text-white'
                          : index === selectedPath.current_topic_index
                          ? 'bg-blue-500 text-white'
                          : 'bg-gray-300 text-gray-600'
                      }`}>
                        {index < selectedPath.current_topic_index ? (
                          <CheckCircle className="h-4 w-4" />
                        ) : index === selectedPath.current_topic_index ? (
                          <Play className="h-4 w-4" />
                        ) : (
                          index + 1
                        )}
                      </div>
                    </div>

                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-gray-900 mb-1">{topic.title}</h3>
                      <p className="text-sm text-gray-600 mb-2">{topic.description}</p>

                      {topic.learning_objectives.length > 0 && (
                        <div className="mb-3">
                          <p className="text-xs font-medium text-gray-700 mb-1">Learning Objectives:</p>
                          <ul className="text-xs text-gray-600 space-y-1">
                            {topic.learning_objectives.slice(0, 3).map((objective, i) => (
                              <li key={i} className="flex items-start space-x-1">
                                <span>•</span>
                                <span>{objective}</span>
                              </li>
                            ))}
                            {topic.learning_objectives.length > 3 && (
                              <li className="text-gray-500">
                                +{topic.learning_objectives.length - 3} more objectives
                              </li>
                            )}
                          </ul>
                        </div>
                      )}

                      <div className="flex items-center space-x-4 text-xs text-gray-500">
                        <div className="flex items-center space-x-1">
                          <Clock className="h-3 w-3" />
                          <span>{topic.estimated_duration}min</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <Brain className="h-3 w-3" />
                          <span>Level {topic.difficulty_level}</span>
                        </div>
                        <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                          topic.status === 'completed' ? 'bg-green-100 text-green-800' :
                          topic.status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
                          'bg-gray-100 text-gray-600'
                        }`}>
                          {topic.status.replace('_', ' ')}
                        </div>
                      </div>
                    </div>

                    <div className="flex-shrink-0">
                      <MessageSquare className="h-5 w-5 text-gray-400 group-hover:text-blue-500" />
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
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Learn with AI Tutor</h1>
          <p className="text-gray-600 mt-1">
            Create personalized learning paths and engage in Socratic dialogues with AI
          </p>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors flex items-center space-x-2"
        >
          <Plus className="h-4 w-4" />
          <span>New Learning Path</span>
        </button>
      </div>

      {/* Search and Filters */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <div className="flex items-center space-x-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search learning paths..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <button className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors">
            <Filter className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <Circle className="h-5 w-5 text-red-500" />
            <span className="text-red-700">{error}</span>
          </div>
          <button
            onClick={loadLearningPaths}
            className="mt-2 px-4 py-2 bg-red-100 hover:bg-red-200 text-red-700 rounded-lg transition-colors"
          >
            Retry
          </button>
        </div>
      )}

      {/* Learning Paths */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-full mb-4"></div>
              <div className="h-2 bg-gray-200 rounded w-full mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      ) : filteredPaths.length === 0 ? (
        <div className="text-center py-12">
          <BookOpen className="h-16 w-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-xl font-medium text-gray-900 mb-2">
            {searchTerm ? 'No matching learning paths' : 'No learning paths yet'}
          </h3>
          <p className="text-gray-500 mb-6">
            {searchTerm
              ? 'Try adjusting your search terms'
              : 'Create your first learning path to start your AI-powered learning journey'
            }
          </p>
          {!searchTerm && (
            <button
              onClick={() => setShowCreateForm(true)}
              className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors flex items-center space-x-2 mx-auto"
            >
              <Plus className="h-5 w-5" />
              <span>Create Learning Path</span>
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredPaths.map((path, index) => (
            <motion.div
              key={path.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: index * 0.1 }}
              className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 hover:shadow-md transition-all duration-200 cursor-pointer"
              onClick={() => openLearningPath(path.id)}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-lg font-bold">
                  {path.topic_name.charAt(0).toUpperCase()}
                </div>
                <button className="p-1 text-gray-400 hover:text-gray-600">
                  <MoreVertical className="h-4 w-4" />
                </button>
              </div>

              <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2">{path.topic_name}</h3>
              <p className="text-sm text-gray-600 mb-4 line-clamp-3">{path.description}</p>

              <div className="space-y-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-500">Progress</span>
                  <span className="font-medium text-gray-900">
                    {Math.round((path.progress_count / path.total_topics) * 100)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${(path.progress_count / path.total_topics) * 100}%` }}
                  />
                </div>

                <div className="flex items-center justify-between text-xs text-gray-500">
                  <div className="flex items-center space-x-1">
                    <BookOpen className="h-3 w-3" />
                    <span>{path.total_topics} topics</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Clock className="h-3 w-3" />
                    <span>{path.estimated_total_hours}h</span>
                  </div>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-gray-100">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">
                    Created {new Date(path.created_at).toLocaleDateString()}
                  </span>
                  <ArrowRight className="h-4 w-4 text-gray-400" />
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {/* Create Learning Path Modal */}
      <AnimatePresence>
        {showCreateForm && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-white rounded-xl p-6 w-full max-w-md"
            >
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Create New Learning Path</h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    What would you like to learn?
                  </label>
                  <input
                    type="text"
                    value={newTopic}
                    onChange={(e) => setNewTopic(e.target.value)}
                    placeholder="e.g. Machine Learning Basics, React Advanced Patterns..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    disabled={isCreating}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Your Level
                  </label>
                  <select
                    value={userLevel}
                    onChange={(e) => setUserLevel(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    disabled={isCreating}
                  >
                    <option value="beginner">Beginner</option>
                    <option value="intermediate">Intermediate</option>
                    <option value="advanced">Advanced</option>
                  </select>
                </div>
              </div>

              <div className="flex items-center justify-end space-x-3 mt-6">
                <button
                  onClick={() => {
                    setShowCreateForm(false)
                    setNewTopic('')
                    setUserLevel('beginner')
                  }}
                  className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
                  disabled={isCreating}
                >
                  Cancel
                </button>
                <button
                  onClick={createLearningPath}
                  disabled={!newTopic.trim() || isCreating}
                  className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                >
                  {isCreating ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Creating...</span>
                    </>
                  ) : (
                    <>
                      <Plus className="h-4 w-4" />
                      <span>Create</span>
                    </>
                  )}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}