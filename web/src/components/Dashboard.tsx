'use client'

import { motion } from 'framer-motion'
import {
  Clock,
  TrendingUp,
  BookOpen,
  Trophy,
  Target,
  ChevronRight,
  Play,
  CheckCircle,
  Circle,
  Star,
  Plus,
  MessageSquare,
  Brain,
  BarChart3
} from 'lucide-react'
import { useBiteSizedTopics } from '@/hooks'
import { useRouter } from 'next/navigation'
import type { BiteSizedTopic } from '@/types'

export default function Dashboard() {
  const { topics, isLoading, error } = useBiteSizedTopics()
  const router = useRouter()

  const handleStartLearning = () => {
    router.push('/learn')
  }

  // Simple stats based on available topics
  const dashboardStats = [
    {
      name: 'Available Topics',
      value: topics.length.toString(),
      icon: BookOpen,
      color: 'bg-blue-500'
    },
    {
      name: 'Ready to Learn',
      value: topics.length.toString(),
      icon: Brain,
      color: 'bg-green-500'
    },
    {
      name: 'Avg Duration',
      value: topics.length > 0 ? `${Math.round(topics.reduce((acc: number, topic: BiteSizedTopic) => acc + topic.estimated_duration, 0) / topics.length)} min` : '0 min',
      icon: Clock,
      color: 'bg-purple-500'
    },
    {
      name: 'Difficulty Levels',
              value: Array.from(new Set(topics.map((t: BiteSizedTopic) => t.user_level))).length.toString(),
      icon: Target,
      color: 'bg-orange-500'
    },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <div className="bg-gradient-to-br from-blue-600 via-purple-600 to-indigo-600 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center"
          >
            <h1 className="text-4xl font-bold mb-4">
              Welcome to Bite-Sized Learning
            </h1>
            <p className="text-xl text-blue-100 mb-8 max-w-2xl mx-auto">
              Learn complex topics through focused, interactive sessions designed to fit into your schedule.
            </p>
            <button
              onClick={handleStartLearning}
              className="inline-flex items-center gap-2 px-8 py-4 bg-white text-blue-600 rounded-xl font-semibold hover:bg-blue-50 transition-colors shadow-lg"
            >
              <Play className="w-5 h-5" />
              Start Learning Now
            </button>
          </motion.div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Stats Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          {dashboardStats.map((stat, index) => (
            <motion.div
              key={stat.name}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="bg-white rounded-xl p-6 shadow-sm border border-gray-200"
            >
              <div className="flex items-center">
                <div className={`p-3 rounded-lg ${stat.color}`}>
                  <stat.icon className="w-6 h-6 text-white" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                  <p className="text-2xl font-semibold text-gray-900">{stat.value}</p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Quick Access Topics */}
        <div className="mb-12">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Quick Start Topics</h2>
            <button
              onClick={handleStartLearning}
              className="flex items-center gap-2 text-blue-600 hover:text-blue-700 transition-colors"
            >
              View All Topics
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 animate-pulse">
                  <div className="h-6 bg-gray-200 rounded mb-4"></div>
                  <div className="h-4 bg-gray-200 rounded mb-2"></div>
                  <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                </div>
              ))}
            </div>
          ) : error ? (
            <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
              <p className="text-red-600">{error}</p>
            </div>
          ) : topics.length === 0 ? (
            <div className="bg-white rounded-xl p-12 shadow-sm border border-gray-200 text-center">
              <BookOpen className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No topics available</h3>
              <p className="text-gray-600">Check back later for new learning topics.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                             {topics.slice(0, 6).map((topic: BiteSizedTopic, index: number) => (
                <motion.div
                  key={topic.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 hover:shadow-md transition-shadow cursor-pointer"
                  onClick={handleStartLearning}
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">{topic.title}</h3>
                      <p className="text-gray-600 text-sm">{topic.core_concept}</p>
                    </div>
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded-full">
                      {topic.user_level}
                    </span>
                  </div>

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

                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1 text-sm text-gray-500">
                      <Target className="w-4 h-4" />
                      {topic.learning_objectives.length} objectives
                    </div>
                    <div className="flex items-center gap-1 text-blue-600">
                      <span className="text-sm font-medium">Start</span>
                      <ChevronRight className="w-4 h-4" />
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>

        {/* Getting Started Section */}
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-2xl p-8 border border-blue-200">
          <div className="max-w-2xl">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Ready to Learn?</h2>
            <p className="text-gray-600 mb-6">
              Our bite-sized learning approach breaks down complex topics into manageable, interactive sessions.
              Each topic is designed to be completed in 15 minutes or less, making it easy to fit learning into your day.
            </p>
            <div className="flex flex-col sm:flex-row gap-4">
              <button
                onClick={handleStartLearning}
                className="flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <MessageSquare className="w-5 h-5" />
                Browse Topics
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}