'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Search, 
  Filter, 
  BookOpen, 
  Clock, 
  Star, 
  Users,
  ChevronDown,
  Play,
  CheckCircle,
  Plus
} from 'lucide-react'

const categories = [
  'All Courses',
  'Programming',
  'Data Science',
  'Design',
  'Business',
  'Marketing',
  'Personal Development'
]

const difficultLevels = ['All Levels', 'Beginner', 'Intermediate', 'Advanced']

const courses = [
  {
    id: 1,
    title: 'Advanced React Patterns',
    instructor: 'Sarah Johnson',
    category: 'Programming',
    difficulty: 'Advanced',
    duration: '12 hours',
    students: 1234,
    rating: 4.8,
    price: 89,
    image: '/api/placeholder/400/250',
    progress: 78,
    enrolled: true,
    description: 'Master advanced React patterns including compound components, render props, and custom hooks.'
  },
  {
    id: 2,
    title: 'Machine Learning Fundamentals',
    instructor: 'Dr. Michael Chen',
    category: 'Data Science',
    difficulty: 'Intermediate',
    duration: '18 hours',
    students: 2156,
    rating: 4.9,
    price: 129,
    image: '/api/placeholder/400/250',
    progress: 45,
    enrolled: true,
    description: 'Learn the core concepts of machine learning with hands-on Python projects.'
  },
  {
    id: 3,
    title: 'TypeScript Deep Dive',
    instructor: 'Alex Rodriguez',
    category: 'Programming',
    difficulty: 'Intermediate',
    duration: '8 hours',
    students: 987,
    rating: 4.7,
    price: 69,
    image: '/api/placeholder/400/250',
    progress: 92,
    enrolled: true,
    description: 'Master TypeScript with advanced types, generics, and best practices.'
  },
  {
    id: 4,
    title: 'UI/UX Design Mastery',
    instructor: 'Emma Davis',
    category: 'Design',
    difficulty: 'Beginner',
    duration: '15 hours',
    students: 3421,
    rating: 4.8,
    price: 99,
    image: '/api/placeholder/400/250',
    progress: 0,
    enrolled: false,
    description: 'Learn design thinking, user research, and create beautiful interfaces.'
  },
  {
    id: 5,
    title: 'Python for Data Analysis',
    instructor: 'Dr. Rachel Kim',
    category: 'Data Science',
    difficulty: 'Beginner',
    duration: '14 hours',
    students: 1876,
    rating: 4.6,
    price: 79,
    image: '/api/placeholder/400/250',
    progress: 0,
    enrolled: false,
    description: 'Analyze data using Python, pandas, and visualization libraries.'
  },
  {
    id: 6,
    title: 'Digital Marketing Strategy',
    instructor: 'Mark Thompson',
    category: 'Marketing',
    difficulty: 'Intermediate',
    duration: '10 hours',
    students: 2341,
    rating: 4.5,
    price: 89,
    image: '/api/placeholder/400/250',
    progress: 0,
    enrolled: false,
    description: 'Build comprehensive digital marketing campaigns that drive results.'
  },
]

export default function CoursesView() {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('All Courses')
  const [selectedDifficulty, setSelectedDifficulty] = useState('All Levels')
  const [showFilters, setShowFilters] = useState(false)

  const filteredCourses = courses.filter(course => {
    const matchesSearch = course.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         course.instructor.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesCategory = selectedCategory === 'All Courses' || course.category === selectedCategory
    const matchesDifficulty = selectedDifficulty === 'All Levels' || course.difficulty === selectedDifficulty
    
    return matchesSearch && matchesCategory && matchesDifficulty
  })

  const enrolledCourses = filteredCourses.filter(course => course.enrolled)
  const availableCourses = filteredCourses.filter(course => !course.enrolled)

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
      >
        <div>
          <h1 className="text-3xl font-bold text-gray-900">My Courses</h1>
          <p className="text-gray-600 mt-1">Continue learning and explore new topics</p>
        </div>
        <button className="button-primary flex items-center space-x-2">
          <Plus className="h-4 w-4" />
          <span>Browse All Courses</span>
        </button>
      </motion.div>

      {/* Search and Filters */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
        className="card"
      >
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search courses..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="button-secondary flex items-center space-x-2"
          >
            <Filter className="h-4 w-4" />
            <span>Filters</span>
            <ChevronDown className={`h-4 w-4 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
          </button>
        </div>

        {showFilters && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
            className="mt-4 pt-4 border-t border-gray-200 grid grid-cols-1 sm:grid-cols-2 gap-4"
          >
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Category</label>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {categories.map(category => (
                  <option key={category} value={category}>{category}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Difficulty</label>
              <select
                value={selectedDifficulty}
                onChange={(e) => setSelectedDifficulty(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {difficultLevels.map(level => (
                  <option key={level} value={level}>{level}</option>
                ))}
              </select>
            </div>
          </motion.div>
        )}
      </motion.div>

      {/* Continue Learning Section */}
      {enrolledCourses.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Continue Learning</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {enrolledCourses.map((course, index) => (
              <motion.div
                key={course.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="card group cursor-pointer hover:shadow-strong"
              >
                <div className="aspect-video bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg mb-4 flex items-center justify-center relative overflow-hidden">
                  <BookOpen className="h-12 w-12 text-white" />
                  <div className="absolute inset-0 bg-black bg-opacity-20 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                    <Play className="h-8 w-8 text-white" />
                  </div>
                </div>
                <div className="space-y-3">
                  <div>
                    <h3 className="font-semibold text-gray-900">{course.title}</h3>
                    <p className="text-sm text-gray-500">by {course.instructor}</p>
                  </div>
                  <div className="flex items-center space-x-4 text-sm text-gray-500">
                    <div className="flex items-center">
                      <Clock className="h-4 w-4 mr-1" />
                      {course.duration}
                    </div>
                    <div className="flex items-center">
                      <Users className="h-4 w-4 mr-1" />
                      {course.students.toLocaleString()}
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700">Progress</span>
                      <span className="text-sm font-medium text-gray-700">{course.progress}%</span>
                    </div>
                    <div className="progress-bar">
                      <div
                        className="progress-fill"
                        style={{ width: `${course.progress}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Available Courses Section */}
      {availableCourses.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
        >
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Discover New Courses</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {availableCourses.map((course, index) => (
              <motion.div
                key={course.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="card group cursor-pointer hover:shadow-strong"
              >
                <div className="aspect-video bg-gradient-to-br from-green-500 to-blue-600 rounded-lg mb-4 flex items-center justify-center relative overflow-hidden">
                  <BookOpen className="h-12 w-12 text-white" />
                  <div className="absolute top-2 right-2 bg-white rounded-full px-2 py-1">
                    <span className="text-xs font-semibold text-gray-900">${course.price}</span>
                  </div>
                </div>
                <div className="space-y-3">
                  <div>
                    <h3 className="font-semibold text-gray-900">{course.title}</h3>
                    <p className="text-sm text-gray-500">by {course.instructor}</p>
                  </div>
                  <p className="text-sm text-gray-600 line-clamp-2">{course.description}</p>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4 text-sm text-gray-500">
                      <div className="flex items-center">
                        <Star className="h-4 w-4 mr-1 text-yellow-400 fill-current" />
                        {course.rating}
                      </div>
                      <div className="flex items-center">
                        <Clock className="h-4 w-4 mr-1" />
                        {course.duration}
                      </div>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      course.difficulty === 'Beginner' ? 'bg-green-100 text-green-800' :
                      course.difficulty === 'Intermediate' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {course.difficulty}
                    </span>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  )
}