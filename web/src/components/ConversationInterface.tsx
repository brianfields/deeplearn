'use client'

import React, { useState, useEffect, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import ProgressSidebar from './ProgressSidebar'
import {
  Send,
  MessageSquare,
  Brain,
  Target,
  CheckCircle,
  AlertCircle,
  Wifi,
  WifiOff,
  User,
  Bot,
  X
} from 'lucide-react'
import { ConversationWebSocket, ChatMessage } from '@/lib/api'
import { ProgressUpdate, SessionState } from '@/types'

interface ConversationInterfaceProps {
  topicId: string
  topicTitle: string
  onClose: () => void
}

export default function ConversationInterface({ topicId, topicTitle, onClose }: ConversationInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isConnected, setIsConnected] = useState(false)
  const [progress, setProgress] = useState<ProgressUpdate | null>(null)
  const [sessionState, setSessionState] = useState<SessionState | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const wsRef = useRef<ConversationWebSocket | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    const ws = new ConversationWebSocket(topicId)
    wsRef.current = ws

    ws.onopen = () => {
      setIsConnected(true)
      setError(null)
    }

    ws.onclose = () => {
      setIsConnected(false)
    }

    ws.onerror = (error) => {
      setError('Connection error. Please try again.')
      setIsConnected(false)
    }

    ws.onmessage = (data) => {
      if (data.type === 'chat_message') {
        setMessages(prev => [...prev, data.message as ChatMessage])
        setIsLoading(false)
      } else if (data.type === 'progress_update') {
        setProgress(data.progress as ProgressUpdate)
      } else if (data.type === 'session_state') {
        setSessionState(data.state as SessionState)
      }
    }

    return () => {
      ws.close()
    }
  }, [topicId])

  const sendMessage = async () => {
    if (!inputMessage.trim() || !wsRef.current || !isConnected) return

    const userMessage: ChatMessage = {
      role: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)
    setInputMessage('')

    try {
      wsRef.current.sendMessage(inputMessage)
    } catch (error) {
      setError('Failed to send message. Please try again.')
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const quickActions = [
    { text: "I need help understanding this", icon: Brain },
    { text: "Can you give me an example?", icon: Target },
    { text: "I think I get it now", icon: CheckCircle },
    { text: "This is confusing", icon: AlertCircle }
  ]

  return (
    <div className="h-full flex bg-gray-50/30 backdrop-blur-sm">
      {/* Main conversation area - uses flex column with proper height management */}
      <div className="flex-1 flex flex-col min-h-0">
        {/* Fixed Header - explicit height */}
        <header className="h-20 flex-shrink-0 border-b border-gray-200/50 bg-white/80 backdrop-blur-md">
          <div className="h-full px-6 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-500/10 rounded-full flex items-center justify-center">
                <MessageSquare className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <h1 className="font-semibold text-gray-900 text-lg">{topicTitle}</h1>
                <div className="flex items-center gap-2 mt-0.5">
                  {isConnected ? (
                    <>
                      <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                      <span className="text-sm text-green-600 font-medium">Connected</span>
                    </>
                  ) : (
                    <>
                      <div className="w-2 h-2 bg-red-500 rounded-full" />
                      <span className="text-sm text-red-600 font-medium">Disconnected</span>
                    </>
                  )}
                </div>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="hover:bg-gray-100/80 rounded-full w-8 h-8 p-0"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </header>

        {/* Main content area - takes remaining space */}
        <div className="flex-1 flex min-h-0">
          {/* Messages area - scrollable content */}
          <div className="flex-1 flex flex-col min-h-0">
            {/* Scrollable Messages - THIS IS THE ONLY SCROLLING AREA */}
            <div className="flex-1 overflow-y-auto">
              <div className="px-6 py-4 space-y-6">
                {messages.map((message, index) => (
                  <div
                    key={index}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[75%] rounded-2xl px-4 py-3 ${
                        message.role === 'user'
                          ? 'bg-blue-500 text-white shadow-sm'
                          : 'bg-white/80 text-gray-900 shadow-sm border border-gray-200/50 backdrop-blur-sm'
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        {message.role === 'user' ? (
                          <User className="h-3 w-3 opacity-70" />
                        ) : (
                          <Bot className="h-3 w-3 opacity-70" />
                        )}
                        <span className="text-xs font-medium opacity-70">
                          {message.role === 'user' ? 'You' : 'AI Tutor'}
                        </span>
                      </div>
                      <div className="text-sm leading-relaxed whitespace-pre-wrap">
                        {message.content}
                      </div>
                      <div className={`text-xs mt-2 opacity-60 ${
                        message.role === 'user' ? 'text-blue-100' : 'text-gray-500'
                      }`}>
                        {message.timestamp ? new Date(message.timestamp).toLocaleTimeString() : 'Just now'}
                      </div>
                    </div>
                  </div>
                ))}

                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-white/80 backdrop-blur-sm rounded-2xl px-4 py-3 max-w-[75%] shadow-sm border border-gray-200/50">
                      <div className="flex items-center gap-2 mb-1">
                        <Bot className="h-3 w-3 text-gray-600" />
                        <span className="text-xs font-medium text-gray-600">AI Tutor</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-gray-600">Thinking</span>
                        <div className="flex gap-1">
                          <div className="w-1 h-1 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                          <div className="w-1 h-1 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                          <div className="w-1 h-1 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {error && (
                  <div className="flex justify-center">
                    <div className="bg-red-50/80 backdrop-blur-sm border border-red-200/50 rounded-2xl px-4 py-3 text-red-700 text-sm shadow-sm">
                      {error}
                    </div>
                  </div>
                )}
              </div>
              <div ref={messagesEndRef} />
            </div>

            {/* Fixed Input Area - explicit height */}
            <footer className="h-32 flex-shrink-0 border-t border-gray-200/50 bg-white/80 backdrop-blur-md">
              <div className="h-full px-6 py-4 flex flex-col justify-center space-y-3">
                {/* Quick Actions */}
                <div className="flex flex-wrap gap-2">
                  {quickActions.map((action, index) => (
                    <Button
                      key={index}
                      variant="outline"
                      size="sm"
                      onClick={() => setInputMessage(action.text)}
                      className="text-xs bg-white/60 border-gray-200/50 hover:bg-white/80 backdrop-blur-sm"
                      disabled={!isConnected}
                    >
                      <action.icon className="h-3 w-3 mr-1.5" />
                      {action.text}
                    </Button>
                  ))}
                </div>

                {/* Input */}
                <div className="flex gap-3">
                  <Input
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Type your message..."
                    disabled={!isConnected}
                    className="flex-1 bg-white/60 border-gray-200/50 backdrop-blur-sm focus:bg-white/80 transition-all duration-200"
                  />
                  <Button
                    onClick={sendMessage}
                    disabled={!inputMessage.trim() || !isConnected || isLoading}
                    className="bg-blue-500 hover:bg-blue-600 text-white shadow-sm px-4"
                  >
                    <Send className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </footer>
          </div>
        </div>
      </div>

      {/* Fixed Progress Sidebar - explicit width */}
      <ProgressSidebar
        progress={progress}
        sessionState={sessionState}
        topicTitle={topicTitle}
        messageCount={messages.filter(m => m.role === 'user').length}
      />
    </div>
  )
}