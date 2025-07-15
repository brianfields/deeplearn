'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  ChevronLeft, 
  ChevronRight, 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertCircle,
  Trophy,
  RotateCcw,
  BookOpen,
  Target
} from 'lucide-react'

interface QuizInterfaceProps {
  quizId: string
}

const quiz = {
  id: '1',
  title: 'React Hooks Fundamentals',
  course: 'Advanced React Patterns',
  totalQuestions: 10,
  timeLimit: 1800, // 30 minutes in seconds
  questions: [
    {
      id: 1,
      question: 'What is the primary purpose of React Hooks?',
      type: 'multiple-choice',
      options: [
        'To replace class components entirely',
        'To allow state and lifecycle features in functional components',
        'To improve performance of React applications',
        'To simplify component styling'
      ],
      correct: 1,
      explanation: 'React Hooks allow you to use state and other React features without writing class components, making functional components more powerful.'
    },
    {
      id: 2,
      question: 'Which hook would you use to perform side effects in a functional component?',
      type: 'multiple-choice',
      options: [
        'useState',
        'useEffect',
        'useContext',
        'useReducer'
      ],
      correct: 1,
      explanation: 'useEffect is the hook designed for performing side effects in functional components, replacing lifecycle methods like componentDidMount and componentDidUpdate.'
    },
    {
      id: 3,
      question: 'What are the Rules of Hooks?',
      type: 'multiple-choice',
      options: [
        'Only call hooks in class components',
        'Only call hooks at the top level and from React functions',
        'Hooks can be called conditionally',
        'Hooks should be called in loops for better performance'
      ],
      correct: 1,
      explanation: 'The Rules of Hooks state that you should only call hooks at the top level of React functions and never inside loops, conditions, or nested functions.'
    },
    {
      id: 4,
      question: 'Complete the code: const [count, setCount] = ________(0);',
      type: 'fill-in-blank',
      answer: 'useState',
      explanation: 'useState is the hook used to add state to functional components. It returns an array with the current state value and a function to update it.'
    },
    {
      id: 5,
      question: 'What will happen if you call hooks conditionally?',
      type: 'multiple-choice',
      options: [
        'The component will render faster',
        'React will throw an error',
        'The hooks will work normally',
        'The component will unmount'
      ],
      correct: 1,
      explanation: 'Calling hooks conditionally violates the Rules of Hooks and can cause React to throw errors or behave unpredictably.'
    }
  ]
}

