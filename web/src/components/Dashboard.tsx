'use client'

import { useState, useEffect } from 'react'
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
import { apiClient, type Progress, calculateProgress } from '@/lib/api'

export default function Dashboard() {
  const [progress, setProgress] = useState<Progress | null>(null)
  const [learningPaths, setLearningPaths] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      setIsLoading(true)
      setError(null)

      // Fetch progress and learning paths in parallel
      const [progressData, pathsData] = await Promise.all([
        apiClient.getProgress(),
        apiClient.getLearningPaths()
      ])

      setProgress(progressData)
      setLearningPaths(pathsData)

    } catch (error) {
      console.error('Error loading dashboard data:', error)
      setError('Failed to load dashboard data. Please refresh the page.')
    } finally {
      setIsLoading(false)
    }
  }

  const stats = progress ? [
    {
      name: 'Learning Paths',
      value: progress.total_paths.toString(),
      icon: BookOpen,
      color: 'bg-blue-500'
    },
    {
      name: 'Completed',
      value: progress.completed_paths.toString(),
      icon: CheckCircle,
      color: 'bg-green-500'
    },
    {
      name: 'Understanding',
      value: `${Math.round((progress.overall_progress?.understanding_level || 0) * 100)}%`,
      icon: Brain,
      color: 'bg-purple-500'
    },
    {
      name: 'Concepts Mastered',
      value: (progress.overall_progress?.concepts_mastered || 0).toString(),
      icon: Trophy,
      color: 'bg-orange-500'
    },
  ] : []

  if (isLoading) {
    return (
      <div className="space-y-8">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
                <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
                <div className="h-8 bg-gray-200 rounded w-1/3"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <Circle className="h-5 w-5 text-red-500" />
            <span className="text-red-700">{error}</span>
          </div>
          <button
            onClick={loadDashboardData}
            className="mt-2 px-4 py-2 bg-red-100 hover:bg-red-200 text-red-700 rounded-lg transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Welcome back, Brian!</h1>
            <p className="text-gray-600 mt-1">Ready to continue your learning journey?</p>
          </div>
          <div className="flex items-center space-x-3">
            <div className="text-right">
              <p className="text-sm text-gray-500">Total Progress</p>
              <p className="text-2xl font-bold text-blue-500">
                {progress ? `${Math.round((progress.overall_progress?.understanding_level || 0) * 100)}%` : '0%'}
              </p>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Stats Grid */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
      >
        {stats.map((stat, index) => (
          <motion.div
            key={stat.name}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: index * 0.1 }}
            className="card hover:shadow-strong transition-all duration-200"
          >
            <div className="flex items-center">
              <div className={`p-3 rounded-lg ${stat.color}`}>
                <stat.icon className="h-6 w-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
              </div>
            </div>
          </motion.div>
        ))}
      </motion.div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Continue Learning */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="lg:col-span-2"
        >
          <div className="card">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-900">Continue Learning</h2>
              <button className="text-blue-600 hover:text-blue-700 text-sm font-medium flex items-center">
                View all <ChevronRight className="h-4 w-4 ml-1" />
              </button>
            </div>
            {learningPaths.length === 0 ? (
              <div className="text-center py-8">
                <BookOpen className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">Start Your Learning Journey</h3>
                <p className="text-gray-500 mb-4">Create your first learning path to begin conversational learning with AI.</p>
                <button className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors flex items-center space-x-2 mx-auto">
                  <Plus className="h-4 w-4" />
                  <span>Start Learning</span>
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {learningPaths.slice(0, 3).map((path) => (
                  <div key={path.id} className="flex items-center space-x-4 p-4 rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50/50 transition-all duration-200 group">
                    <div className="w-16 h-16 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-sm font-bold">
                      {path.topic_name.charAt(0).toUpperCase()}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-gray-900 truncate">{path.topic_name}</h3>
                      <p className="text-sm text-gray-500 mb-2 truncate">{path.description}</p>
                      <div className="flex items-center space-x-2">
                        <div className="flex-1 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${(path.progress_count / path.total_topics) * 100}%` }}
                          ></div>
                        </div>
                        <span className="text-xs text-gray-500">{Math.round((path.progress_count / path.total_topics) * 100)}%</span>
                      </div>
                      <p className="text-xs text-gray-400 mt-1">{path.progress_count}/{path.total_topics} topics • {path.estimated_total_hours}h estimated</p>
                    </div>
                    <button className="p-2 text-blue-600 hover:bg-blue-100 rounded-lg transition-colors opacity-0 group-hover:opacity-100">
                      <MessageSquare className="h-5 w-5" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </motion.div>

        {/* Sidebar Content */}
        <div className="space-y-6">
          {/* Learning Progress */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
            className="card"
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Learning Progress</h3>

            {progress && progress.learning_paths.length > 0 ? (
              <div className="space-y-3">
                {progress.learning_paths.slice(0, 3).map((path) => (
                  <div key={path.id} className="flex items-center space-x-3 p-3 border border-gray-100 rounded-lg">
                    <div className={`w-3 h-3 rounded-full ${
                      path.progress >= 80 ? 'bg-green-500' :
                      path.progress >= 50 ? 'bg-yellow-500' : 'bg-blue-500'
                    }`}></div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">{path.topic_name}</p>
                      <p className="text-xs text-gray-500 truncate">
                        {path.current_topic || 'Not started'}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-gray-900">{Math.round(path.progress)}%</p>
                      <p className="text-xs text-gray-500">Progress</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-4">
                <BarChart3 className="h-8 w-8 text-gray-300 mx-auto mb-2" />
                <p className="text-sm text-gray-500">No learning progress yet</p>
              </div>
            )}
          </motion.div>

          {/* Overall Progress */}
          {progress && (
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.5 }}
              className="card"
            >
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Overall Progress</h3>
              <div className="space-y-4">
                <div className="text-center p-3 bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg border border-blue-200">
                  <Brain className="h-6 w-6 text-blue-500 mx-auto mb-1" />
                  <p className="text-lg font-bold text-blue-600">
                    {Math.round(progress.overall_progress.understanding_level * 100)}%
                  </p>
                  <p className="text-xs text-gray-600">Understanding</p>
                </div>
                <div className="text-center p-3 bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg border border-green-200">
                  <Trophy className="h-6 w-6 text-green-500 mx-auto mb-1" />
                  <p className="text-lg font-bold text-green-600">
                    {progress.overall_progress.concepts_mastered}
                  </p>
                  <p className="text-xs text-gray-600">Mastered</p>
                </div>
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  )
}