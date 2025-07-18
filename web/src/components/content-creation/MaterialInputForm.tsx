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
  onMaterialCreated: (topicData: any) => void
  initialData?: {
    title: string
    source_material: string
    source_domain: string
    source_level: string
  }
}

export default function MaterialInputForm({ onMaterialCreated, initialData }: MaterialInputFormProps) {
  const [formData, setFormData] = useState({
    title: initialData?.title || '',
    source_material: initialData?.source_material || '',
    source_domain: initialData?.source_domain || '',
    source_level: initialData?.source_level || 'intermediate'
  })
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    
    // Validation
    if (!formData.title.trim()) {
      setError('Topic title is required')
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

    setIsLoading(true)
    
    try {
      const response = await fetch('/api/topics/create-from-material', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: formData.title,
          source_material: formData.source_material,
          source_domain: formData.source_domain,
          source_level: formData.source_level
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to create topic from material')
      }

      const topicData = await response.json()
      onMaterialCreated(topicData)
      
    } catch (error) {
      console.error('Error creating topic from material:', error)
      setError(error instanceof Error ? error.message : 'An unexpected error occurred')
    } finally {
      setIsLoading(false)
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
    <Card className="max-w-4xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="h-5 w-5" />
          Create Topic from Source Material
        </CardTitle>
        <p className="text-sm text-gray-600">
          Enter your source material and let AI extract structured topics and learning objectives
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
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="title">Topic Title *</Label>
              <Input
                id="title"
                placeholder="e.g., Python Functions"
                value={formData.title}
                onChange={(e) => handleInputChange('title', e.target.value)}
                disabled={isLoading}
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="source_domain">Domain (Optional)</Label>
              <Input
                id="source_domain"
                placeholder="e.g., Programming, Mathematics"
                value={formData.source_domain}
                onChange={(e) => handleInputChange('source_domain', e.target.value)}
                disabled={isLoading}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="source_level">Target Level</Label>
            <Select 
              value={formData.source_level} 
              onValueChange={(value) => handleInputChange('source_level', value)}
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
                  title: '',
                  source_material: '',
                  source_domain: '',
                  source_level: 'intermediate'
                })
                setError(null)
              }}
              disabled={isLoading}
            >
              Clear
            </Button>
            
            <Button
              type="submit"
              disabled={isLoading || !formData.title.trim() || !formData.source_material.trim()}
              className="bg-purple-600 hover:bg-purple-700"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Creating...
                </>
              ) : (
                'Create Refined Material'
              )}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}