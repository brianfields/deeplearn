'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import Header from './Header'
import Sidebar from './Sidebar'

interface LayoutProps {
  children: React.ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)

  const toggleSidebar = () => {
    setIsSidebarCollapsed(!isSidebarCollapsed)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="flex">
        <Sidebar 
          isCollapsed={isSidebarCollapsed}
          onToggleCollapse={toggleSidebar}
        />
        <motion.main
          initial={false}
          animate={{ 
            marginLeft: isSidebarCollapsed ? 80 : 256,
            width: isSidebarCollapsed ? 'calc(100% - 80px)' : 'calc(100% - 256px)'
          }}
          transition={{ duration: 0.3, ease: 'easeInOut' }}
          className="flex-1 pt-6"
        >
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            {children}
          </div>
        </motion.main>
      </div>
    </div>
  )
}