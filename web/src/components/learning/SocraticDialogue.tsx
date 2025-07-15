'use client'

import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, MessageCircle, Lightbulb, CheckCircle, Brain, Sparkles, HelpCircle, User, Bot } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import type { SocraticDialogueProps } from '@/types/components'

interface SocraticMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  isGuiding?: boolean
}

export default function SocraticDialogue({
  dialogue,
  onComplete,
  isLoading = false
}: SocraticDialogueProps) {
  const [messages, setMessages] = useState<SocraticMessage[]>([
    {
      id: '1',
      role: 'assistant',
      content: dialogue.starting_prompt,
      timestamp: new Date(),
      isGuiding: true
    }
  ])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [insights, setInsights] = useState<string[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async () => {
    if (!input.trim() || isTyping) return

    const userMessage: SocraticMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsTyping(true)

    // Simulate AI response (in real app, this would call your AI service)
    setTimeout(() => {
      const responses = [
        "That&apos;s an interesting perspective. Can you tell me more about why you think that?",
        "What evidence supports that conclusion?",
        "How might someone disagree with that viewpoint?",
        "What assumptions are you making here?",
        "Can you think of an example that illustrates this concept?",
        "What would happen if we changed one variable in this scenario?"
      ]

      const assistantMessage: SocraticMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: responses[Math.floor(Math.random() * responses.length)],
        timestamp: new Date(),
        isGuiding: true
      }

      setMessages(prev => [...prev, assistantMessage])
      setIsTyping(false)

      // Add insight occasionally
      if (Math.random() > 0.7) {
        const newInsight = `Understanding gained from: "${userMessage.content.slice(0, 50)}..."`
        setInsights(prev => [...prev, newInsight])
      }
    }, 1000 + Math.random() * 1000)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleComplete = () => {
    const insights = messages
      .filter(msg => msg.role === 'user')
      .map(msg => msg.content)

    onComplete({
      componentType: 'socratic_dialogue',
      timeSpent: 0,
      completed: true,
      data: { insights }
    })
  }

  const quickPrompts = [
    "I need a hint",
    "Can you give me an example?",
    "I'm not sure about this",
    "Let me think differently"
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-100 flex flex-col">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white/90 backdrop-blur-sm border-b border-purple-200 p-4"
      >
        <div className="max-w-2xl mx-auto">
          <div className="flex items-center gap-2 mb-2">
            <MessageCircle className="w-5 h-5 text-purple-600" />
            <span className="text-sm font-medium text-purple-600">Explore</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">
            {dialogue.title}
          </h1>
          <p className="text-gray-600 text-sm sm:text-base mb-4">
            Exploring: {dialogue.concept}
          </p>
          <p className="text-gray-500 text-xs sm:text-sm">
            {dialogue.dialogue_objective}
          </p>
        </div>
      </motion.div>

      {/* Messages Area */}
      <div className="flex-1 flex flex-col min-h-0">
        <ScrollArea className="flex-1 p-4">
          <div className="max-w-2xl mx-auto space-y-4">
            <AnimatePresence>
              {messages.map((message) => (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                      message.role === 'user'
                        ? 'bg-purple-600 text-white'
                        : message.isGuiding
                        ? 'bg-gradient-to-r from-purple-100 to-pink-100 text-gray-800 border border-purple-200'
                        : 'bg-white text-gray-800 border border-gray-200'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      {message.role === 'user' ? (
                        <User className="w-3 h-3 opacity-70" />
                      ) : (
                        <Bot className="w-3 h-3 opacity-70" />
                      )}
                      <span className="text-xs opacity-70">
                        {message.role === 'user' ? 'You' : 'Guide'}
                      </span>
                    </div>
                    <p className="text-sm leading-relaxed">{message.content}</p>
                    <div className="text-xs opacity-60 mt-1">
                      {message.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>

            {/* Typing Indicator */}
            {isTyping && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex justify-start"
              >
                <div className="bg-white rounded-2xl px-4 py-3 border border-gray-200">
                  <div className="flex items-center gap-2">
                    <Bot className="w-3 h-3 text-gray-600" />
                    <span className="text-xs text-gray-600">Guide</span>
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-sm text-gray-600">Thinking</span>
                    <div className="flex gap-1">
                      <div className="w-1 h-1 bg-gray-400 rounded-full animate-bounce" />
                      <div className="w-1 h-1 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <div className="w-1 h-1 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>

        {/* Insights Panel */}
        {insights.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-gradient-to-r from-yellow-50 to-orange-50 border-t border-yellow-200 p-4"
          >
            <div className="max-w-2xl mx-auto">
              <div className="flex items-center gap-2 mb-2">
                <Lightbulb className="w-4 h-4 text-yellow-600" />
                <span className="text-sm font-medium text-yellow-800">Insights Gained</span>
              </div>
              <div className="space-y-1">
                {insights.map((insight, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="text-sm text-yellow-700 bg-yellow-100 rounded-lg px-3 py-2"
                  >
                    {insight}
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.div>
        )}

        {/* Input Area */}
        <div className="bg-white/90 backdrop-blur-sm border-t border-purple-200 p-4">
          <div className="max-w-2xl mx-auto">
            {/* Quick Prompts */}
            <div className="mb-3">
              <div className="flex flex-wrap gap-2">
                {quickPrompts.map((prompt, index) => (
                  <Button
                    key={index}
                    variant="outline"
                    size="sm"
                    onClick={() => setInput(prompt)}
                    className="text-xs bg-purple-50 border-purple-200 hover:bg-purple-100"
                  >
                    <HelpCircle className="w-3 h-3 mr-1" />
                    {prompt}
                  </Button>
                ))}
              </div>
            </div>

            {/* Input */}
            <div className="flex gap-2">
              <Input
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Share your thoughts..."
                className="flex-1 bg-white/80 border-purple-200 focus:border-purple-400"
                disabled={isTyping}
              />
              <Button
                onClick={handleSendMessage}
                disabled={!input.trim() || isTyping}
                className="bg-purple-600 hover:bg-purple-700 text-white"
              >
                <Send className="w-4 h-4" />
              </Button>
            </div>

            {/* Complete Button */}
            <div className="mt-4 flex justify-center">
              <Button
                onClick={handleComplete}
                disabled={messages.length < 4 || isLoading}
                className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white"
              >
                {isLoading ? (
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Processing...
                  </div>
                ) : (
                  "Complete Exploration"
                )}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}