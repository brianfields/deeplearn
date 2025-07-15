'use client'

import { useState, useEffect, useCallback } from 'react'
import { useParams, useSearchParams } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ArrowLeft,
  Book,
  Clock,
  Target,
  Brain,
  Loader2,
  AlertCircle,
  ChevronDown,
  ChevronRight,
  Play,
  Eye,
  Zap,
  Flame
} from 'lucide-react'
import Link from 'next/link'
import { apiClient } from '@/api'
import DuolingoLearningFlow from '@/components/learning/DuolingoLearningFlow'
import { duolingoLearningService } from '@/services/duolingo-learning'
import type { BiteSizedTopicDetail } from '@/types'

interface CollapsibleSectionProps {
  title: string
  children: React.ReactNode
  defaultOpen?: boolean
}

function CollapsibleSection({ title, children, defaultOpen = false }: CollapsibleSectionProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen)

  return (
    <div className="border border-slate-200 rounded-lg overflow-hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-6 py-4 bg-slate-50 hover:bg-slate-100 flex items-center justify-between transition-colors"
      >
        <h4 className="text-lg font-semibold text-slate-900">{title}</h4>
        {isOpen ? (
          <ChevronDown className="w-5 h-5 text-slate-600" />
        ) : (
          <ChevronRight className="w-5 h-5 text-slate-600" />
        )}
      </button>
      {isOpen && (
        <motion.div
          initial={{ height: 0 }}
          animate={{ height: 'auto' }}
          exit={{ height: 0 }}
          className="overflow-hidden"
        >
          <div className="p-6 bg-white">
            {children}
          </div>
        </motion.div>
      )}
    </div>
  )
}

function JsonDisplay({ data, title }: { data: any, title?: string }) {
  const formatValue = (value: any): React.ReactNode => {
    if (value === null || value === undefined) {
      return <span className="text-slate-400 italic">null</span>
    }

    if (typeof value === 'boolean') {
      return <span className="text-purple-600 font-medium">{value.toString()}</span>
    }

    if (typeof value === 'number') {
      return <span className="text-blue-600 font-medium">{value}</span>
    }

    if (typeof value === 'string') {
      // Check if it looks like HTML content
      if (value.includes('<') && value.includes('>')) {
        return (
          <div className="mt-2">
            <div className="prose prose-sm max-w-none p-4 bg-slate-50 rounded border">
              <div dangerouslySetInnerHTML={{ __html: value }} />
            </div>
          </div>
        )
      }
      return <span className="text-green-700">{value}</span>
    }

    if (Array.isArray(value)) {
      return (
        <div className="ml-4 space-y-2">
          {value.map((item, index) => (
            <div key={index} className="border-l-2 border-slate-200 pl-4">
              <div className="text-sm text-slate-500 mb-1">Item {index + 1}:</div>
              {formatValue(item)}
            </div>
          ))}
        </div>
      )
    }

    if (typeof value === 'object') {
      return (
        <div className="ml-4 space-y-3">
          {Object.entries(value).map(([key, val]) => (
            <div key={key} className="border-l-2 border-slate-200 pl-4">
              <div className="font-medium text-slate-700 mb-1">{key}:</div>
              {formatValue(val)}
            </div>
          ))}
        </div>
      )
    }

    return <span className="text-slate-600">{String(value)}</span>
  }

  return (
    <div className="bg-slate-50 rounded-lg p-4 border">
      {title && <h5 className="font-semibold text-slate-900 mb-3">{title}</h5>}
      {formatValue(data)}
    </div>
  )
}

