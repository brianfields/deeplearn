'use client'

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Separator } from '@/components/ui/separator'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  Brain,
  MessageSquare,
  TrendingUp,
  Clock,
  Target,
  AlertTriangle,
  CheckCircle,
  Info,
  Zap,
  BookOpen,
  Circle,
  CheckCircle2,
  Play,
  Trophy,
  Users
} from 'lucide-react'

interface DebugData {
  // Current session state
  current_phase?: string
  strategy_used?: string
  session_duration?: number
  message_count?: number

  // Student model state
  understanding_level?: number
  engagement_score?: number
  confusion_level?: number
  learning_velocity?: number
  needs_encouragement?: boolean

  // Strategy decision info
  strategy_confidence?: number
  strategy_reasoning?: string
  available_strategies?: string[]

  // Enhanced progress tracking
  concepts_covered?: string[]
  concepts_mastered?: string[]
  objectives_covered?: string[]

  // New detailed progress fields
  topic_title?: string
  learning_objectives?: Array<{
    text: string
    status: 'not_started' | 'introduced' | 'practicing' | 'tested' | 'mastered'
  }>
  key_concepts?: Array<{
    name: string
    status: 'not_covered' | 'introduced' | 'practicing' | 'understood' | 'mastered'
    definition?: string
  }>
  sub_topics?: Array<{
    name: string
    status: 'upcoming' | 'current' | 'completed'
    progress_percentage?: number
  }>

  // Performance history
  recent_performance?: Array<{
    understanding: number
    engagement: number
    timestamp: string
  }>
}

interface DebugPanelProps {
  debugData: DebugData
  isVisible?: boolean
}

