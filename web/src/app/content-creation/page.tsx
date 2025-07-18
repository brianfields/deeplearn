'use client'

import { useState } from 'react'
import Layout from '@/components/Layout'
import MaterialInputForm from '@/components/content-creation/MaterialInputForm'
import RefinedMaterialView from '@/components/content-creation/RefinedMaterialView'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { FileText, Brain, CheckCircle, Plus } from 'lucide-react'

// Types
interface RefinedMaterial {
  topics: Array<{
    topic: string
    learning_objectives: string[]
    key_facts: string[]
    common_misconceptions: Array<{
      misconception: string
      correct_concept: string
    }>
    assessment_angles: string[]
  }>
}

interface ContentSession {
  session_id: string
  topic: string
  domain: string
  level: string
  refined_material: RefinedMaterial | null
  mcqs: Array<{
    mcq_id: string
    topic: string
    learning_objective: string
    mcq: {
      stem: string
      options: string[]
      correct_answer: string
      correct_answer_index: number
      rationale: string
    }
    evaluation: {
      alignment: string
      stem_quality: string
      options_quality: string
      overall: string
    }
    created_at: string
  }>
  created_at: string
  updated_at: string
}

export default function ContentCreationPage() {
  const [activeTab, setActiveTab] = useState('create')
  const [currentSession, setCurrentSession] = useState<ContentSession | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const handleMaterialCreated = (session: ContentSession) => {
    setCurrentSession(session)
    setActiveTab('material')
  }

  const handleMCQCreated = (updatedSession: ContentSession) => {
    setCurrentSession(updatedSession)
  }

  const handleNewSession = () => {
    setCurrentSession(null)
    setActiveTab('create')
  }

  return (
    <Layout>
      <div className="py-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Content Creation Studio</h1>
          <p className="text-gray-600 mt-2">
            Create and iterate on educational content using AI-powered tools
          </p>
        </div>

        <div className="grid grid-cols-12 gap-6">
          {/* Left sidebar - Navigation */}
          <div className="col-span-3">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Brain className="h-5 w-5" />
                  Content Studio
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button 
                  variant={activeTab === 'create' ? 'default' : 'ghost'}
                  className="w-full justify-start"
                  onClick={() => setActiveTab('create')}
                >
                  <Plus className="h-4 w-4 mr-2" />
                  New Content
                </Button>
                
                {currentSession && (
                  <>
                    <Button 
                      variant={activeTab === 'material' ? 'default' : 'ghost'}
                      className="w-full justify-start"
                      onClick={() => setActiveTab('material')}
                    >
                      <FileText className="h-4 w-4 mr-2" />
                      Refined Material
                    </Button>
                    
                    <Button 
                      variant={activeTab === 'mcqs' ? 'default' : 'ghost'}
                      className="w-full justify-start"
                      onClick={() => setActiveTab('mcqs')}
                    >
                      <CheckCircle className="h-4 w-4 mr-2" />
                      MCQs ({currentSession.mcqs.length})
                    </Button>
                  </>
                )}
              </CardContent>
            </Card>

            {/* Session info */}
            {currentSession && (
              <Card className="mt-4">
                <CardHeader>
                  <CardTitle className="text-sm">Current Session</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <div>
                    <span className="font-medium">Topic:</span> {currentSession.topic}
                  </div>
                  {currentSession.domain && (
                    <div>
                      <span className="font-medium">Domain:</span> {currentSession.domain}
                    </div>
                  )}
                  <div>
                    <span className="font-medium">Level:</span> {currentSession.level}
                  </div>
                  <div>
                    <span className="font-medium">Topics:</span> {currentSession.refined_material?.topics.length || 0}
                  </div>
                  <div>
                    <span className="font-medium">MCQs:</span> {currentSession.mcqs.length}
                  </div>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={handleNewSession}
                    className="w-full mt-2"
                  >
                    Start New Session
                  </Button>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Main content area */}
          <div className="col-span-9">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="create">Create Material</TabsTrigger>
                <TabsTrigger value="material" disabled={!currentSession}>
                  Refined Material
                </TabsTrigger>
                <TabsTrigger value="mcqs" disabled={!currentSession}>
                  MCQs
                </TabsTrigger>
              </TabsList>

              <TabsContent value="create" className="space-y-6">
                <MaterialInputForm 
                  onMaterialCreated={handleMaterialCreated}
                  isLoading={isLoading}
                  onLoadingChange={setIsLoading}
                />
              </TabsContent>

              <TabsContent value="material" className="space-y-6">
                {currentSession && (
                  <RefinedMaterialView
                    session={currentSession}
                    onMCQCreated={handleMCQCreated}
                  />
                )}
              </TabsContent>

              <TabsContent value="mcqs" className="space-y-6">
                {currentSession && (
                  <div className="space-y-4">
                    <h2 className="text-xl font-semibold">Created MCQs</h2>
                    {currentSession.mcqs.length === 0 ? (
                      <Card>
                        <CardContent className="py-8 text-center">
                          <CheckCircle className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                          <h3 className="text-lg font-medium text-gray-900 mb-2">No MCQs Yet</h3>
                          <p className="text-gray-600">
                            Go to the Refined Material tab to create MCQs for your learning objectives.
                          </p>
                        </CardContent>
                      </Card>
                    ) : (
                      <div className="space-y-4">
                        {currentSession.mcqs.map((mcq, index) => (
                          <Card key={mcq.mcq_id}>
                            <CardHeader>
                              <CardTitle className="text-lg">
                                MCQ {index + 1}: {mcq.topic}
                              </CardTitle>
                              <p className="text-sm text-gray-600">
                                Learning Objective: {mcq.learning_objective}
                              </p>
                            </CardHeader>
                            <CardContent>
                              <div className="space-y-4">
                                <div>
                                  <h4 className="font-medium mb-2">Question</h4>
                                  <p className="text-gray-700">{mcq.mcq.stem}</p>
                                </div>
                                
                                <div>
                                  <h4 className="font-medium mb-2">Options</h4>
                                  <div className="space-y-2">
                                    {mcq.mcq.options.map((option, optionIndex) => (
                                      <div 
                                        key={optionIndex}
                                        className={`p-3 rounded-lg border ${
                                          optionIndex === mcq.mcq.correct_answer_index
                                            ? 'bg-green-50 border-green-200'
                                            : 'bg-gray-50 border-gray-200'
                                        }`}
                                      >
                                        <span className="font-medium">
                                          {String.fromCharCode(65 + optionIndex)}.
                                        </span> {option}
                                        {optionIndex === mcq.mcq.correct_answer_index && (
                                          <span className="ml-2 text-green-600 font-medium">
                                            ✓ Correct
                                          </span>
                                        )}
                                      </div>
                                    ))}
                                  </div>
                                </div>
                                
                                <div>
                                  <h4 className="font-medium mb-2">Rationale</h4>
                                  <p className="text-gray-700">{mcq.mcq.rationale}</p>
                                </div>
                                
                                <div>
                                  <h4 className="font-medium mb-2">Quality Assessment</h4>
                                  <p className="text-gray-700 text-sm">{mcq.evaluation.overall}</p>
                                </div>
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </TabsContent>
            </Tabs>
          </div>
        </div>
      </div>
    </Layout>
  )
}