export default function QuizInterface({ quizId }: QuizInterfaceProps) {
  const [currentQuestion, setCurrentQuestion] = useState(0)
  const [answers, setAnswers] = useState<{ [key: number]: any }>({})
  const [isSubmitted, setIsSubmitted] = useState(false)
  const [timeLeft, setTimeLeft] = useState(quiz.timeLimit)
  const [showExplanation, setShowExplanation] = useState(false)

  const handleAnswer = (questionId: number, answer: any) => {
    setAnswers(prev => ({
      ...prev,
      [questionId]: answer
    }))
  }

  const handleSubmit = () => {
    setIsSubmitted(true)
    setShowExplanation(true)
  }

  const calculateScore = () => {
    let correct = 0
    quiz.questions.forEach(question => {
      const userAnswer = answers[question.id]
      if (question.type === 'multiple-choice' && userAnswer === question.correct) {
        correct++
      } else if (question.type === 'fill-in-blank' && userAnswer?.toLowerCase() === question.answer?.toLowerCase()) {
        correct++
      }
    })
    return Math.round((correct / quiz.questions.length) * 100)
  }

  const currentQ = quiz.questions[currentQuestion]
  const isAnswered = answers[currentQ.id] !== undefined
  const score = calculateScore()

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  if (isSubmitted) {
    return (
      <div className="max-w-4xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-center py-12"
        >
          <div className="mb-8">
            <div className={`inline-flex items-center justify-center w-20 h-20 rounded-full mb-4 ${
              score >= 80 ? 'bg-green-100' : score >= 60 ? 'bg-yellow-100' : 'bg-red-100'
            }`}>
              {score >= 80 ? (
                <Trophy className="h-10 w-10 text-green-600" />
              ) : score >= 60 ? (
                <Target className="h-10 w-10 text-yellow-600" />
              ) : (
                <AlertCircle className="h-10 w-10 text-red-600" />
              )}
            </div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Quiz Complete!</h1>
            <p className="text-xl text-gray-600">Your Score: {score}%</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="card text-center">
              <div className="text-2xl font-bold text-blue-600 mb-2">
                {quiz.questions.filter(q => {
                  const userAnswer = answers[q.id]
                  return q.type === 'multiple-choice' ? userAnswer === q.correct : 
                         userAnswer?.toLowerCase() === q.answer?.toLowerCase()
                }).length}
              </div>
              <div className="text-sm text-gray-600">Correct Answers</div>
            </div>
            <div className="card text-center">
              <div className="text-2xl font-bold text-gray-900 mb-2">{quiz.questions.length}</div>
              <div className="text-sm text-gray-600">Total Questions</div>
            </div>
            <div className="card text-center">
              <div className="text-2xl font-bold text-purple-600 mb-2">
                {formatTime(quiz.timeLimit - timeLeft)}
              </div>
              <div className="text-sm text-gray-600">Time Taken</div>
            </div>
          </div>

          <div className="flex justify-center space-x-4">
            <button 
              onClick={() => setShowExplanation(!showExplanation)}
              className="button-primary"
            >
              {showExplanation ? 'Hide' : 'Show'} Explanations
            </button>
            <button className="button-secondary flex items-center space-x-2">
              <RotateCcw className="h-4 w-4" />
              <span>Retake Quiz</span>
            </button>
          </div>
        </motion.div>

        {showExplanation && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="space-y-6"
          >
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Review Answers</h2>
            {quiz.questions.map((question, index) => {
              const userAnswer = answers[question.id]
              const isCorrect = question.type === 'multiple-choice' ? 
                userAnswer === question.correct : 
                userAnswer?.toLowerCase() === question.answer?.toLowerCase()

              return (
                <div key={question.id} className="card">
                  <div className="flex items-start space-x-3">
                    <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                      isCorrect ? 'bg-green-100' : 'bg-red-100'
                    }`}>
                      {isCorrect ? (
                        <CheckCircle className="h-5 w-5 text-green-600" />
                      ) : (
                        <XCircle className="h-5 w-5 text-red-600" />
                      )}
                    </div>
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900 mb-3">
                        {index + 1}. {question.question}
                      </h3>
                      
                      {question.type === 'multiple-choice' && (
                        <div className="space-y-2 mb-4">
                          {question.options?.map((option, optionIndex) => (
                            <div 
                              key={optionIndex}
                              className={`p-3 rounded-lg border ${
                                optionIndex === question.correct ? 'border-green-500 bg-green-50' :
                                optionIndex === userAnswer ? 'border-red-500 bg-red-50' :
                                'border-gray-200'
                              }`}
                            >
                              <div className="flex items-center justify-between">
                                <span>{option}</span>
                                {optionIndex === question.correct && (
                                  <CheckCircle className="h-4 w-4 text-green-600" />
                                )}
                                {optionIndex === userAnswer && optionIndex !== question.correct && (
                                  <XCircle className="h-4 w-4 text-red-600" />
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}

                      {question.type === 'fill-in-blank' && (
                        <div className="mb-4">
                          <div className="flex items-center space-x-2">
                            <span className="text-gray-600">Your answer:</span>
                            <span className={`font-medium ${isCorrect ? 'text-green-600' : 'text-red-600'}`}>
                              {userAnswer || 'No answer provided'}
                            </span>
                          </div>
                          <div className="flex items-center space-x-2 mt-1">
                            <span className="text-gray-600">Correct answer:</span>
                            <span className="font-medium text-green-600">{question.answer}</span>
                          </div>
                        </div>
                      )}

                      <div className="bg-blue-50 p-3 rounded-lg">
                        <p className="text-sm text-blue-800">
                          <strong>Explanation:</strong> {question.explanation}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
          </motion.div>
        )}
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{quiz.title}</h1>
          <p className="text-gray-600">{quiz.course}</p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 text-gray-600">
            <Clock className="h-4 w-4" />
            <span>{formatTime(timeLeft)}</span>
          </div>
          <div className="text-sm text-gray-500">
            {currentQuestion + 1} / {quiz.questions.length}
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-8">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm text-gray-600">Progress</span>
          <span className="text-sm text-gray-600">
            {Math.round(((currentQuestion + 1) / quiz.questions.length) * 100)}%
          </span>
        </div>
        <div className="progress-bar">
          <div 
            className="progress-fill"
            style={{ width: `${((currentQuestion + 1) / quiz.questions.length) * 100}%` }}
          ></div>
        </div>
      </div>

      {/* Question */}
      <AnimatePresence mode="wait">
        <motion.div
          key={currentQuestion}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          transition={{ duration: 0.3 }}
          className="card mb-8"
        >
          <h2 className="text-xl font-semibold text-gray-900 mb-6">
            {currentQuestion + 1}. {currentQ.question}
          </h2>

          {currentQ.type === 'multiple-choice' && (
            <div className="space-y-3">
              {currentQ.options?.map((option, index) => (
                <button
                  key={index}
                  onClick={() => handleAnswer(currentQ.id, index)}
                  className={`w-full p-4 text-left rounded-lg border-2 transition-all duration-200 ${
                    answers[currentQ.id] === index
                      ? 'border-blue-500 bg-blue-50 text-blue-700'
                      : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <div className={`w-4 h-4 rounded-full border-2 ${
                      answers[currentQ.id] === index
                        ? 'border-blue-500 bg-blue-500'
                        : 'border-gray-300'
                    }`}>
                      {answers[currentQ.id] === index && (
                        <div className="w-2 h-2 bg-white rounded-full m-0.5"></div>
                      )}
                    </div>
                    <span>{option}</span>
                  </div>
                </button>
              ))}
            </div>
          )}

          {currentQ.type === 'fill-in-blank' && (
            <div>
              <input
                type="text"
                placeholder="Type your answer here..."
                value={answers[currentQ.id] || ''}
                onChange={(e) => handleAnswer(currentQ.id, e.target.value)}
                className="w-full p-4 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-blue-500 text-lg"
              />
            </div>
          )}
        </motion.div>
      </AnimatePresence>

      {/* Navigation */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => setCurrentQuestion(Math.max(0, currentQuestion - 1))}
          disabled={currentQuestion === 0}
          className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
            currentQuestion === 0
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
              : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
          }`}
        >
          <ChevronLeft className="h-4 w-4" />
          <span>Previous</span>
        </button>

        <div className="flex space-x-2">
          {quiz.questions.map((_, index) => (
            <button
              key={index}
              onClick={() => setCurrentQuestion(index)}
              className={`w-8 h-8 rounded-lg transition-colors ${
                index === currentQuestion
                  ? 'bg-blue-500 text-white'
                  : answers[quiz.questions[index].id] !== undefined
                  ? 'bg-green-100 text-green-600 border border-green-300'
                  : 'bg-gray-100 text-gray-400 border border-gray-300'
              }`}
            >
              {index + 1}
            </button>
          ))}
        </div>

        {currentQuestion === quiz.questions.length - 1 ? (
          <button
            onClick={handleSubmit}
            disabled={!isAnswered}
            className={`flex items-center space-x-2 px-6 py-2 rounded-lg transition-colors ${
              isAnswered
                ? 'bg-green-600 text-white hover:bg-green-700'
                : 'bg-gray-100 text-gray-400 cursor-not-allowed'
            }`}
          >
            <span>Submit Quiz</span>
          </button>
        ) : (
          <button
            onClick={() => setCurrentQuestion(Math.min(quiz.questions.length - 1, currentQuestion + 1))}
            disabled={!isAnswered}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
              isAnswered
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'bg-gray-100 text-gray-400 cursor-not-allowed'
            }`}
          >
            <span>Next</span>
            <ChevronRight className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  )
}