function ComponentRenderer({ component }: { component: any }) {
  const getComponentColor = (type: string) => {
    switch (type) {
      case 'didactic_snippet': return 'blue'
      case 'glossary': return 'indigo'
      case 'socratic_dialogue': return 'amber'
      case 'short_answer_question': return 'green'
      case 'multiple_choice_question': return 'emerald'
      case 'post_topic_quiz': return 'purple'
      default: return 'gray'
    }
  }

  const getDescriptiveTitle = (component: any) => {
    const baseType = component.component_type.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())
    const content = component.content

    switch (component.component_type) {
      case 'didactic_snippet':
        if (content.title) {
          return `${baseType}: ${content.title}`
        }
        break

      case 'glossary':
        if (content.concept) {
          return `${baseType}: ${content.concept}`
        }
        break

      case 'multiple_choice_question':
        if (Array.isArray(content) && content[0]?.question) {
          const question = content[0].question
          const truncated = question.length > 60 ? question.substring(0, 60) + '...' : question
          return `${baseType}: ${truncated}`
        } else if (content.question) {
          const question = content.question
          const truncated = question.length > 60 ? question.substring(0, 60) + '...' : question
          return `${baseType}: ${truncated}`
        }
        break

      case 'short_answer_question':
        if (Array.isArray(content) && content[0]?.question) {
          const question = content[0].question
          const truncated = question.length > 60 ? question.substring(0, 60) + '...' : question
          return `${baseType}: ${truncated}`
        } else if (content.question) {
          const question = content.question
          const truncated = question.length > 60 ? question.substring(0, 60) + '...' : question
          return `${baseType}: ${truncated}`
        }
        break

      case 'post_topic_quiz':
        if (Array.isArray(content) && content[0]) {
          const item = content[0]
          if (item.question) {
            const question = item.question
            const truncated = question.length > 60 ? question.substring(0, 60) + '...' : question
            const type = item.type ? ` (${item.type})` : ''
            return `${baseType}${type}: ${truncated}`
          }
        } else if (content.question) {
          const question = content.question
          const truncated = question.length > 60 ? question.substring(0, 60) + '...' : question
          const type = content.type ? ` (${content.type})` : ''
          return `${baseType}${type}: ${truncated}`
        }
        break

      case 'socratic_dialogue':
        if (Array.isArray(content) && content[0]) {
          const dialogue = content[0]
          if (dialogue.concept) {
            return `${baseType}: ${dialogue.concept}`
          } else if (dialogue.starting_prompt || dialogue['Starting Prompt']) {
            const prompt = dialogue.starting_prompt || dialogue['Starting Prompt']
            const truncated = prompt.length > 60 ? prompt.substring(0, 60) + '...' : prompt
            return `${baseType}: ${truncated}`
          }
        } else if (content.concept) {
          return `${baseType}: ${content.concept}`
        } else if (content.starting_prompt) {
          const prompt = content.starting_prompt
          const truncated = prompt.length > 60 ? prompt.substring(0, 60) + '...' : prompt
          return `${baseType}: ${truncated}`
        }
        break
    }

    return baseType
  }

  const color = getComponentColor(component.component_type)
  const bgClass = `bg-${color}-50`
  const borderClass = `border-${color}-200`
  const textClass = `text-${color}-900`

  return (
    <CollapsibleSection
      title={getDescriptiveTitle(component)}
    >
      <div className={`${bgClass} ${borderClass} border rounded-lg p-4`}>
        <JsonDisplay
          data={component.content}
          title={`${component.component_type} Content`}
        />
      </div>
    </CollapsibleSection>
  )
}

