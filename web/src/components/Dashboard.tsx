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
import { useLearningPaths } from '@/hooks/useLearningPaths'
import { useRouter } from 'next/navigation'

export default function Dashboard() {
  const { learningPaths: rawLearningPaths, isLoading, error, stats, refreshPaths } = useLearningPaths()
  const router = useRouter()

  // Ensure learningPaths is always an array to prevent undefined errors
  const learningPaths = rawLearningPaths || []

  const handleViewAllPaths = () => {
    router.push('/learn')
  }

  const handleStartLearning = () => {
    router.push('/learn')
  }

  const handleOpenPath = (pathId: string) => {
    router.push(`/learn?path=${pathId}`)
  }

  const dashboardStats = stats ? [
    {
      name: 'Learning Paths',
      value: stats.totalPaths.toString(),
      icon: BookOpen,
      color: 'bg-blue-500'
    },
    {
      name: 'Completed',
      value: stats.completedPaths.toString(),
      icon: CheckCircle,
      color: 'bg-green-500'
    },
    {
      name: 'Average Progress',
      value: `${Math.round(stats.averageProgress)}%`,
      icon: Brain,
      color: 'bg-purple-500'
    },
    {
      name: 'Total Topics',
      value: stats.totalTopics.toString(),
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
            onClick={refreshPaths}
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
                {stats ? `${Math.round(stats.averageProgress)}%` : '0%'}
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
        {dashboardStats.map((stat, index) => (
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
              <button
                onClick={handleViewAllPaths}
                className="text-blue-600 hover:text-blue-700 text-sm font-medium flex items-center"
              >
                View all <ChevronRight className="h-4 w-4 ml-1" />
              </button>
            </div>
            {learningPaths.length === 0 ? (
              <div className="text-center py-8">
                <BookOpen className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">Start Your Learning Journey</h3>
                <p className="text-gray-500 mb-4">Create your first learning path to begin conversational learning with AI.</p>
                <button
                  onClick={handleStartLearning}
                  className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors flex items-center space-x-2 mx-auto"
                >
                  <Plus className="h-4 w-4" />
                  <span>Start Learning</span>
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {learningPaths.slice(0, 3).map((path) => (
                  <div
                    key={path.id}
                    onClick={() => handleOpenPath(path.id)}
                    className="flex items-center space-x-4 p-4 rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50/50 transition-all duration-200 group cursor-pointer"
                  >
                    <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-lg font-bold">
                      {path.topic_name.charAt(0).toUpperCase()}
                    </div>
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900 group-hover:text-blue-700">{path.topic_name}</h3>
                      <p className="text-sm text-gray-500 mt-1">{path.description}</p>
                                              <div className="flex items-center space-x-4 mt-2">
                          <div className="flex items-center space-x-1 text-xs text-gray-500">
                            <BookOpen className="h-3 w-3" />
                            <span>{path.total_topics || 0} topics</span>
                          </div>
                          <div className="flex items-center space-x-1 text-xs text-gray-500">
                            <Clock className="h-3 w-3" />
                            <span>{path.estimated_total_hours || 0}h</span>
                          </div>
                        </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className="text-right">
                        <p className="text-sm font-medium text-gray-900">
                          {path.total_topics > 0 ? Math.round((path.progress_count / path.total_topics) * 100) : 0}%
                        </p>
                        <p className="text-xs text-gray-500">Complete</p>
                      </div>
                      <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center group-hover:bg-blue-100 transition-colors">
                        <Play className="h-4 w-4 text-gray-600 group-hover:text-blue-600" />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </motion.div>

        {/* Quick Actions */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
        >
          <div className="card">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">Quick Actions</h2>
            <div className="space-y-4">
              <button
                onClick={handleStartLearning}
                className="w-full flex items-center space-x-3 p-4 rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50/50 transition-all duration-200 group"
              >
                <div className="w-10 h-10 rounded-lg bg-blue-500 flex items-center justify-center">
                  <Plus className="h-5 w-5 text-white" />
                </div>
                <div className="flex-1 text-left">
                  <p className="font-medium text-gray-900 group-hover:text-blue-700">New Learning Path</p>
                  <p className="text-sm text-gray-500">Start learning something new</p>
                </div>
              </button>

              <button className="w-full flex items-center space-x-3 p-4 rounded-lg border border-gray-200 hover:border-purple-300 hover:bg-purple-50/50 transition-all duration-200 group">
                <div className="w-10 h-10 rounded-lg bg-purple-500 flex items-center justify-center">
                  <MessageSquare className="h-5 w-5 text-white" />
                </div>
                <div className="flex-1 text-left">
                  <p className="font-medium text-gray-900 group-hover:text-purple-700">AI Tutor Chat</p>
                  <p className="text-sm text-gray-500">Get help with any topic</p>
                </div>
              </button>

              <button className="w-full flex items-center space-x-3 p-4 rounded-lg border border-gray-200 hover:border-green-300 hover:bg-green-50/50 transition-all duration-200 group">
                <div className="w-10 h-10 rounded-lg bg-green-500 flex items-center justify-center">
                  <Target className="h-5 w-5 text-white" />
                </div>
                <div className="flex-1 text-left">
                  <p className="font-medium text-gray-900 group-hover:text-green-700">Practice Quiz</p>
                  <p className="text-sm text-gray-500">Test your knowledge</p>
                </div>
              </button>

              <button className="w-full flex items-center space-x-3 p-4 rounded-lg border border-gray-200 hover:border-orange-300 hover:bg-orange-50/50 transition-all duration-200 group">
                <div className="w-10 h-10 rounded-lg bg-orange-500 flex items-center justify-center">
                  <BarChart3 className="h-5 w-5 text-white" />
                </div>
                <div className="flex-1 text-left">
                  <p className="font-medium text-gray-900 group-hover:text-orange-700">Progress Report</p>
                  <p className="text-sm text-gray-500">View detailed analytics</p>
                </div>
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}