'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  ChevronDown,
  ChevronRight,
  Target,
  Lightbulb,
  AlertTriangle,
  CheckCircle,
  Brain,
  Loader2,
  Plus
} from 'lucide-react'

interface RefinedMaterialViewProps {
  topic: any
  onMCQCreated: (updatedTopic: any) => void
  onProceedToComponents: () => void
}

export default function RefinedMaterialView({ topic, onMCQCreated, onProceedToComponents }: RefinedMaterialViewProps) {
  const [openSections, setOpenSections] = useState<Set<string>>(new Set())
  const [creatingMCQ, setCreatingMCQ] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const toggleSection = (sectionId: string) => {
    const newOpenSections = new Set(openSections)
    if (newOpenSections.has(sectionId)) {
      newOpenSections.delete(sectionId)
    } else {
      newOpenSections.add(sectionId)
    }
    setOpenSections(newOpenSections)
  }

  const handleCreateMCQ = async (topicData: any, learningObjective: string) => {
    const mcqKey = `${topicData.topic}-${learningObjective}`
    setCreatingMCQ(mcqKey)
    setError(null)

    try {
      const response = await fetch(`/api/content/topics/${topic.id}/components`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          component_type: 'mcq',
          learning_objective: learningObjective,
          topic_context: {
            topic: topicData.topic,
            key_facts: topicData.key_facts || [],
            common_misconceptions: topicData.common_misconceptions || [],
            assessment_angles: topicData.assessment_angles || []
          }
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to create MCQ')
      }

      // Get updated topic data
      const topicResponse = await fetch(`/api/content/topics/${topic.id}`)

      if (!topicResponse.ok) {
        throw new Error('Failed to get updated topic data')
      }

      const updatedTopic = await topicResponse.json()
      onMCQCreated(updatedTopic)

    } catch (error) {
      console.error('Error creating MCQ:', error)
      setError(error instanceof Error ? error.message : 'An unexpected error occurred')
    } finally {
      setCreatingMCQ(null)
    }
  }

  const isMCQCreated = (topicName: string, learningObjective: string) => {
    return topic.components.some((component: any) =>
      component.component_type === 'mcq' &&
      component.content?.learning_objective === learningObjective
    )
  }

  if (!topic.refined_material) {
    return (
      <Card className="max-w-4xl mx-auto">
        <CardContent className="py-8 text-center">
          <p className="text-gray-500">No refined material available</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">Refined Material</h2>
          <p className="text-gray-600 text-sm">
            {topic.refined_material.topics.length} topics extracted from your source material
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="outline" className="text-xs">
            {topic.source_level} level
          </Badge>
          <Button onClick={onProceedToComponents} className="bg-purple-600 hover:bg-purple-700">
            <Plus className="w-4 h-4 mr-2" />
            Proceed to Components
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="space-y-4">
        {topic.refined_material.topics.map((topicData: any, index: number) => {
          const sectionId = `topic-${index}`
          const isOpen = openSections.has(sectionId)

          return (
            <Card key={index}>
              <Collapsible>
                <CollapsibleTrigger
                  className="w-full"
                  onClick={() => toggleSection(sectionId)}
                >
                  <CardHeader className="hover:bg-gray-50 transition-colors">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-lg flex items-center gap-2">
                        <Brain className="h-5 w-5" />
                        {topicData.topic}
                      </CardTitle>
                      <div className="flex items-center gap-2">
                        <Badge variant="secondary" className="text-xs">
                          {topicData.learning_objectives?.length || 0} objectives
                        </Badge>
                        {isOpen ? (
                          <ChevronDown className="h-4 w-4" />
                        ) : (
                          <ChevronRight className="h-4 w-4" />
                        )}
                      </div>
                    </div>
                  </CardHeader>
                </CollapsibleTrigger>

                <CollapsibleContent>
                  <CardContent className="pt-0">
                    <div className="space-y-6">
                      {/* Learning Objectives */}
                      {topicData.learning_objectives && topicData.learning_objectives.length > 0 && (
                        <div>
                          <h4 className="font-medium flex items-center gap-2 mb-3">
                            <Target className="h-4 w-4" />
                            Learning Objectives
                          </h4>
                          <div className="space-y-2">
                            {topicData.learning_objectives.map((objective: string, objIndex: number) => (
                              <div
                                key={objIndex}
                                className="flex items-center justify-between p-3 bg-blue-50 rounded-lg border border-blue-200"
                              >
                                <span className="text-sm text-blue-900">{objective}</span>
                                <div className="flex items-center gap-2">
                                  {isMCQCreated(topicData.topic, objective) ? (
                                    <Badge variant="default" className="text-xs bg-green-600">
                                      <CheckCircle className="h-3 w-3 mr-1" />
                                      MCQ Created
                                    </Badge>
                                  ) : (
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      onClick={() => handleCreateMCQ(topicData, objective)}
                                      disabled={creatingMCQ === `${topicData.topic}-${objective}`}
                                    >
                                      {creatingMCQ === `${topicData.topic}-${objective}` ? (
                                        <>
                                          <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                                          Creating...
                                        </>
                                      ) : (
                                        'Create MCQ'
                                      )}
                                    </Button>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Key Facts */}
                      {topicData.key_facts && topicData.key_facts.length > 0 && (
                        <div>
                          <h4 className="font-medium flex items-center gap-2 mb-3">
                            <Lightbulb className="h-4 w-4" />
                            Key Facts
                          </h4>
                          <ul className="space-y-1">
                            {topicData.key_facts.map((fact: string, factIndex: number) => (
                              <li key={factIndex} className="text-sm text-gray-700 flex items-start gap-2">
                                <span className="text-green-600 mt-1">•</span>
                                {fact}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Common Misconceptions */}
                      {topicData.common_misconceptions && topicData.common_misconceptions.length > 0 && (
                        <div>
                          <h4 className="font-medium flex items-center gap-2 mb-3">
                            <AlertTriangle className="h-4 w-4" />
                            Common Misconceptions
                          </h4>
                          <div className="space-y-2">
                            {topicData.common_misconceptions.map((misconception: any, miscIndex: number) => (
                              <div key={miscIndex} className="p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                                <div className="text-sm">
                                  <p className="text-red-700 font-medium mb-1">
                                    ❌ {misconception.misconception}
                                  </p>
                                  <p className="text-green-700">
                                    ✅ {misconception.correct_concept}
                                  </p>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Assessment Angles */}
                      {topicData.assessment_angles && topicData.assessment_angles.length > 0 && (
                        <div>
                          <h4 className="font-medium flex items-center gap-2 mb-3">
                            <CheckCircle className="h-4 w-4" />
                            Assessment Angles
                          </h4>
                          <div className="flex flex-wrap gap-2">
                            {topicData.assessment_angles.map((angle: string, angleIndex: number) => (
                              <Badge key={angleIndex} variant="outline" className="text-xs">
                                {angle}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </CollapsibleContent>
              </Collapsible>
            </Card>
          )
        })}
      </div>

      {topic.refined_material.topics.length === 0 && (
        <Card>
          <CardContent className="py-8 text-center">
            <p className="text-gray-500">No topics found in the refined material</p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}