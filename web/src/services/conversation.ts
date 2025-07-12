/**
 * Conversation Service
 *
 * This service manages all conversation-related business logic including
 * WebSocket connections, message handling, and conversation state management.
 *
 * Responsibilities:
 * - WebSocket connection management
 * - Message queuing and delivery
 * - Conversation state tracking
 * - Progress monitoring
 * - Error handling and recovery
 *
 * Usage:
 * ```typescript
 * import { conversationService } from '@/services/conversation'
 *
 * const conversation = await conversationService.startConversation('path-123', 'topic-456')
 * ```
 */

import type {
  ConversationSession,
  ChatMessage,
  WebSocketMessage,
  ProgressUpdate,
  SessionState,
  MessageRole
} from '@/types'

import {
  apiClient,
  ConversationWebSocket,
  ConnectionState,
  WebSocketError,
  ApiError
} from '@/api'

/**
 * Conversation event handlers
 */
export interface ConversationHandlers {
  onMessage?: (message: ChatMessage) => void
  onProgress?: (progress: ProgressUpdate) => void
  onSessionState?: (state: SessionState) => void
  onConnectionChange?: (state: ConnectionState) => void
  onError?: (error: Error) => void
}

/**
 * Active conversation instance
 */
export interface ActiveConversation {
  pathId: string
  topicId: string
  session: ConversationSession
  websocket: ConversationWebSocket
  handlers: ConversationHandlers
  messages: ChatMessage[]
  isConnected: boolean
  lastActivity: Date
}

/**
 * Options for starting a conversation
 */
export interface StartConversationOptions {
  pathId: string
  topicId: string
  handlers?: ConversationHandlers
}

/**
 * Conversation statistics
 */
export interface ConversationStats {
  totalMessages: number
  userMessages: number
  assistantMessages: number
  sessionDuration: number
  averageResponseTime: number
  connectionUptime: number
}

/**
 * Conversation service class
 */
export class ConversationService {
  private activeConversations = new Map<string, ActiveConversation>()
  private messageHistory = new Map<string, ChatMessage[]>()
  private responseTimeTracker = new Map<string, number>()

  /**
   * Generate conversation key
   */
  private getConversationKey(pathId: string, topicId: string): string {
    return `${pathId}_${topicId}`
  }

  /**
   * Start a new conversation or continue existing one
   */
  async startConversation(options: StartConversationOptions): Promise<ActiveConversation> {
    const { pathId, topicId, handlers = {} } = options
    const key = this.getConversationKey(pathId, topicId)

    try {
      // Check if conversation already exists
      const existing = this.activeConversations.get(key)
      if (existing) {
        // Update handlers if provided
        existing.handlers = { ...existing.handlers, ...handlers }
        return existing
      }

      // Try to continue existing conversation first
      let session: ConversationSession
      try {
        session = await apiClient.continueConversation(pathId, topicId)
      } catch (error) {
        // If continuing fails, start a new conversation
        session = await apiClient.startConversation(pathId, topicId)
      }

      // Create WebSocket connection
      const websocket = new ConversationWebSocket(topicId)

      // Initialize conversation
      const conversation: ActiveConversation = {
        pathId,
        topicId,
        session,
        websocket,
        handlers,
        messages: session.message_history || [],
        isConnected: false,
        lastActivity: new Date()
      }

      // Setup WebSocket handlers
      this.setupWebSocketHandlers(conversation)

      // Store conversation
      this.activeConversations.set(key, conversation)
      this.messageHistory.set(key, conversation.messages)

      return conversation
    } catch (error) {
      if (error instanceof ApiError) {
        throw error
      }
      throw new Error(`Failed to start conversation: ${error}`)
    }
  }

  /**
   * Send a message in the conversation
   */
  async sendMessage(pathId: string, topicId: string, message: string): Promise<void> {
    const key = this.getConversationKey(pathId, topicId)
    const conversation = this.activeConversations.get(key)

    if (!conversation) {
      throw new Error('Conversation not found. Start a conversation first.')
    }

    if (!message.trim()) {
      throw new Error('Message cannot be empty')
    }

    try {
      // Add user message to history
      const userMessage: ChatMessage = {
        role: 'user',
        content: message.trim(),
        timestamp: new Date().toISOString()
      }

      this.addMessage(key, userMessage)
      conversation.lastActivity = new Date()

      // Track response time
      this.responseTimeTracker.set(key, Date.now())

      // Send via WebSocket
      conversation.websocket.sendMessage(message.trim())

      // Notify handlers
      conversation.handlers.onMessage?.(userMessage)
    } catch (error) {
      throw new Error(`Failed to send message: ${error}`)
    }
  }

  /**
   * Get conversation messages
   */
  getMessages(pathId: string, topicId: string): ChatMessage[] {
    const key = this.getConversationKey(pathId, topicId)
    return this.messageHistory.get(key) || []
  }

  /**
   * Get active conversation
   */
  getConversation(pathId: string, topicId: string): ActiveConversation | null {
    const key = this.getConversationKey(pathId, topicId)
    return this.activeConversations.get(key) || null
  }

