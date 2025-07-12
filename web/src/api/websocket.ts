/**
 * WebSocket Client for Real-time Conversations
 *
 * This module provides a robust WebSocket client with:
 * - Automatic reconnection
 * - Message queuing during disconnections
 * - Error handling and logging
 * - TypeScript support
 * - Connection state management
 *
 * Usage:
 * ```typescript
 * import { ConversationWebSocket } from '@/api/websocket'
 *
 * const ws = new ConversationWebSocket('topic-123')
 * ws.onMessage = (data) => console.log('Received:', data)
 * ws.sendMessage('Hello!')
 * ```
 */

import type {
  WebSocketMessage,
  ChatMessage,
  ProgressUpdate,
  SessionState
} from '@/types'

import {
  WebSocketError,
  WebSocketCloseCode
} from '@/types/api'

/**
 * WebSocket connection states
 */
export enum ConnectionState {
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  DISCONNECTED = 'disconnected',
  RECONNECTING = 'reconnecting',
  FAILED = 'failed'
}

/**
 * Configuration for WebSocket client
 */
export interface WebSocketConfig {
  baseUrl: string
  enableLogging: boolean
  reconnectAttempts: number
  reconnectDelay: number
  maxReconnectDelay: number
  messageQueueSize: number
  pingInterval: number
}

/**
 * Event handlers for WebSocket events
 */
export interface WebSocketHandlers {
  onOpen?: () => void
  onClose?: (code: number, reason: string) => void
  onError?: (error: WebSocketError) => void
  onMessage?: (data: WebSocketMessage) => void
  onStateChange?: (state: ConnectionState) => void
}

/**
 * Message to be sent to server
 */
export interface OutgoingMessage {
  message: string
}

/**
 * WebSocket client for real-time conversations
 */
export class ConversationWebSocket {
  private ws: WebSocket | null = null
  private config: WebSocketConfig
  private handlers: WebSocketHandlers = {}
  private state: ConnectionState = ConnectionState.DISCONNECTED
  private reconnectAttempt = 0
  private reconnectTimer: NodeJS.Timeout | null = null
  private pingTimer: NodeJS.Timeout | null = null
  private messageQueue: OutgoingMessage[] = []
  private topicId: string

  /**
   * Default configuration
   */
  private static readonly DEFAULT_CONFIG: WebSocketConfig = {
    baseUrl: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000',
    enableLogging: process.env.NODE_ENV === 'development',
    reconnectAttempts: 5,
    reconnectDelay: 1000,
    maxReconnectDelay: 30000,
    messageQueueSize: 100,
    pingInterval: 30000
  }

  constructor(topicId: string, config: Partial<WebSocketConfig> = {}) {
    this.topicId = topicId
    this.config = { ...ConversationWebSocket.DEFAULT_CONFIG, ...config }
    this.connect()
  }

  /**
   * Set event handlers
   */
  setHandlers(handlers: WebSocketHandlers): void {
    this.handlers = { ...this.handlers, ...handlers }
  }

  /**
   * Connect to WebSocket server
   */
  private connect(): void {
    if (this.state === ConnectionState.CONNECTING || this.state === ConnectionState.CONNECTED) {
      return
    }

    this.setState(ConnectionState.CONNECTING)
    this.clearReconnectTimer()

    try {
      const url = `${this.config.baseUrl}/ws/conversation/${this.topicId}`

      if (this.config.enableLogging) {
        console.log(`[WebSocket] Connecting to ${url}`)
      }

      this.ws = new WebSocket(url)
      this.setupEventListeners()
    } catch (error) {
      this.handleError(new WebSocketError('Failed to create WebSocket connection'))
    }
  }