export default function DebugPanel({ debugData, isVisible = true }: DebugPanelProps) {
  // Only show in development
  if (process.env.NODE_ENV !== 'development' || !isVisible) {
    return null
  }

  const getPhaseColor = (phase?: string) => {
    switch (phase?.toLowerCase()) {
      case 'introduction': return 'bg-blue-100 text-blue-800'
      case 'exploration': return 'bg-green-100 text-green-800'
      case 'practice': return 'bg-orange-100 text-orange-800'
      case 'assessment': return 'bg-purple-100 text-purple-800'
      case 'consolidation': return 'bg-gray-100 text-gray-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getStrategyColor = (strategy?: string) => {
    switch (strategy?.toLowerCase()) {
      case 'direct_instruction': return 'bg-red-100 text-red-800'
      case 'socratic_inquiry': return 'bg-blue-100 text-blue-800'
      case 'guided_practice': return 'bg-green-100 text-green-800'
      case 'assessment': return 'bg-purple-100 text-purple-800'
      case 'encouragement': return 'bg-yellow-100 text-yellow-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const formatDuration = (minutes?: number) => {
    if (!minutes) return '0m'
    const mins = Math.floor(minutes)
    const secs = Math.floor((minutes - mins) * 60)
    return `${mins}m ${secs}s`
  }

  const getScoreColor = (score?: number) => {
    if (!score) return 'text-gray-500'
    if (score >= 0.8) return 'text-green-600'
    if (score >= 0.6) return 'text-yellow-600'
    if (score >= 0.4) return 'text-orange-600'
    return 'text-red-600'
  }

  const getObjectiveStatusIcon = (status: string) => {
    switch (status) {
      case 'mastered': return <Trophy className="h-3 w-3 text-yellow-500" />
      case 'tested': return <CheckCircle2 className="h-3 w-3 text-green-500" />
      case 'practicing': return <Play className="h-3 w-3 text-orange-500" />
      case 'introduced': return <Circle className="h-3 w-3 text-blue-500" />
      default: return <Circle className="h-3 w-3 text-gray-300" />
    }
  }

  const getObjectiveStatusColor = (status: string) => {
    switch (status) {
      case 'mastered': return 'text-yellow-700 bg-yellow-50 border-yellow-200'
      case 'tested': return 'text-green-700 bg-green-50 border-green-200'
      case 'practicing': return 'text-orange-700 bg-orange-50 border-orange-200'
      case 'introduced': return 'text-blue-700 bg-blue-50 border-blue-200'
      default: return 'text-gray-500 bg-gray-50 border-gray-200'
    }
  }

  const getConceptStatusColor = (status: string) => {
    switch (status) {
      case 'mastered': return 'bg-green-100 text-green-800'
      case 'understood': return 'bg-blue-100 text-blue-800'
      case 'practicing': return 'bg-orange-100 text-orange-800'
      case 'introduced': return 'bg-purple-100 text-purple-800'
      default: return 'bg-gray-100 text-gray-600'
    }
  }

  const getSubTopicStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle className="h-3 w-3 text-green-500" />
      case 'current': return <Play className="h-3 w-3 text-blue-500" />
      default: return <Circle className="h-3 w-3 text-gray-300" />
    }
  }

  return (
    <Card className="w-full max-w-sm bg-gray-50 border-2 border-dashed border-gray-300">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium text-gray-700 flex items-center gap-2">
          <Info className="h-4 w-4" />
          Learning Progress
          <Badge variant="outline" className="text-xs">DEV</Badge>
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        <ScrollArea className="h-[500px]">
          <div className="space-y-4">

            {/* Topic Overview */}
            {debugData.topic_title && (
              <div>
                <h4 className="text-xs font-semibold text-gray-600 mb-2 flex items-center gap-1">
                  <BookOpen className="h-3 w-3" />
                  Current Topic
                </h4>
                <div className="p-2 bg-blue-50 rounded border border-blue-200">
                  <p className="text-sm font-medium text-blue-800">{debugData.topic_title}</p>
                </div>
              </div>
            )}

            {/* Learning Objectives Progress */}
            {debugData.learning_objectives && debugData.learning_objectives.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-gray-600 mb-2 flex items-center gap-1">
                  <Target className="h-3 w-3" />
                  Learning Objectives
                </h4>
                <div className="space-y-2">
                  {debugData.learning_objectives.map((objective, idx) => (
                    <div key={idx} className={`p-2 rounded border text-xs ${getObjectiveStatusColor(objective.status)}`}>
                      <div className="flex items-start gap-2">
                        {getObjectiveStatusIcon(objective.status)}
                        <div className="flex-1">
                          <p className="text-xs leading-relaxed">{objective.text}</p>
                          <Badge className={`text-xs mt-1 ${getObjectiveStatusColor(objective.status)}`}>
                            {objective.status.replace('_', ' ')}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Sub-topics Progress */}
            {debugData.sub_topics && debugData.sub_topics.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-gray-600 mb-2 flex items-center gap-1">
                  <Users className="h-3 w-3" />
                  Topic Breakdown
                </h4>
                <div className="space-y-2">
                  {debugData.sub_topics.map((topic, idx) => (
                    <div key={idx} className="p-2 bg-white rounded border">
                      <div className="flex items-center gap-2 mb-1">
                        {getSubTopicStatusIcon(topic.status)}
                        <span className="text-xs font-medium flex-1">{topic.name}</span>
                        <Badge variant="outline" className="text-xs">
                          {topic.status}
                        </Badge>
                      </div>
                      {topic.progress_percentage !== undefined && (
                        <Progress value={topic.progress_percentage} className="h-1 mt-1" />
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Key Concepts */}
            {debugData.key_concepts && debugData.key_concepts.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-gray-600 mb-2 flex items-center gap-1">
                  <Brain className="h-3 w-3" />
                  Key Concepts
                </h4>
                <div className="space-y-2">
                  {debugData.key_concepts.map((concept, idx) => (
                    <div key={idx} className="p-2 bg-white rounded border">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-medium">{concept.name}</span>
                        <Badge className={`text-xs ${getConceptStatusColor(concept.status)}`}>
                          {concept.status.replace('_', ' ')}
                        </Badge>
                      </div>
                      {concept.definition && (
                        <p className="text-xs text-gray-600 mt-1">{concept.definition}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            <Separator />

            {/* Current Session State */}
            <div>
              <h4 className="text-xs font-semibold text-gray-600 mb-2 flex items-center gap-1">
                <MessageSquare className="h-3 w-3" />
                Session State
              </h4>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-500">Phase:</span>
                  <Badge className={`text-xs ${getPhaseColor(debugData.current_phase)}`}>
                    {debugData.current_phase || 'unknown'}
                  </Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-500">Strategy:</span>
                  <Badge className={`text-xs ${getStrategyColor(debugData.strategy_used)}`}>
                    {debugData.strategy_used?.replace('_', ' ') || 'unknown'}
                  </Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-500">Duration:</span>
                  <span className="text-xs font-medium">
                    {formatDuration(debugData.session_duration)}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-500">Messages:</span>
                  <span className="text-xs font-medium">
                    {debugData.message_count || 0}
                  </span>
                </div>
              </div>
            </div>

            <Separator />

            {/* Student Model State - Compact */}
            <div>
              <h4 className="text-xs font-semibold text-gray-600 mb-2 flex items-center gap-1">
                <Brain className="h-3 w-3" />
                Student Metrics
              </h4>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="text-center p-2 bg-white rounded border">
                  <div className={`font-semibold ${getScoreColor(debugData.understanding_level)}`}>
                    {Math.round((debugData.understanding_level || 0) * 100)}%
                  </div>
                  <div className="text-gray-500">Understanding</div>
                </div>
                <div className="text-center p-2 bg-white rounded border">
                  <div className={`font-semibold ${getScoreColor(debugData.engagement_score)}`}>
                    {Math.round((debugData.engagement_score || 0) * 100)}%
                  </div>
                  <div className="text-gray-500">Engagement</div>
                </div>
                <div className="text-center p-2 bg-white rounded border">
                  <div className={`font-semibold ${getScoreColor(1 - (debugData.confusion_level || 0))}`}>
                    {Math.round((debugData.confusion_level || 0) * 100)}%
                  </div>
                  <div className="text-gray-500">Confusion</div>
                </div>
                <div className="text-center p-2 bg-white rounded border">
                  <div className="font-semibold text-blue-600">
                    {debugData.learning_velocity?.toFixed(2) || '0.00'}
                  </div>
                  <div className="text-gray-500">Velocity</div>
                </div>
              </div>

              {debugData.needs_encouragement && (
                <div className="flex items-center gap-2 p-2 bg-yellow-50 rounded border mt-2">
                  <AlertTriangle className="h-3 w-3 text-yellow-600" />
                  <span className="text-xs text-yellow-700">Needs Encouragement</span>
                </div>
              )}
            </div>

            {/* Strategy Decision - Compact */}
            {(debugData.strategy_confidence || debugData.strategy_reasoning) && (
              <>
                <Separator />
                <div>
                  <h4 className="text-xs font-semibold text-gray-600 mb-2 flex items-center gap-1">
                    <Target className="h-3 w-3" />
                    AI Decision
                  </h4>
                  {debugData.strategy_confidence && (
                    <div className="mb-2">
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-xs text-gray-500">Confidence</span>
                        <span className="text-xs font-medium">
                          {Math.round(debugData.strategy_confidence * 100)}%
                        </span>
                      </div>
                      <Progress value={debugData.strategy_confidence * 100} className="h-1" />
                    </div>
                  )}

                  {debugData.strategy_reasoning && (
                    <div className="p-2 bg-blue-50 rounded border">
                      <p className="text-xs text-blue-700">
                        {debugData.strategy_reasoning}
                      </p>
                    </div>
                  )}
                </div>
              </>
            )}

            {/* Legacy Progress (if no detailed progress available) */}
            {(!debugData.learning_objectives && !debugData.key_concepts && !debugData.sub_topics) && (
              <>
                <Separator />
                <div>
                  <h4 className="text-xs font-semibold text-gray-600 mb-2 flex items-center gap-1">
                    <CheckCircle className="h-3 w-3" />
                    Basic Progress
                  </h4>
                  <div className="space-y-2">
                    {debugData.concepts_covered && debugData.concepts_covered.length > 0 && (
                      <div>
                        <span className="text-xs text-gray-500 block mb-1">Concepts Covered:</span>
                        <div className="flex flex-wrap gap-1">
                          {debugData.concepts_covered.map((concept, idx) => (
                            <Badge key={idx} variant="outline" className="text-xs">
                              {concept}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    {debugData.concepts_mastered && debugData.concepts_mastered.length > 0 && (
                      <div>
                        <span className="text-xs text-gray-500 block mb-1">Mastered:</span>
                        <div className="flex flex-wrap gap-1">
                          {debugData.concepts_mastered.map((concept, idx) => (
                            <Badge key={idx} className="text-xs bg-green-100 text-green-800">
                              {concept}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </>
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  )
}