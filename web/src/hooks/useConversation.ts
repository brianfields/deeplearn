/**
 * Conversation Hook
 *
 * This hook provides a complete interface for managing real-time conversations
 * including WebSocket connections, message handling, and state management.
 *
 * Features:
 * - WebSocket connection management
 * - Real-time message handling
 * - Progress tracking
 * - Connection state monitoring
 * - Error handling and recovery
 *
 * Usage:
 * ```typescript
 * const {
 *   messages,
 *   sendMessage,
 *   isConnected,
 *   progress
 * } = useConversation(pathId, topicId)
 * ```
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import type {
  ChatMessage,
  ProgressUpdate,
  SessionState,
  MessageRole
} from '@/types'

import {
  conversationService,
  type ActiveConversation,
  type ConversationHandlers,
  type ConversationStats
} from '@/services'

import { ConnectionState, ApiError } from '@/api'

/**
 * Hook state interface
 */
interface UseConversationState {
  messages: ChatMessage[]
  isConnected: boolean
  connectionState: ConnectionState
  isLoading: boolean
  isSending: boolean
  error: string | null
  progress: ProgressUpdate | null
  sessionState: SessionState | null
  stats: ConversationStats | null
}

/**
 * Hook return interface
 */
interface UseConversationReturn extends UseConversationState {
  // Message operations
  sendMessage: (message: string) => Promise<void>
  clearMessages: () => void

  // Connection operations
  connect: () => Promise<void>
  disconnect: () => void
  reconnect: () => void

  // Utilities
  clearError: () => void
  refreshStats: () => void
  isUserMessage: (message: ChatMessage) => boolean
  isAssistantMessage: (message: ChatMessage) => boolean
  getLastUserMessage: () => ChatMessage | null
  getLastAssistantMessage: () => ChatMessage | null
}

/**
 * Options for useConversation hook
 */
interface UseConversationOptions {
  autoConnect?: boolean
  onMessage?: (message: ChatMessage) => void
  onProgress?: (progress: ProgressUpdate) => void
  onSessionState?: (state: SessionState) => void
  onConnectionChange?: (state: ConnectionState) => void
  onError?: (error: Error) => void
}

/**
 * Conversation management hook
 */
