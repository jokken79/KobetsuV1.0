'use client'

import { usePathname } from 'next/navigation'
import { SidebarClient } from './SidebarClient'
import { Header } from './Header'

interface MainLayoutProps {
  children: React.ReactNode
}

export function MainLayout({ children }: MainLayoutProps) {
  const pathname = usePathname()
  const isLoginPage = pathname === '/login'

  // For login page, render without sidebar/header wrapper
  if (isLoginPage) {
    return <>{children}</>
  }

  // For all other pages, render with full layout
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Sidebar */}
      <SidebarClient />

      {/* Main Content */}
      <div className="lg:ml-72 min-h-screen flex flex-col">
        {/* Header */}
        <Header />

        {/* Page Content */}
        <main className="flex-1 p-4 lg:p-6 pt-20 lg:pt-6">
          <div className="animate-fade-in">
            {children}
          </div>
        </main>

        {/* Footer */}
        <footer className="py-4 px-6 text-center text-sm text-gray-500 border-t border-gray-200 bg-white">
          <p>&copy; {new Date().getFullYear()} UNS Kikaku All rights reserved.</p>
        </footer>
      </div>
    </div>
  )
}
