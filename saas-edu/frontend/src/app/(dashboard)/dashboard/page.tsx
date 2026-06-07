'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuthStore } from '@/lib/store'
import { analyticsService } from '@/services/analytics.service'

export default function DashboardPage() {
  const router = useRouter()
  const { user, isAuthenticated } = useAuthStore()
  const [overview, setOverview] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!isAuthenticated) { router.push('/login'); return }
    if (user?.role === 'admin' || user?.role === 'teacher') {
      analyticsService.getOverview().then(setOverview).catch(console.error).finally(() => setLoading(false))
    } else { setLoading(false) }
  }, [isAuthenticated, user, router])

  if (!isAuthenticated) return null

  const menuItems = [
    { title: 'Documentos', description: 'Gestiona documentos', href: '/dashboard/documents', color: 'bg-blue-50 text-blue-600', icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
    { title: 'Chat IA', description: 'Pregunta sobre documentos', href: '/dashboard/chat', color: 'bg-purple-50 text-purple-600', icon: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z' },
    { title: 'Evaluaciones', description: 'Genera quizzes', href: '/dashboard/evaluations', color: 'bg-green-50 text-green-600', icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4' },
    { title: 'Analíticas', description: 'Progreso de alumnos', href: '/dashboard/analytics', color: 'bg-orange-50 text-orange-600', icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z', roles: ['admin', 'teacher'] },
  ]

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Bienvenido, {user?.first_name}</h1>
        <p className="text-gray-600">{user?.role === 'student' ? 'Tu progreso' : 'Panel de control'}</p>
      </div>
      {user?.role !== 'student' && !loading && overview && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6"><p className="text-sm text-gray-500 mb-1">Documentos</p><p className="text-3xl font-bold">{overview.total_documents}</p></div>
          <div className="bg-white rounded-lg shadow p-6"><p className="text-sm text-gray-500 mb-1">Alumnos (7d)</p><p className="text-3xl font-bold">{overview.active_students_7d}</p></div>
          <div className="bg-white rounded-lg shadow p-6"><p className="text-sm text-gray-500 mb-1">Mensajes hoy</p><p className="text-3xl font-bold">{overview.messages_today}</p></div>
          <div className="bg-white rounded-lg shadow p-6"><p className="text-sm text-gray-500 mb-1">Score promedio</p><p className="text-3xl font-bold">{overview.avg_score ? `${overview.avg_score}%` : 'N/A'}</p></div>
        </div>
      )}
      {!loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {menuItems.filter(i => !i.roles || i.roles.includes(user?.role || '')).map(item => (
            <Link key={item.href} href={item.href} className="block bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6">
              <div className="flex items-start gap-4">
                <div className={`p-3 rounded-lg ${item.color}`}><svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={item.icon} /></svg></div>
                <div><h2 className="text-lg font-semibold text-gray-900">{item.title}</h2><p className="text-sm text-gray-500">{item.description}</p></div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}