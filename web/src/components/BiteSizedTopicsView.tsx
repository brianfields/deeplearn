'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  Play,
  Book,
  Clock,
  Target,
  Brain,
  ChevronRight,
  Loader2,
  AlertCircle,
  RefreshCw,
  Eye
} from 'lucide-react'
import { useBiteSizedTopics } from '@/hooks'
import ConversationInterface from './ConversationInterface'
import type { BiteSizedTopic, ConversationSession } from '@/types'



export default function BiteSizedTopicsView() {
  const {
    topics,
    isLoading,
    isLoadingDetail,
    error,
    refreshTopics,
    startConversation
  } = useBiteSizedTopics()

  const [activeConversation, setActiveConversation] = useState<ConversationSession | null>(null)

  const handleRunTopic = async (topic: BiteSizedTopic) => {
    try {
      const session = await startConversation(topic.id)
      setActiveConversation(session)
    } catch (error) {
      console.error('Failed to start conversation:', error)
    }
  }

  const handleViewContent = (topic: BiteSizedTopic) => {
    // Open topic content in new tab
    window.open(`/topic/${topic.id}`, '_blank')
  }



  const handleCloseConversation = () => {
    setActiveConversation(null)
  }

  if (activeConversation) {
    return (
      <ConversationInterface
        pathId="bite-sized"
        topicId={activeConversation.session_id}
        topicTitle={activeConversation.topic_title}
        onClose={handleCloseConversation}
      />
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Bite-Sized Learning Topics</h1>
              <p className="text-gray-600 mt-2">
                Choose a topic to start an interactive learning session or explore the content
              </p>
            </div>
            <button
              onClick={refreshTopics}
              disabled={isLoading}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <RefreshCw className="w-4 h-4" />
              )}
              Refresh
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Error State */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-500" />
            <span className="text-red-700">{error}</span>
          </div>
        )}

        {/* Loading State */}
        {isLoading && topics.length === 0 ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <Loader2 className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-4" />
              <p className="text-gray-600">Loading topics...</p>
            </div>
          </div>
        ) : (
          /* Topics Grid */
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {topics.map((topic) => (
              <motion.div
                key={topic.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow"
              >
                {/* Topic Card Header */}
                <div className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">{topic.title}</h3>
                      <p className="text-gray-600 text-sm mb-3">{topic.core_concept}</p>
                    </div>
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded-full">
                      {topic.user_level}
                    </span>
                  </div>

                  {/* Learning Objectives Preview */}
                  <div className="mb-4">
                    <h4 className="text-sm font-medium text-gray-900 mb-2">Learning Goals</h4>
                    <ul className="space-y-1">
                      {topic.learning_objectives.slice(0, 2).map((objective, index) => (
                        <li key={index} className="flex items-start gap-2 text-sm text-gray-600">
                          <Target className="w-3 h-3 mt-0.5 text-blue-500 shrink-0" />
                          {objective}
                        </li>
                      ))}
                      {topic.learning_objectives.length > 2 && (
                        <li className="text-sm text-gray-500">
                          +{topic.learning_objectives.length - 2} more objectives
                        </li>
                      )}
                    </ul>
                  </div>

                  {/* Metadata */}
                  <div className="flex items-center gap-4 text-sm text-gray-500 mb-4">
                    <div className="flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      {topic.estimated_duration} min
                    </div>
                    <div className="flex items-center gap-1">
                      <Brain className="w-4 h-4" />
                      {topic.key_concepts.length} concepts
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleRunTopic(topic)}
                      className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                    >
                      <Play className="w-4 h-4" />
                      Start Learning
                    </button>
                    <button
                      onClick={() => handleViewContent(topic)}
                      className="flex items-center justify-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                    >
                      <Eye className="w-4 h-4" />
                      View Content
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}

        {/* Empty State */}
        {!isLoading && topics.length === 0 && !error && (
          <div className="text-center py-12">
            <Book className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No topics available</h3>
            <p className="text-gray-600">
              There are no bite-sized topics available at the moment.
            </p>
          </div>
        )}
      </div>



      {/* Loading Detail Overlay */}
      {isLoadingDetail && (
        <div className="fixed inset-0 bg-black/20 z-40 flex items-center justify-center">
          <div className="bg-white rounded-lg p-6 shadow-xl">
            <div className="flex items-center gap-3">
              <Loader2 className="w-5 h-5 animate-spin text-blue-500" />
              <span className="text-gray-700">Loading topic content...</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}