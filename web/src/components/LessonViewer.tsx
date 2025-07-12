'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  ChevronLeft, 
  ChevronRight, 
  Play, 
  Pause, 
  Volume2, 
  Maximize, 
  BookOpen,
  CheckCircle,
  Circle,
  MessageSquare,
  Share,
  Bookmark,
  MoreVertical,
  Clock,
  Users,
  Star
} from 'lucide-react'

interface LessonViewerProps {
  courseId: string
  lessonId: string
}

const lesson = {
  id: '1',
  title: 'Introduction to React Hooks',
  courseTitle: 'Advanced React Patterns',
  instructor: 'Sarah Johnson',
  duration: '24:35',
  content: `
# Introduction to React Hooks

React Hooks were introduced in React 16.8 as a way to use state and other React features without writing class components. They allow you to "hook into" React's features from functional components.

## Why Use Hooks?

Hooks solve several problems that developers faced with class components:

1. **Complex components become hard to understand** - Hooks let you split one component into smaller functions based on what pieces are related.

2. **Difficult to reuse stateful logic between components** - Custom hooks make it easy to share stateful logic between components.

3. **Classes confuse both people and machines** - Hooks let you use more of React's features without classes.

## The useState Hook

The \`useState\` hook is the most commonly used hook. It allows you to add state to functional components:

\`\`\`javascript
import React, { useState } from 'react';

function Counter() {
  const [count, setCount] = useState(0);

  return (
    <div>
      <p>You clicked {count} times</p>
      <button onClick={() => setCount(count + 1)}>
        Click me
      </button>
    </div>
  );
}
\`\`\`

## The useEffect Hook

The \`useEffect\` hook lets you perform side effects in functional components. It serves the same purpose as \`componentDidMount\`, \`componentDidUpdate\`, and \`componentWillUnmount\` combined:

\`\`\`javascript
import React, { useState, useEffect } from 'react';

function Example() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    document.title = \`You clicked \${count} times\`;
  });

  return (
    <div>
      <p>You clicked {count} times</p>
      <button onClick={() => setCount(count + 1)}>
        Click me
      </button>
    </div>
  );
}
\`\`\`

## Rules of Hooks

When using hooks, there are two important rules to follow:

1. **Only call hooks at the top level** - Don't call hooks inside loops, conditions, or nested functions.

2. **Only call hooks from React functions** - Call hooks from React function components or custom hooks.

## Custom Hooks

You can create your own hooks to reuse stateful logic between components:

\`\`\`javascript
import { useState, useEffect } from 'react';

function useCounter(initialValue = 0) {
  const [count, setCount] = useState(initialValue);

  const increment = () => setCount(count + 1);
  const decrement = () => setCount(count - 1);
  const reset = () => setCount(initialValue);

  return { count, increment, decrement, reset };
}

// Usage
function CounterComponent() {
  const { count, increment, decrement, reset } = useCounter(0);

  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={increment}>+</button>
      <button onClick={decrement}>-</button>
      <button onClick={reset}>Reset</button>
    </div>
  );
}
\`\`\`

## Summary

React Hooks provide a more direct API to the React concepts you already know. They give you access to escape hatches and don't require you to learn complex functional or reactive programming techniques.

In the next lesson, we'll dive deeper into the \`useEffect\` hook and learn about cleanup functions and dependencies.
  `,
  videoUrl: '/api/placeholder/800/450',
  nextLesson: {
    id: '2',
    title: 'Understanding useEffect Dependencies'
  },
  prevLesson: {
    id: '0',
    title: 'Course Overview'
  }
}

const courseProgress = {
  currentLesson: 1,
  totalLessons: 24,
  completedLessons: [0]
}