export function useConversation(
  pathId: string | null,
  topicId: string | null,
  options: UseConversationOptions = {}
): UseConversationReturn {
  const {
    autoConnect = true,
    onMessage,
    onProgress,
    onSessionState,
    onConnectionChange,
    onError
  } = options

  const [state, setState] = useState<UseConversationState>({
    messages: [],
    isConnected: false,
    connectionState: ConnectionState.DISCONNECTED,
    isLoading: false,
    isSending: false,
    error: null,
    progress: null,
    sessionState: null,
    stats: null
  })

  // Ref to store current conversation
  const conversationRef = useRef<ActiveConversation | null>(null)

  /**
   * Update specific state properties
   */
  const updateState = useCallback((updates: Partial<UseConversationState>) => {
    setState(prev => ({ ...prev, ...updates }))
  }, [])

  /**
   * Setup conversation handlers
   */
  const createHandlers = useCallback((): ConversationHandlers => ({
    onMessage: (message: ChatMessage) => {
      updateState({
        messages: [...state.messages, message],
        isSending: false
      })
      onMessage?.(message)
    },

    onProgress: (progress: ProgressUpdate) => {
      updateState({ progress })
      onProgress?.(progress)
    },

    onSessionState: (sessionState: SessionState) => {
      updateState({ sessionState })
      onSessionState?.(sessionState)
    },

    onConnectionChange: (connectionState: ConnectionState) => {
      updateState({
        connectionState,
        isConnected: connectionState === ConnectionState.CONNECTED
      })
      onConnectionChange?.(connectionState)
    },

    onError: (error: Error) => {
      updateState({
        error: error.message,
        isLoading: false,
        isSending: false
      })
      onError?.(error)
    }
  }), [state.messages, updateState, onMessage, onProgress, onSessionState, onConnectionChange, onError])

  /**
   * Start conversation
   */
  const connect = useCallback(async () => {
    if (!pathId || !topicId) {
      updateState({ error: 'Path ID and Topic ID are required' })
      return
    }

    try {
      updateState({ isLoading: true, error: null })

      const handlers = createHandlers()
      const conversation = await conversationService.startConversation({
        pathId,
        topicId,
        handlers
      })

      conversationRef.current = conversation

      updateState({
        messages: conversation.messages,
        isLoading: false,
        isConnected: conversation.isConnected
      })

      // Load initial stats
      refreshStats()
    } catch (error) {
      const errorMessage = error instanceof ApiError
        ? error.message
        : 'Failed to start conversation'
      updateState({ error: errorMessage, isLoading: false })
    }
  }, [pathId, topicId, createHandlers, updateState])

  /**
   * Disconnect conversation
   */
  const disconnect = useCallback(() => {
    if (pathId && topicId) {
      conversationService.closeConversation(pathId, topicId)
      conversationRef.current = null
      updateState({
        isConnected: false,
        connectionState: ConnectionState.DISCONNECTED
      })
    }
  }, [pathId, topicId, updateState])

  /**
   * Reconnect conversation
   */
  const reconnect = useCallback(() => {
    disconnect()
    setTimeout(() => connect(), 1000) // Brief delay before reconnecting
  }, [disconnect, connect])

  /**
   * Send message
   */
  const sendMessage = useCallback(async (message: string) => {
    if (!pathId || !topicId) {
      throw new Error('Path ID and Topic ID are required')
    }

    if (!message.trim()) {
      throw new Error('Message cannot be empty')
    }

    if (!state.isConnected) {
      throw new Error('Not connected to conversation')
    }

    try {
      updateState({ isSending: true, error: null })
      await conversationService.sendMessage(pathId, topicId, message)
      // The response will be handled by the onMessage handler
    } catch (error) {
      const errorMessage = error instanceof Error
        ? error.message
        : 'Failed to send message'
      updateState({ error: errorMessage, isSending: false })
      throw error
    }
  }, [pathId, topicId, state.isConnected, updateState])

  /**
   * Clear messages
   */
  const clearMessages = useCallback(() => {
    updateState({ messages: [] })
  }, [updateState])

  /**
   * Clear error
   */
  const clearError = useCallback(() => {
    updateState({ error: null })
  }, [updateState])

  /**
   * Refresh conversation statistics
   */
  const refreshStats = useCallback(() => {
    if (pathId && topicId) {
      const stats = conversationService.getConversationStats(pathId, topicId)
      updateState({ stats })
    }
  }, [pathId, topicId, updateState])

  /**
   * Auto-connect when path/topic changes
   */
  useEffect(() => {
    if (autoConnect && pathId && topicId) {
      connect()
    }

    // Cleanup on unmount or when pathId/topicId changes
    return () => {
      if (conversationRef.current) {
        disconnect()
      }
    }
  }, [pathId, topicId, autoConnect]) // Note: not including connect/disconnect to avoid loops

  /**
   * Refresh stats periodically
   */
  useEffect(() => {
    if (!state.isConnected) return

    const interval = setInterval(refreshStats, 10000) // Every 10 seconds
    return () => clearInterval(interval)
  }, [state.isConnected, refreshStats])

  /**
   * Utility functions
   */
  const isUserMessage = useCallback((message: ChatMessage): boolean => {
    return message.role === 'user'
  }, [])

  const isAssistantMessage = useCallback((message: ChatMessage): boolean => {
    return message.role === 'assistant'
  }, [])

  const getLastUserMessage = useCallback((): ChatMessage | null => {
    const userMessages = state.messages.filter(isUserMessage)
    return userMessages.length > 0 ? userMessages[userMessages.length - 1] : null
  }, [state.messages, isUserMessage])

  const getLastAssistantMessage = useCallback((): ChatMessage | null => {
    const assistantMessages = state.messages.filter(isAssistantMessage)
    return assistantMessages.length > 0 ? assistantMessages[assistantMessages.length - 1] : null
  }, [state.messages, isAssistantMessage])

  return {
    // State
    messages: state.messages,
    isConnected: state.isConnected,
    connectionState: state.connectionState,
    isLoading: state.isLoading,
    isSending: state.isSending,
    error: state.error,
    progress: state.progress,
    sessionState: state.sessionState,
    stats: state.stats,

    // Operations
    sendMessage,
    clearMessages,
    connect,
    disconnect,
    reconnect,

    // Utilities
    clearError,
    refreshStats,
    isUserMessage,
    isAssistantMessage,
    getLastUserMessage,
    getLastAssistantMessage
  }
}

/**
 * Hook for conversation progress tracking
 */
export function useConversationProgress(pathId: string | null, topicId: string | null) {
  const [progress, setProgress] = useState<ProgressUpdate | null>(null)

  useEffect(() => {
    if (!pathId || !topicId) return

    const conversation = conversationService.getConversation(pathId, topicId)
    if (conversation) {
      // Set up progress handler
      conversation.handlers.onProgress = setProgress
    }
  }, [pathId, topicId])

  return progress
}

/**
 * Hook for conversation statistics
 */
export function useConversationStats(pathId: string | null, topicId: string | null) {
  const [stats, setStats] = useState<ConversationStats | null>(null)

  const refreshStats = useCallback(() => {
    if (pathId && topicId) {
      const newStats = conversationService.getConversationStats(pathId, topicId)
      setStats(newStats)
    }
  }, [pathId, topicId])

  useEffect(() => {
    refreshStats()

    // Refresh every 5 seconds
    const interval = setInterval(refreshStats, 5000)
    return () => clearInterval(interval)
  }, [refreshStats])

  return { stats, refreshStats }
}