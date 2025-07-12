'use client'

import { useState } from 'react'
import { usePathname } from 'next/navigation'
import Link from 'next/link'
import { motion } from 'framer-motion'
import {
  Home,
  BookOpen,
  Trophy,
  BarChart3,
  Users,
  Calendar,
  Settings,
  ChevronLeft,
  ChevronRight,
  MessageSquare
} from 'lucide-react'

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'AI Learning', href: '/learn', icon: MessageSquare },
  { name: 'My Courses', href: '/courses', icon: BookOpen },
  { name: 'Achievements', href: '/achievements', icon: Trophy },
  { name: 'Progress', href: '/progress', icon: BarChart3 },
  { name: 'Study Groups', href: '/groups', icon: Users },
  { name: 'Schedule', href: '/schedule', icon: Calendar },
  { name: 'Settings', href: '/settings', icon: Settings },
]

interface SidebarProps {
  isCollapsed: boolean
  onToggleCollapse: () => void
}

export default function Sidebar({ isCollapsed, onToggleCollapse }: SidebarProps) {
  const pathname = usePathname()

  return (
    <motion.div
      initial={false}
      animate={{ width: isCollapsed ? 80 : 256 }}
      transition={{ duration: 0.3, ease: 'easeInOut' }}
      className="fixed left-0 top-16 h-[calc(100vh-4rem)] glass-effect border-r border-gray-200/50 z-40"
    >
      <div className="flex flex-col h-full">
        {/* Toggle button */}
        <div className="flex justify-end p-4 border-b border-gray-200/50">
          <button
            onClick={onToggleCollapse}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            {isCollapsed ? (
              <ChevronRight className="h-4 w-4 text-gray-500" />
            ) : (
              <ChevronLeft className="h-4 w-4 text-gray-500" />
            )}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-6 space-y-2">
          {navigation.map((item) => {
            const isActive = pathname === item.href
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`
                  flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200
                  ${isActive
                    ? 'bg-blue-50 text-blue-700 border-r-2 border-blue-500'
                    : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                  }
                `}
              >
                <item.icon className={`h-5 w-5 ${isActive ? 'text-blue-700' : 'text-gray-500'}`} />
                <motion.span
                  initial={false}
                  animate={{
                    opacity: isCollapsed ? 0 : 1,
                    x: isCollapsed ? -10 : 0
                  }}
                  transition={{ duration: 0.2 }}
                  className="ml-3 whitespace-nowrap"
                >
                  {item.name}
                </motion.span>
              </Link>
            )
          })}
        </nav>

        {/* Footer */}
        <motion.div
          initial={false}
          animate={{ opacity: isCollapsed ? 0 : 1 }}
          transition={{ duration: 0.2 }}
          className="p-4 border-t border-gray-200/50"
        >
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-4">
            <h3 className="text-sm font-medium text-gray-900 mb-1">
              Upgrade to Pro
            </h3>
            <p className="text-xs text-gray-600 mb-3">
              Unlock advanced features and unlimited courses
            </p>
            <button className="w-full bg-gradient-to-r from-blue-500 to-purple-500 text-white text-xs font-medium py-2 px-3 rounded-lg hover:from-blue-600 hover:to-purple-600 transition-all duration-200">
              Upgrade Now
            </button>
          </div>
        </motion.div>
      </div>
    </motion.div>
  )
}