  /**
   * Setup WebSocket event listeners
   */
  private setupEventListeners(): void {
    if (!this.ws) return

    this.ws.onopen = () => {
      if (this.config.enableLogging) {
        console.log('[WebSocket] Connected')
      }

      this.setState(ConnectionState.CONNECTED)
      this.reconnectAttempt = 0
      this.handlers.onOpen?.()
      this.startPing()
      this.flushMessageQueue()
    }

    this.ws.onclose = (event) => {
      if (this.config.enableLogging) {
        console.log(`[WebSocket] Disconnected: ${event.code} ${event.reason}`)
      }

      this.setState(ConnectionState.DISCONNECTED)
      this.stopPing()
      this.handlers.onClose?.(event.code, event.reason)

      // Only attempt reconnection for unexpected closures
      if (event.code !== WebSocketCloseCode.NORMAL_CLOSURE) {
        this.scheduleReconnect()
      }
    }

    this.ws.onerror = () => {
      const error = new WebSocketError('WebSocket connection error')
      this.handleError(error)
    }

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as WebSocketMessage

        if (this.config.enableLogging) {
          console.log('[WebSocket] Received:', data)
        }

        this.handlers.onMessage?.(data)
      } catch (error) {
        this.handleError(new WebSocketError('Failed to parse WebSocket message'))
      }
    }
  }

  /**
   * Schedule reconnection attempt
   */
  private scheduleReconnect(): void {
    if (this.reconnectAttempt >= this.config.reconnectAttempts) {
      this.setState(ConnectionState.FAILED)
      this.handleError(new WebSocketError('Max reconnection attempts reached'))
      return
    }

    this.setState(ConnectionState.RECONNECTING)
    this.reconnectAttempt++

    const delay = Math.min(
      this.config.reconnectDelay * Math.pow(2, this.reconnectAttempt - 1),
      this.config.maxReconnectDelay
    )

    if (this.config.enableLogging) {
      console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempt})`)
    }

    this.reconnectTimer = setTimeout(() => {
      this.connect()
    }, delay)
  }

  /**
   * Clear reconnection timer
   */
  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
  }

  /**
   * Start ping mechanism to keep connection alive
   */
  private startPing(): void {
    this.pingTimer = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        // Send ping message (server should respond with pong)
        this.ws.send(JSON.stringify({ type: 'ping' }))
      }
    }, this.config.pingInterval)
  }

  /**
   * Stop ping mechanism
   */
  private stopPing(): void {
    if (this.pingTimer) {
      clearInterval(this.pingTimer)
      this.pingTimer = null
    }
  }

  /**
   * Update connection state and notify handlers
   */
  private setState(newState: ConnectionState): void {
    if (this.state !== newState) {
      this.state = newState
      this.handlers.onStateChange?.(newState)
    }
  }

  /**
   * Handle WebSocket errors
   */
  private handleError(error: WebSocketError): void {
    if (this.config.enableLogging) {
      console.error('[WebSocket] Error:', error)
    }
    this.handlers.onError?.(error)
  }

  /**
   * Add message to queue
   */
  private queueMessage(message: OutgoingMessage): void {
    if (this.messageQueue.length >= this.config.messageQueueSize) {
      this.messageQueue.shift() // Remove oldest message
    }
    this.messageQueue.push(message)
  }

  /**
   * Send all queued messages
   */
  private flushMessageQueue(): void {
    while (this.messageQueue.length > 0 && this.ws?.readyState === WebSocket.OPEN) {
      const message = this.messageQueue.shift()!
      this.sendMessageNow(message)
    }
  }

  /**
   * Send message immediately without queuing
   */
  private sendMessageNow(message: OutgoingMessage): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))

      if (this.config.enableLogging) {
        console.log('[WebSocket] Sent:', message)
      }
    }
  }

  // ================================
  // Public API
  // ================================

  /**
   * Send a message to the server
   */
  sendMessage(message: string): void {
    const outgoingMessage: OutgoingMessage = { message }

    if (this.state === ConnectionState.CONNECTED) {
      this.sendMessageNow(outgoingMessage)
    } else {
      this.queueMessage(outgoingMessage)
    }
  }

  /**
   * Close the WebSocket connection
   */
  close(code: number = WebSocketCloseCode.NORMAL_CLOSURE, reason?: string): void {
    this.clearReconnectTimer()
    this.stopPing()

    if (this.ws) {
      this.ws.close(code, reason)
      this.ws = null
    }

    this.setState(ConnectionState.DISCONNECTED)
  }

  /**
   * Manually trigger reconnection
   */
  reconnect(): void {
    this.close()
    this.reconnectAttempt = 0
    this.connect()
  }

  /**
   * Get current connection state
   */
  getState(): ConnectionState {
    return this.state
  }

  /**
   * Check if WebSocket is connected
   */
  isConnected(): boolean {
    return this.state === ConnectionState.CONNECTED
  }

  /**
   * Get connection statistics
   */
  getStats(): {
    state: ConnectionState
    reconnectAttempt: number
    queuedMessages: number
    topicId: string
  } {
    return {
      state: this.state,
      reconnectAttempt: this.reconnectAttempt,
      queuedMessages: this.messageQueue.length,
      topicId: this.topicId
    }
  }

  /**
   * Update configuration
   */
  updateConfig(config: Partial<WebSocketConfig>): void {
    this.config = { ...this.config, ...config }
  }
}

/**
 * Factory function to create WebSocket client
 */
export function createConversationWebSocket(
  topicId: string,
  config?: Partial<WebSocketConfig>
): ConversationWebSocket {
  return new ConversationWebSocket(topicId, config)
}