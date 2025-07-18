'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  ArrowLeft,
  Settings,
  Plus,
  Loader2,
  AlertCircle,
  Brain,
  BookOpen,
  MessageSquare,
  HelpCircle,
  FileText,
  Trash2,
  Edit3,
  RefreshCw,
  CheckCircle,
  Target
} from 'lucide-react'
import MaterialInputForm from '@/components/content-creation/MaterialInputForm'
import RefinedMaterialView from '@/components/content-creation/RefinedMaterialView'

interface BiteSizedTopic {
  id: string
  title: string
  core_concept: string
  user_level: string
  learning_objectives: string[]
  key_concepts: string[]
  key_aspects: string[]
  target_insights: string[]
  source_material?: string
  source_domain?: string
  source_level?: string
  refined_material?: RefinedMaterial
  components: BiteSizedComponent[]
}

interface RefinedMaterial {
  topics: RefinedMaterialTopic[]
}

interface RefinedMaterialTopic {
  topic: string
  learning_objectives: string[]
  key_facts: string[]
  common_misconceptions: Array<{
    misconception: string
    correct_concept: string
  }>
  assessment_angles: string[]
}

interface BiteSizedComponent {
  id: string
  component_type: string
  title: string
  content: any
  created_at: string
  updated_at: string
}

const COMPONENT_TYPES = {
  didactic_snippet: { icon: BookOpen, label: 'Didactic Snippet', color: 'bg-blue-100 text-blue-800' },
  glossary: { icon: FileText, label: 'Glossary', color: 'bg-green-100 text-green-800' },
  mcq: { icon: HelpCircle, label: 'Multiple Choice', color: 'bg-orange-100 text-orange-800' },
  short_answer: { icon: MessageSquare, label: 'Short Answer', color: 'bg-purple-100 text-purple-800' },
  socratic_dialogue: { icon: Brain, label: 'Socratic Dialogue', color: 'bg-red-100 text-red-800' },
  post_topic_quiz: { icon: Settings, label: 'Post-Topic Quiz', color: 'bg-gray-100 text-gray-800' },
  // Fallback for unknown component types
  unknown: { icon: FileText, label: 'Unknown Component', color: 'bg-gray-100 text-gray-800' }
}