export default function TopicContentPage() {
  const params = useParams()
  const searchParams = useSearchParams()
  const topicId = params?.id as string
  const [topic, setTopic] = useState<BiteSizedTopicDetail | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isPreloading, setIsPreloading] = useState(false)

  // Check if we should start in learning mode and which flow to use
  const initialMode = searchParams.get('mode') === 'learning' ? 'learning' : 'overview'
  const useDuolingoFlow = searchParams.get('duolingo') === 'true' || searchParams.get('mode') === 'learning'
  const [viewMode, setViewMode] = useState<'overview' | 'content' | 'learning'>(initialMode)

  const loadTopic = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)

      // Use Duolingo service for optimized loading
      const topicData = await duolingoLearningService.loadTopic(topicId, true)
      setTopic(topicData)

      // Start preloading next topics in background
      setIsPreloading(true)
      // Preloading happens automatically in the service
      setTimeout(() => setIsPreloading(false), 2000)

    } catch (err) {
      // Fallback to regular API if Duolingo service fails
      try {
        const topicData = await apiClient.getBiteSizedTopicDetail(topicId)
        setTopic(topicData)
      } catch (fallbackErr) {
        setError(err instanceof Error ? err.message : 'Failed to load topic')
      }
    } finally {
      setIsLoading(false)
    }
  }, [topicId])

  useEffect(() => {
    if (topicId) {
      loadTopic()
    }
  }, [topicId, loadTopic])

  const handleLearningComplete = (results: any) => {
    console.log('Learning completed:', results)
    // If we came from learning mode, go back to learn page after completion
    if (searchParams.get('mode') === 'learning') {
      setTimeout(() => {
        window.location.href = '/learn'
      }, 3000) // Give user time to see completion screen
    } else {
      setViewMode('overview')
    }
  }

  const handleBackToOverview = () => {
    // If we came from learning mode, go back to learn page
    if (searchParams.get('mode') === 'learning') {
      window.location.href = '/learn'
    } else {
      setViewMode('overview')
    }
  }

  // Get offline availability status
  const isAvailableOffline = topic ? duolingoLearningService.isTopicAvailableOffline(topic.id) : false
  const cacheStats = duolingoLearningService.getCacheStats()

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-4" />
          <p className="text-gray-600">
            {isPreloading ? 'Optimizing for fast learning...' : 'Loading topic content...'}
          </p>
          {isPreloading && (
            <p className="text-xs text-gray-500 mt-2">
              Preloading next topics for offline use
            </p>
          )}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Error Loading Topic</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={loadTopic}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    )
  }

  if (!topic) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Book className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Topic Not Found</h2>
          <p className="text-gray-600">The requested topic could not be found.</p>
        </div>
      </div>
    )
  }

  // Show Duolingo learning flow if enabled
  if (viewMode === 'learning' && useDuolingoFlow) {
    return (
      <DuolingoLearningFlow
        topic={topic}
        onComplete={handleLearningComplete}
        onBack={handleBackToOverview}
      />
    )
  }

  // Show regular learning flow if in learning mode but not Duolingo
  if (viewMode === 'learning') {
    return (
      <DuolingoLearningFlow
        topic={topic}
        onComplete={handleLearningComplete}
        onBack={handleBackToOverview}
      />
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <Link
              href="/learn"
              className="inline-flex items-center text-gray-600 hover:text-gray-900 transition-colors"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Learn
            </Link>

            {/* Cache status indicators */}
            <div className="flex items-center gap-3 text-sm">
              {isAvailableOffline && (
                <div className="flex items-center gap-1 text-green-600">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span>Available offline</span>
                </div>
              )}
              {cacheStats.currentStreak > 0 && (
                <div className="flex items-center gap-1 text-orange-600">
                  <Flame className="w-4 h-4" />
                  <span>{cacheStats.currentStreak} day streak</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Topic overview */}
      <div className="max-w-4xl mx-auto px-4 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden"
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h1 className="text-3xl font-bold mb-2">{topic.title}</h1>
                <p className="text-blue-100 text-lg mb-4">{topic.core_concept}</p>
                <div className="flex items-center gap-4 text-sm">
                  <div className="flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    <span>~15 minutes</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Target className="w-4 h-4" />
                    <span>{topic.learning_objectives.length} objectives</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Brain className="w-4 h-4" />
                    <span>{topic.components.length} components</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Action buttons */}
          <div className="p-6 border-b border-gray-200">
            <div className="flex flex-col sm:flex-row gap-3">
              <button
                onClick={() => setViewMode('learning')}
                className="flex-1 bg-gradient-to-r from-green-600 to-blue-600 text-white py-3 px-6 rounded-lg font-medium flex items-center justify-center gap-2 hover:from-green-700 hover:to-blue-700 transition-all"
              >
                <Zap className="w-5 h-5" />
                Start Duolingo-style Learning
              </button>
              <button
                onClick={() => {
                  const url = new URL(window.location.href)
                  url.searchParams.set('duolingo', 'false')
                  window.location.href = url.toString()
                  setViewMode('learning')
                }}
                className="flex-1 bg-blue-600 text-white py-3 px-6 rounded-lg font-medium flex items-center justify-center gap-2 hover:bg-blue-700 transition-colors"
              >
                <Play className="w-5 h-5" />
                Standard Learning Mode
              </button>
              <button
                onClick={() => setViewMode('content')}
                className="flex-1 border border-gray-300 text-gray-700 py-3 px-6 rounded-lg font-medium flex items-center justify-center gap-2 hover:bg-gray-50 transition-colors"
              >
                <Eye className="w-5 h-5" />
                Browse Content
              </button>
            </div>
          </div>

          {/* Overview Section */}
          {viewMode === 'overview' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-8"
            >
              <h2 className="text-xl font-semibold text-gray-900 mb-6">Topic Overview</h2>

              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div>
                  <h3 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                    <Target className="w-5 h-5 text-blue-500" />
                    Learning Objectives
                  </h3>
                  <ul className="space-y-2">
                    {topic.learning_objectives?.map((objective: string, index: number) => (
                      <li key={index} className="text-gray-600 text-sm">
                        • {objective}
                      </li>
                    ))}
                  </ul>
                </div>

                <div>
                  <h3 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                    <Brain className="w-5 h-5 text-purple-500" />
                    Key Concepts
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {topic.key_concepts?.map((concept: string, index: number) => (
                      <span
                        key={index}
                        className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm"
                      >
                        {concept}
                      </span>
                    ))}
                  </div>
                </div>

                <div>
                  <h3 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                    <Clock className="w-5 h-5 text-green-500" />
                    Duration & Details
                  </h3>
                  <div className="space-y-2 text-sm text-gray-600">
                    <div>Created: {new Date(topic.created_at).toLocaleDateString()}</div>
                    <div>Updated: {new Date(topic.updated_at).toLocaleDateString()}</div>
                    <div>Components: {topic.components?.length || 0}</div>
                  </div>
                </div>
              </div>

              {topic.key_aspects && topic.key_aspects.length > 0 && (
                <div className="mt-6 pt-6 border-t border-gray-200">
                  <h3 className="font-medium text-gray-900 mb-3">Key Aspects</h3>
                  <ul className="grid md:grid-cols-2 gap-2">
                    {topic.key_aspects.map((aspect: string, index: number) => (
                      <li key={index} className="text-gray-600 text-sm">
                        • {aspect}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </motion.div>
          )}

          {/* Content Components */}
          {viewMode === 'content' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-white rounded-xl shadow-sm border border-gray-200 p-6"
            >
              <h2 className="text-xl font-semibold text-gray-900 mb-6">Content Components</h2>

              <div className="space-y-4">
                {topic.components?.map((component: any, index: number) => (
                  <ComponentRenderer key={index} component={component} />
                ))}
              </div>
            </motion.div>
          )}
        </motion.div>
      </div>
    </div>
  )
}