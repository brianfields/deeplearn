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
  Eye,
  Zap,
  Flame,
  Plus,
  Settings
} from 'lucide-react'
import { useBiteSizedTopics, useDuolingoLearning } from '@/hooks'
import type { BiteSizedTopic } from '@/types'

export default function BiteSizedTopicsView() {
  const {
    topics,
    isLoading,
    isLoadingDetail,
    error,
    refreshTopics
  } = useBiteSizedTopics()

  const { cacheStats, isOfflineAvailable } = useDuolingoLearning()

  const handleRunTopic = (topic: BiteSizedTopic) => {
    // Navigate to topic page with Duolingo-style learning mode
    window.location.href = `/topic/${topic.id}?mode=learning&duolingo=true`
  }

  const handleViewContent = (topic: BiteSizedTopic) => {
    // Go directly to content view, skipping the overview
    window.location.href = `/topic/${topic.id}?mode=content`
  }

  const handleEditTopic = (topic: BiteSizedTopic) => {
    // Navigate to content creation studio for this topic
    window.location.href = `/content-creation/${topic.id}`
  }

  const handleNewTopic = () => {
    // Navigate to content creation studio for new topic
    window.location.href = `/content-creation/new`
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-4" />
          <p className="text-gray-600">Loading bite-sized topics...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Error Loading Topics</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={refreshTopics}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2 mx-auto"
          >
            <RefreshCw className="w-4 h-4" />
            Try Again
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Bite-Sized Learning</h1>
              <p className="text-gray-600 mt-1">Quick, focused topics you can complete in 15 minutes</p>
            </div>

            {/* Stats display and New Topic Button */}
            <div className="flex items-center gap-6">
              {cacheStats.currentStreak > 0 && (
                <div className="flex items-center gap-2 text-orange-600">
                  <Flame className="w-5 h-5" />
                  <div className="text-right">
                    <div className="text-xl font-bold">{cacheStats.currentStreak}</div>
                    <div className="text-xs">Day Streak</div>
                  </div>
                </div>
              )}

              <div className="flex items-center gap-2 text-green-600">
                <Target className="w-5 h-5" />
                <div className="text-right">
                  <div className="text-xl font-bold">{cacheStats.todayProgress}</div>
                  <div className="text-xs">Today</div>
                </div>
              </div>

              <div className="flex items-center gap-2 text-blue-600">
                <Book className="w-5 h-5" />
                <div className="text-right">
                  <div className="text-xl font-bold">{cacheStats.cachedTopics}</div>
                  <div className="text-xs">Cached</div>
                </div>
              </div>

              {/* New Topic Button */}
              <button
                onClick={handleNewTopic}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors flex items-center gap-2 font-medium"
              >
                <Plus className="w-4 h-4" />
                New Topic
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Topics grid */}
      <div className="max-w-6xl mx-auto px-4 py-8">
        {topics.length === 0 ? (
          <div className="text-center py-12">
            <Book className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">No Topics Available</h3>
            <p className="text-gray-600 mb-4">Create a learning path to generate bite-sized topics.</p>
            <button
              onClick={refreshTopics}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh Topics
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {topics.map((topic: BiteSizedTopic) => (
              <motion.div
                key={topic.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow"
              >
                {/* Topic header */}
                <div className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2">
                        {topic.title}
                      </h3>
                      <p className="text-gray-600 text-sm mb-3 line-clamp-2">
                        {topic.core_concept}
                      </p>
                    </div>

                    {/* Offline indicator */}
                    {isOfflineAvailable && (
                      <div className="w-2 h-2 bg-green-500 rounded-full ml-2 mt-1"
                           title="Available offline" />
                    )}
                  </div>

                  {/* Topic metadata */}
                  <div className="flex items-center gap-4 text-xs text-gray-500 mb-4">
                    <div className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      <span>~15 min</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Target className="w-3 h-3" />
                      <span>{topic.learning_objectives.length} objectives</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Brain className="w-3 h-3" />
                      <span>{topic.user_level}</span>
                    </div>
                  </div>

                  {/* Learning objectives preview */}
                  <div className="mb-4">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">You'll learn:</h4>
                    <ul className="space-y-1">
                      {topic.learning_objectives.slice(0, 2).map((objective: string, index: number) => (
                        <li key={index} className="text-xs text-gray-600 flex items-start gap-2">
                          <span className="text-blue-500 mt-1">•</span>
                          <span className="line-clamp-1">{objective}</span>
                        </li>
                      ))}
                      {topic.learning_objectives.length > 2 && (
                        <li className="text-xs text-gray-500">
                          +{topic.learning_objectives.length - 2} more...
                        </li>
                      )}
                    </ul>
                  </div>
                </div>

                {/* Action buttons */}
                <div className="px-6 pb-6">
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleRunTopic(topic)}
                      className="flex-1 bg-gradient-to-r from-green-600 to-blue-600 text-white py-3 px-4 rounded-lg font-medium flex items-center justify-center gap-2 hover:from-green-700 hover:to-blue-700 transition-all text-sm"
                    >
                      <Zap className="w-4 h-4" />
                      Start Learning
                    </button>

                    <button
                      onClick={() => handleViewContent(topic)}
                      className="px-4 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                      title="View content"
                    >
                      <Eye className="w-4 h-4" />
                    </button>

                    <button
                      onClick={() => handleEditTopic(topic)}
                      className="px-4 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                      title="Edit topic"
                    >
                      <Settings className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}