export default function LessonViewer({ courseId, lessonId }: LessonViewerProps) {
  const [isPlaying, setIsPlaying] = useState(false)
  const [showTranscript, setShowTranscript] = useState(false)
  const [isBookmarked, setIsBookmarked] = useState(false)

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                <ChevronLeft className="h-5 w-5 text-gray-600" />
              </button>
              <div>
                <h1 className="text-lg font-semibold text-gray-900">{lesson.title}</h1>
                <p className="text-sm text-gray-500">{lesson.courseTitle}</p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <div className="text-sm text-gray-500">
                Lesson {courseProgress.currentLesson} of {courseProgress.totalLessons}
              </div>
              <div className="w-32 bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${(courseProgress.currentLesson / courseProgress.totalLessons) * 100}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-3 space-y-6">
            {/* Video Player */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="bg-black rounded-xl overflow-hidden shadow-strong"
            >
              <div className="aspect-video bg-gradient-to-br from-gray-800 to-gray-900 flex items-center justify-center relative">
                <div className="text-white text-center">
                  <BookOpen className="h-16 w-16 mx-auto mb-4 opacity-50" />
                  <p className="text-lg font-medium">Video Player</p>
                  <p className="text-sm opacity-75">Duration: {lesson.duration}</p>
                </div>
                <button 
                  onClick={() => setIsPlaying(!isPlaying)}
                  className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-40 hover:bg-opacity-60 transition-colors"
                >
                  {isPlaying ? (
                    <Pause className="h-12 w-12 text-white" />
                  ) : (
                    <Play className="h-12 w-12 text-white" />
                  )}
                </button>
              </div>
              <div className="bg-gray-900 p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <button onClick={() => setIsPlaying(!isPlaying)} className="text-white hover:text-gray-300">
                      {isPlaying ? <Pause className="h-5 w-5" /> : <Play className="h-5 w-5" />}
                    </button>
                    <button className="text-white hover:text-gray-300">
                      <Volume2 className="h-5 w-5" />
                    </button>
                    <div className="text-white text-sm">
                      00:00 / {lesson.duration}
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button 
                      onClick={() => setShowTranscript(!showTranscript)}
                      className="text-white hover:text-gray-300 text-sm"
                    >
                      Transcript
                    </button>
                    <button className="text-white hover:text-gray-300">
                      <Maximize className="h-5 w-5" />
                    </button>
                  </div>
                </div>
              </div>
            </motion.div>

            {/* Lesson Info */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="card"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">{lesson.title}</h2>
                  <div className="flex items-center space-x-4 text-sm text-gray-500 mb-4">
                    <div className="flex items-center">
                      <img 
                        src="/api/placeholder/40/40" 
                        alt={lesson.instructor}
                        className="w-6 h-6 rounded-full mr-2"
                      />
                      {lesson.instructor}
                    </div>
                    <div className="flex items-center">
                      <Clock className="h-4 w-4 mr-1" />
                      {lesson.duration}
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setIsBookmarked(!isBookmarked)}
                    className={`p-2 rounded-lg transition-colors ${
                      isBookmarked ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    <Bookmark className="h-5 w-5" />
                  </button>
                  <button className="p-2 bg-gray-100 text-gray-600 hover:bg-gray-200 rounded-lg transition-colors">
                    <Share className="h-5 w-5" />
                  </button>
                  <button className="p-2 bg-gray-100 text-gray-600 hover:bg-gray-200 rounded-lg transition-colors">
                    <MoreVertical className="h-5 w-5" />
                  </button>
                </div>
              </div>
            </motion.div>

            {/* Lesson Content */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="card"
            >
              <div className="prose prose-lg max-w-none">
                <div dangerouslySetInnerHTML={{ __html: lesson.content.replace(/\n/g, '<br>') }} />
              </div>
            </motion.div>

            {/* Navigation */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
              className="flex items-center justify-between"
            >
              {lesson.prevLesson ? (
                <button className="flex items-center space-x-2 p-4 bg-white rounded-lg shadow-soft hover:shadow-medium transition-all duration-200 border border-gray-200">
                  <ChevronLeft className="h-5 w-5 text-gray-600" />
                  <div className="text-left">
                    <div className="text-sm text-gray-500">Previous</div>
                    <div className="font-medium text-gray-900">{lesson.prevLesson.title}</div>
                  </div>
                </button>
              ) : (
                <div></div>
              )}
              
              {lesson.nextLesson && (
                <button className="flex items-center space-x-2 p-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                  <div className="text-right">
                    <div className="text-sm text-blue-100">Next</div>
                    <div className="font-medium">{lesson.nextLesson.title}</div>
                  </div>
                  <ChevronRight className="h-5 w-5" />
                </button>
              )}
            </motion.div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Course Progress */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.4 }}
              className="card"
            >
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Course Progress</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Completed</span>
                  <span className="text-sm font-medium text-gray-900">
                    {courseProgress.completedLessons.length} / {courseProgress.totalLessons}
                  </span>
                </div>
                <div className="progress-bar">
                  <div 
                    className="progress-fill"
                    style={{ width: `${(courseProgress.completedLessons.length / courseProgress.totalLessons) * 100}%` }}
                  ></div>
                </div>
                <div className="text-xs text-gray-500">
                  {Math.round((courseProgress.completedLessons.length / courseProgress.totalLessons) * 100)}% complete
                </div>
              </div>
            </motion.div>

            {/* Lesson Notes */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.5 }}
              className="card"
            >
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Lesson Notes</h3>
              <textarea
                placeholder="Add your notes here..."
                className="w-full h-32 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              />
            </motion.div>

            {/* Discussion */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.6 }}
              className="card"
            >
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Discussion</h3>
              <div className="space-y-3">
                <div className="text-sm text-gray-600">
                  Join the discussion with other students
                </div>
                <button className="w-full button-primary flex items-center justify-center space-x-2">
                  <MessageSquare className="h-4 w-4" />
                  <span>View Discussion</span>
                </button>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  )
}