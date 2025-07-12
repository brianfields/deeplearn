'use client'

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Separator } from '@/components/ui/separator'
import { TrendingUp, Clock, Target, BookOpen } from 'lucide-react'
import { ProgressUpdate, SessionState } from '@/types'
import DebugPanel from './DebugPanel'

interface ProgressSidebarProps {
  progress: ProgressUpdate | null
  sessionState: SessionState | null
  topicTitle: string
  messageCount: number
}

export default function ProgressSidebar({
  progress,
  sessionState,
  topicTitle,
  messageCount
}: ProgressSidebarProps) {
  // Map session state and progress to debug data format
  const debugData = {
    // Session state
    current_phase: sessionState?.phase || 'unknown',
    strategy_used: sessionState?.last_strategy || 'unknown',
    session_duration: sessionState?.session_duration_minutes || 0,
    message_count: messageCount,

    // Student metrics
    understanding_level: progress?.understanding_level || 0,
    engagement_score: progress?.engagement_score || 0,
    confusion_level: sessionState?.confusion_level || 0,
    learning_velocity: sessionState?.learning_velocity || 0,
    needs_encouragement: sessionState?.needs_encouragement || false,

    // Strategy decisions
    strategy_confidence: sessionState?.strategy_confidence || 0,
    strategy_reasoning: sessionState?.strategy_reasoning || '',
    available_strategies: sessionState?.available_strategies || [],

    // Enhanced progress data
    topic_title: progress?.topic_title || topicTitle,
    learning_objectives: progress?.learning_objectives || [],
    key_concepts: progress?.key_concepts || [],
    sub_topics: progress?.sub_topics || [],

    // Legacy progress
    concepts_covered: [],
    concepts_mastered: progress?.key_concepts?.filter(c => c.status === 'mastered').map(c => c.name) || [],
    objectives_covered: progress?.objectives_covered || [],
    recent_performance: sessionState?.performance_history?.map(entry => ({
      understanding: entry.metric === 'understanding' ? entry.value : 0,
      engagement: entry.metric === 'engagement' ? entry.value : 0,
      timestamp: entry.timestamp
    })) || []
  }

  return (
    <div className="w-80 h-full flex-shrink-0 border-l bg-gray-50/50 backdrop-blur-sm">
      <div className="h-full overflow-y-auto p-4 space-y-4">
        {/* Progress Overview */}
        <Card className="shadow-sm border-0 bg-white/70 backdrop-blur-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm flex items-center gap-2 text-gray-700">
              <TrendingUp className="h-4 w-4" />
              Learning Progress
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-600">Understanding</span>
                <span className="font-medium text-gray-900">
                  {Math.round((progress?.understanding_level || 0) * 100)}%
                </span>
              </div>
              <Progress
                value={(progress?.understanding_level || 0) * 100}
                className="h-2"
              />
            </div>

            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-600">Engagement</span>
                <span className="font-medium text-gray-900">
                  {Math.round((progress?.engagement_score || 0) * 100)}%
                </span>
              </div>
              <Progress
                value={(progress?.engagement_score || 0) * 100}
                className="h-2"
              />
            </div>

            <Separator className="my-3" />

            <div>
              <div className="flex items-center gap-2 mb-2">
                <Clock className="h-4 w-4 text-gray-500" />
                <span className="text-sm font-medium text-gray-700">Session Info</span>
              </div>
              <div className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Duration</span>
                  <span className="text-gray-900">
                    {sessionState?.session_duration_minutes || 0} min
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Messages</span>
                  <span className="text-gray-900">{messageCount}</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Learning Objectives */}
        <Card className="shadow-sm border-0 bg-white/70 backdrop-blur-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm flex items-center gap-2 text-gray-700">
              <Target className="h-4 w-4" />
              Learning Objectives
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {progress?.learning_objectives?.map((objective, idx) => (
                <div key={idx} className="flex items-start gap-2">
                  <div className={`w-2 h-2 rounded-full mt-2 flex-shrink-0 ${
                    objective.status === 'mastered' ? 'bg-green-500' :
                    objective.status === 'introduced' ? 'bg-yellow-500' :
                    'bg-gray-300'
                  }`} />
                  <span className={`text-sm ${
                    objective.status === 'mastered' ? 'text-green-700' :
                    objective.status === 'introduced' ? 'text-yellow-700' :
                    'text-gray-600'
                  }`}>
                    {objective.text}
                  </span>
                </div>
              ))}
              {(!progress?.learning_objectives || progress?.learning_objectives?.length === 0) && (
                <span className="text-sm text-gray-500">No objectives set yet</span>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Key Concepts */}
        <Card className="shadow-sm border-0 bg-white/70 backdrop-blur-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm flex items-center gap-2 text-gray-700">
              <BookOpen className="h-4 w-4" />
              Key Concepts
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {progress?.key_concepts?.map((concept, idx) => (
                <Badge
                  key={idx}
                  variant={concept.status === 'mastered' ? 'default' : 'secondary'}
                  className={`text-xs ${
                    concept.status === 'mastered' ? 'bg-green-100 text-green-800' :
                    concept.status === 'introduced' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-gray-100 text-gray-600'
                  }`}
                >
                  {concept.name}
                </Badge>
              ))}
              {(!progress?.key_concepts || progress?.key_concepts?.length === 0) && (
                <span className="text-sm text-gray-500">No concepts covered yet</span>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Current Phase */}
        <Card className="shadow-sm border-0 bg-white/70 backdrop-blur-sm">
          <CardContent className="pt-4">
            <div className="text-center">
              <div className="text-sm text-gray-600 mb-1">Current Phase</div>
              <Badge className="text-xs bg-blue-100 text-blue-800">
                {sessionState?.phase || 'Getting Started'}
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* Debug Panel */}
        <DebugPanel debugData={debugData} />
      </div>
    </div>
  )
}