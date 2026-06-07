'use client'
import { useState, useEffect } from 'react'
import { analyticsService } from '@/services/analytics.service'
export default function AnalyticsPage() {
  const [overview, setOverview] = useState<any>(null)
  const [students, setStudents] = useState<any[]>([])
  const [documents, setDocuments] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<'overview' | 'students' | 'documents'>('overview')
  useEffect(() => {
    Promise.all([
      analyticsService.getOverview().then(setOverview),
      analyticsService.getStudentsProgress().then(d => setStudents(d.items)),
      analyticsService.getDocumentsUsage().then(d => setDocuments(d.items))
    ]).catch(console.error).finally(() => setLoading(false))
  }, [])
  if (loading) return <div className="p-6 text-center">Cargando...</div>
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Analíticas</h1>
      <div className="flex gap-4 mb-6 border-b">
        {(['overview', 'students', 'documents'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)} className={`pb-2 px-4 capitalize ${tab === t ? 'border-b-2 border-primary-600 text-primary-600' : 'text-gray-500'}`}>{t}</button>
        ))}
      </div>
      {tab === 'overview' && overview && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white rounded-lg shadow p-6"><p className="text-sm text-gray-500 mb-1">Documentos</p><p className="text-3xl font-bold">{overview.total_documents}</p></div>
          <div className="bg-white rounded-lg shadow p-6"><p className="text-sm text-gray-500 mb-1">Alumnos (7d)</p><p className="text-3xl font-bold">{overview.active_students_7d}</p></div>
          <div className="bg-white rounded-lg shadow p-6"><p className="text-sm text-gray-500 mb-1">Mensajes hoy</p><p className="text-3xl font-bold">{overview.messages_today}</p></div>
          <div className="bg-white rounded-lg shadow p-6"><p className="text-sm text-gray-500 mb-1">Score promedio</p><p className="text-3xl font-bold">{overview.avg_score ? `${overview.avg_score}%` : 'N/A'}</p></div>
        </div>
      )}
      {tab === 'students' && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full"><thead className="bg-gray-50"><tr><th className="px-6 py-3 text-left">Alumno</th><th className="px-6 py-3 text-left">Email</th><th className="px-6 py-3 text-left">Intentos</th><th className="px-6 py-3 text-left">Score</th></tr></thead>
          <tbody className="divide-y">{students.map((s, i) => <tr key={i}><td className="px-6 py-4">{s.user_name}</td><td className="px-6 py-4 text-gray-500">{s.email}</td><td className="px-6 py-4">{s.total_attempts}</td><td className="px-6 py-4">{s.avg_score || 'N/A'}</td></tr>)}</tbody></table>
        </div>
      )}
      {tab === 'documents' && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full"><thead className="bg-gray-50"><tr><th className="px-6 py-3 text-left">Documento</th><th className="px-6 py-3 text-left">Consultas</th><th className="px-6 py-3 text-left">Chunks</th></tr></thead>
          <tbody className="divide-y">{documents.map((d, i) => <tr key={i}><td className="px-6 py-4">{d.title}</td><td className="px-6 py-4">{d.rag_queries}</td><td className="px-6 py-4">{d.chunks}</td></tr>)}</tbody></table>
        </div>
      )}
    </div>
  )
}