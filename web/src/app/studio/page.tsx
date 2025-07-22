'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { Plus, Edit3, BookOpen, Settings } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import Layout from '@/components/shared/Layout'
import { apiClient } from '@/api'
import type { BiteSizedTopic } from '@/types'

export default function StudioPage() {
  const router = useRouter()
  const [topics, setTopics] = useState<BiteSizedTopic[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadTopics()
  }, [])

  const loadTopics = async () => {
    try {
      const topicsData = await apiClient.getBiteSizedTopics()
      setTopics(topicsData)
    } catch (error) {
      console.error('Failed to load topics:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleCreateNew = () => {
    router.push('/studio/new')
  }

  const handleEditTopic = (topicId: string) => {
    router.push(`/studio/${topicId}`)
  }

  return (
    <Layout>
      <div className="max-w-6xl mx-auto py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Content Studio</h1>
            <p className="text-gray-600 mt-2">Create and manage your learning content</p>
          </div>
          <Button onClick={handleCreateNew} className="bg-purple-600 hover:bg-purple-700">
            <Plus className="w-4 h-4 mr-2" />
            New Topic
          </Button>
        </div>

        {isLoading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto"></div>
            <p className="text-gray-600 mt-4">Loading topics...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {topics.map((topic) => (
              <motion.div
                key={topic.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                whileHover={{ y: -2 }}
                transition={{ duration: 0.2 }}
              >
                <Card className="cursor-pointer hover:shadow-lg transition-shadow">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg">{topic.title}</CardTitle>
                    <p className="text-sm text-gray-600 line-clamp-2">{topic.core_concept}</p>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 text-sm text-gray-500">
                        <BookOpen className="w-4 h-4" />
                        <span>{topic.learning_objectives?.length || 0} objectives</span>
                      </div>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleEditTopic(topic.id)}
                      >
                        <Edit3 className="w-4 h-4 mr-1" />
                        Edit
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </Layout>
  )
}