'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { ChevronRight, BookOpen, Target, Clock } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import type { DidacticSnippetProps } from '@/types/components'

export default function DidacticSnippet({
  snippet,
  onContinue,
  isLoading = false
}: DidacticSnippetProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  // Debug log to check what content we're receiving
  console.log('DidacticSnippet received snippet:', snippet)

  // Ensure we have valid content structure
  if (!snippet) {
    console.error('DidacticSnippet: No snippet provided')
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
        <div className="max-w-2xl mx-auto">
          <div className="text-center py-8">
            <p className="text-gray-500">No content available</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4" style={{ display: 'block', visibility: 'visible' }}>
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          <div className="flex items-center gap-2 mb-4">
            <BookOpen className="w-5 h-5 text-blue-600" />
            <span className="text-sm font-medium text-blue-600">Learn</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">
            {snippet.title || 'Learning Topic'}
          </h1>
          <p className="text-gray-600 text-sm sm:text-base">
            {snippet.core_concept || 'Educational Content'}
          </p>
        </motion.div>

        {/* Duration */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
          className="flex items-center gap-2 mb-6 text-sm text-gray-600"
        >
          <Clock className="w-4 h-4" />
          <span>{snippet.estimated_duration || 5} min read</span>
        </motion.div>

        {/* Main Content */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="p-6 mb-6 bg-white/90 backdrop-blur-sm border-0 shadow-lg">
            <div className="prose prose-sm sm:prose-base max-w-none">
              <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                {snippet.snippet || 'Content will be displayed here.'}
              </p>
            </div>
          </Card>
        </motion.div>

        {/* Key Points */}
        {snippet.key_points && snippet.key_points.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <Card className="p-6 mb-6 bg-white/90 backdrop-blur-sm border-0 shadow-lg">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Key Points</h3>
              <ul className="space-y-3">
                {snippet.key_points.map((point, index) => (
                  <motion.li
                    key={index}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.4 + index * 0.1 }}
                    className="flex items-start gap-3"
                  >
                    <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0" />
                    <span className="text-gray-700 text-sm sm:text-base">{point}</span>
                  </motion.li>
                ))}
              </ul>
            </Card>
          </motion.div>
        )}

        {/* Learning Objectives (Expandable) */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="mb-8"
        >
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="w-full text-left"
          >
            <Card className="p-4 bg-white/90 backdrop-blur-sm border-0 shadow-lg hover:shadow-xl transition-shadow">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Target className="w-4 h-4 text-blue-600" />
                  <span className="font-medium text-gray-900">Learning Objectives</span>
                </div>
                <ChevronRight
                  className={`w-4 h-4 text-gray-500 transition-transform ${
                    isExpanded ? 'rotate-90' : ''
                  }`}
                />
              </div>
            </Card>
          </button>

          {isExpanded && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-2"
            >
              <Card className="p-4 bg-white/90 backdrop-blur-sm border-0 shadow-lg">
                <ul className="space-y-2">
                  {(snippet.learning_objectives || []).map((objective, index) => (
                    <li key={index} className="flex items-start gap-2">
                      <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2 flex-shrink-0" />
                      <span className="text-gray-700 text-sm">{objective}</span>
                    </li>
                  ))}
                </ul>
              </Card>
            </motion.div>
          )}
        </motion.div>

        {/* Continue Button */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="sticky bottom-4"
        >
          <Button
            onClick={onContinue}
            disabled={isLoading}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white py-4 text-base font-medium shadow-lg"
          >
            {isLoading ? (
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Loading...
              </div>
            ) : (
              <div className="flex items-center gap-2">
                Continue Learning
                <ChevronRight className="w-4 h-4" />
              </div>
            )}
          </Button>
        </motion.div>
      </div>
    </div>
  )
}