export default function ContentCreationPage() {
  const params = useParams()
  const router = useRouter()
  const topicId = params.topicId as string

  const [topic, setTopic] = useState<BiteSizedTopic | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [currentStep, setCurrentStep] = useState<'input' | 'refined' | 'components'>('input')

  const isNewTopic = topicId === 'new'

  useEffect(() => {
    if (isNewTopic) {
      // Initialize new topic
      setTopic({
        id: 'new',
        title: '',
        core_concept: '',
        user_level: 'intermediate',
        learning_objectives: [],
        key_concepts: [],
        key_aspects: [],
        target_insights: [],
        source_material: '',
        source_domain: '',
        source_level: 'intermediate',
        refined_material: null,
        components: []
      })
      setCurrentStep('input')
      setIsLoading(false)
    } else {
      // Load existing topic
      loadTopic()
    }
  }, [topicId, isNewTopic])

  const loadTopic = async () => {
    try {
      setIsLoading(true)
      const response = await fetch(`/api/content/topics/${topicId}`)
      if (!response.ok) {
        throw new Error('Failed to load topic')
      }
      const topicData = await response.json()
      setTopic(topicData)

      // Set the appropriate step based on topic state
      if (!topicData.refined_material) {
        setCurrentStep('input')
      } else if (topicData.components.length === 0) {
        setCurrentStep('refined')
      } else {
        setCurrentStep('components')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load topic')
    } finally {
      setIsLoading(false)
    }
  }

  const handleGoBack = () => {
    router.push('/')
  }

  const handleGenerateAllComponents = async () => {
    if (!topic) return

    setIsGenerating(true)
    try {
      const response = await fetch(`/api/content/topics/${topic.id}/generate-all-components`, {
        method: 'POST'
      })
      if (!response.ok) {
        throw new Error('Failed to generate components')
      }
      // Reload topic to show new components
      await loadTopic()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate components')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleCreateComponent = async (componentType: string) => {
    if (!topic) return

    try {
      const response = await fetch(`/api/content/topics/${topic.id}/components`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          component_type: componentType
        })
      })
      if (!response.ok) {
        throw new Error('Failed to create component')
      }
      // Reload topic to show new component
      await loadTopic()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create component')
    }
  }

  const handleDeleteComponent = async (componentId: string) => {
    if (!topic) return

    try {
      const response = await fetch(`/api/topics/${topic.id}/components/${componentId}`, {
        method: 'DELETE'
      })
      if (!response.ok) {
        throw new Error('Failed to delete component')
      }
      // Reload topic to remove deleted component
      await loadTopic()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete component')
    }
  }

  const groupComponentsByType = (components: BiteSizedComponent[]) => {
    const grouped: { [key: string]: BiteSizedComponent[] } = {}
    components.forEach(component => {
      if (!grouped[component.component_type]) {
        grouped[component.component_type] = []
      }
      grouped[component.component_type].push(component)
    })

    // Debug: Log component types to help identify unknown types
    console.log('Component types found:', Object.keys(grouped))

    return grouped
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-purple-500 mx-auto mb-4" />
          <p className="text-gray-600">Loading topic...</p>
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
          <Button onClick={handleGoBack} variant="outline">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Dashboard
          </Button>
        </div>
      </div>
    )
  }

  if (!topic) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600">Topic not found</p>
          <Button onClick={handleGoBack} variant="outline" className="mt-4">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Dashboard
          </Button>
        </div>
      </div>
    )
  }

  const componentsByType = groupComponentsByType(topic.components)

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button onClick={handleGoBack} variant="ghost" size="sm">
                <ArrowLeft className="w-4 h-4" />
              </Button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Content Creation Studio</h1>
                <p className="text-gray-600">
                  {isNewTopic ? 'Create a new bite-sized topic' : 'Edit topic components'}
                </p>
              </div>
            </div>

            {!isNewTopic && (
              <Button
                onClick={handleGenerateAllComponents}
                disabled={isGenerating}
                className="bg-purple-600 hover:bg-purple-700"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Generate All Components
                  </>
                )}
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-4 py-8">
        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Step Navigation */}
        <div className="flex items-center justify-center mb-8">
          <div className="flex items-center space-x-8">
            <div className={`flex items-center gap-2 ${currentStep === 'input' ? 'text-purple-600' : currentStep === 'refined' || currentStep === 'components' ? 'text-green-600' : 'text-gray-400'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${currentStep === 'input' ? 'bg-purple-100' : currentStep === 'refined' || currentStep === 'components' ? 'bg-green-100' : 'bg-gray-100'}`}>
                {currentStep === 'refined' || currentStep === 'components' ? (
                  <CheckCircle className="w-5 h-5" />
                ) : (
                  <span className="text-sm font-medium">1</span>
                )}
              </div>
              <span className="text-sm font-medium">Source Material</span>
            </div>

            <div className={`w-16 h-px ${currentStep === 'refined' || currentStep === 'components' ? 'bg-green-300' : 'bg-gray-300'}`}></div>

            <div className={`flex items-center gap-2 ${currentStep === 'refined' ? 'text-purple-600' : currentStep === 'components' ? 'text-green-600' : 'text-gray-400'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${currentStep === 'refined' ? 'bg-purple-100' : currentStep === 'components' ? 'bg-green-100' : 'bg-gray-100'}`}>
                {currentStep === 'components' ? (
                  <CheckCircle className="w-5 h-5" />
                ) : (
                  <span className="text-sm font-medium">2</span>
                )}
              </div>
              <span className="text-sm font-medium">Refined Material</span>
            </div>

            <div className={`w-16 h-px ${currentStep === 'components' ? 'bg-green-300' : 'bg-gray-300'}`}></div>

            <div className={`flex items-center gap-2 ${currentStep === 'components' ? 'text-purple-600' : 'text-gray-400'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${currentStep === 'components' ? 'bg-purple-100' : 'bg-gray-100'}`}>
                <span className="text-sm font-medium">3</span>
              </div>
              <span className="text-sm font-medium">Components</span>
            </div>
          </div>
        </div>

        {/* Step Content */}
        {currentStep === 'input' && (
          <MaterialInputForm
            onMaterialCreated={(topicData) => {
              setTopic(topicData)
              setCurrentStep('refined')
            }}
            initialData={topic ? {
              title: topic.title,
              source_material: topic.source_material || '',
              source_domain: topic.source_domain || '',
              source_level: topic.source_level || 'intermediate'
            } : undefined}
          />
        )}

        {currentStep === 'refined' && topic && (
          <RefinedMaterialView
            topic={topic}
            onMCQCreated={(updatedTopic) => {
              setTopic(updatedTopic)
            }}
            onProceedToComponents={() => {
              setCurrentStep('components')
            }}
          />
        )}

        {currentStep === 'components' && topic && (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Components ({topic.components.length})</CardTitle>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentStep('refined')}
                  >
                    <Target className="w-4 h-4 mr-2" />
                    Back to Refined Material
                  </Button>
                  <select
                    onChange={(e) => e.target.value && handleCreateComponent(e.target.value)}
                    className="px-3 py-2 border border-gray-300 rounded-md text-sm"
                    defaultValue=""
                  >
                    <option value="">Create Component...</option>
                    {Object.entries(COMPONENT_TYPES).map(([type, config]) => (
                      <option key={type} value={type}>{config.label}</option>
                    ))}
                  </select>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {topic.components.length === 0 ? (
                <div className="text-center py-8">
                  <Settings className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No Components Yet</h3>
                  <p className="text-gray-600 mb-4">
                    Create individual components or generate all components at once.
                  </p>
                  {!isNewTopic && (
                    <Button onClick={handleGenerateAllComponents} disabled={isGenerating}>
                      {isGenerating ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Generating...
                        </>
                      ) : (
                        <>
                          <Plus className="w-4 h-4 mr-2" />
                          Generate All Components
                        </>
                      )}
                    </Button>
                  )}
                </div>
              ) : (
                <div className="space-y-6">
                  {Object.entries(componentsByType).map(([type, components]) => {
                    const config = COMPONENT_TYPES[type as keyof typeof COMPONENT_TYPES] || COMPONENT_TYPES.unknown
                    const Icon = config.icon

                    return (
                      <div key={type}>
                        <div className="flex items-center gap-3 mb-3">
                          <Icon className="w-5 h-5 text-gray-600" />
                          <h4 className="font-medium text-gray-900">{config.label}</h4>
                          <Badge variant="outline" className={config.color}>
                            {components.length}
                          </Badge>
                        </div>

                        <div className="space-y-2 ml-8">
                          {components.map((component) => (
                            <div
                              key={component.id}
                              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                            >
                              <div className="flex-1">
                                <h5 className="font-medium text-gray-900">{component.title}</h5>
                                <p className="text-sm text-gray-600">
                                  Created {new Date(component.created_at).toLocaleDateString()}
                                </p>
                              </div>
                              <div className="flex items-center gap-2">
                                <Button size="sm" variant="ghost">
                                  <Edit3 className="w-4 h-4" />
                                </Button>
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  onClick={() => handleDeleteComponent(component.id)}
                                >
                                  <Trash2 className="w-4 h-4" />
                                </Button>
                              </div>
                            </div>
                          ))}

                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleCreateComponent(type)}
                            className="w-full"
                          >
                            <Plus className="w-4 h-4 mr-2" />
                            Create Another {config.label}
                          </Button>
                        </div>

                        {Object.keys(componentsByType).indexOf(type) < Object.keys(componentsByType).length - 1 && (
                          <Separator className="my-4" />
                        )}
                      </div>
                    )
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}