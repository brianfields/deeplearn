'use client'

import { useState, useEffect, useCallback } from 'react'
import { apiClient } from '@/api/client'
import type { BiteSizedTopic, BiteSizedTopicDetail, ConversationSession } from '@/types'

interface UseBiteSizedTopicsState {
  topics: BiteSizedTopic[]
  selectedTopic: BiteSizedTopicDetail | null
  isLoading: boolean
  isLoadingDetail: boolean
  error: string | null
}

interface UseBiteSizedTopicsActions {
  refreshTopics: () => Promise<void>
  selectTopic: (topicId: string) => Promise<void>
  clearSelectedTopic: () => void
  startConversation: (topicId: string) => Promise<ConversationSession>
}

export type UseBiteSizedTopicsReturn = UseBiteSizedTopicsState & UseBiteSizedTopicsActions

export default function useBiteSizedTopics(): UseBiteSizedTopicsReturn {
  const [state, setState] = useState<UseBiteSizedTopicsState>({
    topics: [],
    selectedTopic: null,
    isLoading: true,
    isLoadingDetail: false,
    error: null
  })

  const refreshTopics = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }))
      const topics = await apiClient.getBiteSizedTopics()
      setState(prev => ({ ...prev, topics, isLoading: false }))
    } catch (error) {
      console.error('Error fetching bite-sized topics:', error)
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to fetch topics',
        isLoading: false
      }))
    }
  }, [])

  const selectTopic = useCallback(async (topicId: string) => {
    try {
      setState(prev => ({ ...prev, isLoadingDetail: true, error: null }))
      const topicDetail = await apiClient.getBiteSizedTopicDetail(topicId)
      setState(prev => ({ ...prev, selectedTopic: topicDetail, isLoadingDetail: false }))
    } catch (error) {
      console.error('Error fetching topic details:', error)
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to fetch topic details',
        isLoadingDetail: false
      }))
    }
  }, [])

  const clearSelectedTopic = useCallback(() => {
    setState(prev => ({ ...prev, selectedTopic: null }))
  }, [])

  const startConversation = useCallback(async (topicId: string): Promise<ConversationSession> => {
    try {
      const session = await apiClient.startBiteSizedTopicConversation(topicId)
      return session
    } catch (error) {
      console.error('Error starting conversation:', error)
      throw error
    }
  }, [])

  // Load topics on mount
  useEffect(() => {
    refreshTopics()
  }, [refreshTopics])

  return {
    ...state,
    refreshTopics,
    selectTopic,
    clearSelectedTopic,
    startConversation
  }
}