  /**
   * Close a conversation
   */
  closeConversation(pathId: string, topicId: string): void {
    const key = this.getConversationKey(pathId, topicId)
    const conversation = this.activeConversations.get(key)

    if (conversation) {
      conversation.websocket.close()
      this.activeConversations.delete(key)
    }
  }

  /**
   * Close all conversations
   */
  closeAllConversations(): void {
    for (const conversation of this.activeConversations.values()) {
      conversation.websocket.close()
    }
    this.activeConversations.clear()
  }

  /**
   * Get conversation statistics
   */
  getConversationStats(pathId: string, topicId: string): ConversationStats | null {
    const key = this.getConversationKey(pathId, topicId)
    const conversation = this.activeConversations.get(key)
    const messages = this.getMessages(pathId, topicId)

    if (!conversation) {
      return null
    }

    const userMessages = messages.filter(m => m.role === 'user').length
    const assistantMessages = messages.filter(m => m.role === 'assistant').length

    const sessionStart = conversation.session.ai_message
      ? new Date(conversation.session.ai_message).getTime()
      : Date.now()

    const sessionDuration = Date.now() - sessionStart

    return {
      totalMessages: messages.length,
      userMessages,
      assistantMessages,
      sessionDuration,
      averageResponseTime: 0, // TODO: Calculate from responseTimeTracker
      connectionUptime: sessionDuration // Simplified for now
    }
  }

  /**
   * Get all active conversations
   */
  getActiveConversations(): ActiveConversation[] {
    return Array.from(this.activeConversations.values())
  }

  /**
   * Check if conversation is active
   */
  isConversationActive(pathId: string, topicId: string): boolean {
    const key = this.getConversationKey(pathId, topicId)
    const conversation = this.activeConversations.get(key)
    return conversation?.isConnected || false
  }

  // ================================
  // Private Methods
  // ================================

  /**
   * Setup WebSocket event handlers
   */
  private setupWebSocketHandlers(conversation: ActiveConversation): void {
    const { websocket, handlers } = conversation
    const key = this.getConversationKey(conversation.pathId, conversation.topicId)

    websocket.setHandlers({
      onOpen: () => {
        conversation.isConnected = true
        handlers.onConnectionChange?.(ConnectionState.CONNECTED)
      },

      onClose: () => {
        conversation.isConnected = false
        handlers.onConnectionChange?.(ConnectionState.DISCONNECTED)
      },

      onError: (error: WebSocketError) => {
        handlers.onError?.(error)
      },

      onStateChange: (state: ConnectionState) => {
        conversation.isConnected = state === ConnectionState.CONNECTED
        handlers.onConnectionChange?.(state)
      },

      onMessage: (data: WebSocketMessage) => {
        this.handleWebSocketMessage(key, data, conversation)
      }
    })
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleWebSocketMessage(
    key: string,
    data: WebSocketMessage,
    conversation: ActiveConversation
  ): void {
    conversation.lastActivity = new Date()

    switch (data.type) {
      case 'chat_message':
        if (data.message) {
          this.addMessage(key, data.message)
          conversation.handlers.onMessage?.(data.message)

          // Calculate response time for assistant messages
          if (data.message.role === 'assistant') {
            const startTime = this.responseTimeTracker.get(key)
            if (startTime) {
              const responseTime = Date.now() - startTime
              // TODO: Store response time for statistics
              this.responseTimeTracker.delete(key)
            }
          }
        }
        break

      case 'progress_update':
        if (data.progress) {
          conversation.handlers.onProgress?.(data.progress)
        }
        break

      case 'session_state':
        if (data.state) {
          conversation.handlers.onSessionState?.(data.state)
        }
        break

      case 'error':
        const error = new Error(data.error || 'Unknown WebSocket error')
        conversation.handlers.onError?.(error)
        break
    }
  }

  /**
   * Add message to conversation history
   */
  private addMessage(key: string, message: ChatMessage): void {
    const messages = this.messageHistory.get(key) || []
    messages.push(message)
    this.messageHistory.set(key, messages)

    // Update conversation messages
    const conversation = this.activeConversations.get(key)
    if (conversation) {
      conversation.messages = messages
    }
  }

  /**
   * Clean up inactive conversations
   */
  private cleanupInactiveConversations(): void {
    const now = new Date()
    const maxInactiveTime = 30 * 60 * 1000 // 30 minutes

    for (const [key, conversation] of this.activeConversations.entries()) {
      const inactiveTime = now.getTime() - conversation.lastActivity.getTime()

      if (inactiveTime > maxInactiveTime && !conversation.isConnected) {
        conversation.websocket.close()
        this.activeConversations.delete(key)
      }
    }
  }

  /**
   * Initialize cleanup timer
   */
  private initCleanup(): void {
    // Run cleanup every 5 minutes
    setInterval(() => {
      this.cleanupInactiveConversations()
    }, 5 * 60 * 1000)
  }
}

/**
 * Default conversation service instance
 */
export const conversationService = new ConversationService()

/**
 * Create a new conversation service instance
 */
export function createConversationService(): ConversationService {
  return new ConversationService()
}