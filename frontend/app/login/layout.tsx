import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Login | UNS Kobetsu Keiyakusho',
  description: 'Sign in to the UNS Kobetsu Keiyakusho Management System',
}

export default function LoginLayout({
  children,
}: {
  children: React.ReactNode
}) {
  // Login page has its own layout without sidebar/header
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      {children}
    </div>
  )
}
