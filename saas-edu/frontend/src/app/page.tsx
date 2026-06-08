// saas-edu/frontend/src/app/page.tsx
'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/lib/store'

export default function HomePage() {
  const router = useRouter()
  const { isAuthenticated, isAuthenticatedLoading } = useAuthStore()

  useEffect(() => {
    if (isAuthenticatedLoading) return
    if (isAuthenticated) {
      router.replace('/dashboard')
    } else {
      router.replace('/login')
    }
  }, [isAuthenticated, isAuthenticatedLoading, router])

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="animate-pulse text-gray-500">Redirigiendo...</div>
    </div>
  )
}