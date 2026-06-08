// saas-edu/frontend/src/app/(dashboard)/layout.tsx
'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/lib/store'
import Sidebar from '@/components/layout/Sidebar'

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const { isAuthenticated, isAuthenticatedLoading } = useAuthStore()

  useEffect(() => {
    if (!isAuthenticatedLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [isAuthenticated, isAuthenticatedLoading, router])

  if (isAuthenticatedLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (!isAuthenticated) return null

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>
    </div>
  )
}