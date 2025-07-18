'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Loader2, FileText, AlertCircle } from 'lucide-react'

interface MaterialInputFormProps {
  onMaterialCreated: (session: any) => void
  isLoading: boolean
  onLoadingChange: (loading: boolean) => void
}

export default function MaterialInputForm({
  onMaterialCreated,
  isLoading,
  onLoadingChange
}: MaterialInputFormProps) {
  const [formData, setFormData] = useState({
    topic: '',
    source_material: '',
    domain: '',
    level: 'intermediate',
    model: 'gpt-4o'
  })
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    // Validation
    if (!formData.topic.trim()) {
      setError('Topic is required')
      return
    }

    if (!formData.source_material.trim()) {
      setError('Source material is required')
      return
    }

    if (formData.source_material.trim().length < 100) {
      setError('Source material should be at least 100 characters long')
      return
    }

    onLoadingChange(true)

    try {
      const response = await fetch('/api/content/refined-material', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to create refined material')
      }

      const refinedMaterialResponse = await response.json()

      // Get the full session data
      const sessionResponse = await fetch(`/api/content/sessions/${refinedMaterialResponse.session_id}`)

      if (!sessionResponse.ok) {
        throw new Error('Failed to get session data')
      }

      const sessionData = await sessionResponse.json()
      onMaterialCreated(sessionData)

    } catch (error) {
      console.error('Error creating refined material:', error)
      setError(error instanceof Error ? error.message : 'An unexpected error occurred')
    } finally {
      onLoadingChange(false)
    }
  }

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
    if (error) setError(null)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="h-5 w-5" />
          Create Refined Material
        </CardTitle>
        <p className="text-sm text-gray-600">
          Input your source material and let AI extract structured topics and learning objectives
        </p>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="topic">Topic Title *</Label>
              <Input
                id="topic"
                placeholder="e.g., Python Functions"
                value={formData.topic}
                onChange={(e) => handleInputChange('topic', e.target.value)}
                disabled={isLoading}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="domain">Domain (Optional)</Label>
              <Input
                id="domain"
                placeholder="e.g., Programming, Mathematics"
                value={formData.domain}
                onChange={(e) => handleInputChange('domain', e.target.value)}
                disabled={isLoading}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="level">Target Level</Label>
              <Select
                value={formData.level}
                onValueChange={(value) => handleInputChange('level', value)}
                disabled={isLoading}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select level" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="beginner">Beginner</SelectItem>
                  <SelectItem value="intermediate">Intermediate</SelectItem>
                  <SelectItem value="advanced">Advanced</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="model">AI Model</Label>
              <Select
                value={formData.model}
                onValueChange={(value) => handleInputChange('model', value)}
                disabled={isLoading}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select model" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="gpt-4o">GPT-4o</SelectItem>
                  <SelectItem value="gpt-3.5-turbo">GPT-3.5 Turbo</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="source_material">Source Material *</Label>
            <Textarea
              id="source_material"
              placeholder="Paste your source material here. This should be the raw text content that you want to create educational content from. The AI will analyze this and extract structured topics and learning objectives."
              rows={12}
              value={formData.source_material}
              onChange={(e) => handleInputChange('source_material', e.target.value)}
              disabled={isLoading}
              className="resize-none"
            />
            <p className="text-xs text-gray-500">
              {formData.source_material.length} characters
              {formData.source_material.length > 0 && formData.source_material.length < 100 && (
                <span className="text-red-500 ml-1">
                  (minimum 100 characters)
                </span>
              )}
            </p>
          </div>

          <div className="flex justify-end space-x-3">
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setFormData({
                  topic: '',
                  source_material: '',
                  domain: '',
                  level: 'intermediate',
                  model: 'gpt-4o'
                })
                setError(null)
              }}
              disabled={isLoading}
            >
              Clear
            </Button>

            <Button
              type="submit"
              disabled={isLoading || !formData.topic.trim() || !formData.source_material.trim()}
            >
              {isLoading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              Create Refined Material
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}