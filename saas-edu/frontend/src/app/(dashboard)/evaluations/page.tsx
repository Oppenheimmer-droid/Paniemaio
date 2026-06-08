'use client'
import { useState, useEffect } from 'react'
import toast from 'react-hot-toast'
import { evaluationsService } from '@/services/evaluations.service'
import { useAuthStore } from '@/lib/store'

function Skeleton({ className }: { className?: string }) {
  return <div className={`animate-pulse bg-gray-200 rounded ${className || ''}`} />
}

export default function EvaluationsPage() {
  const { user } = useAuthStore()
  const [evaluations, setEvaluations] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [quiz, setQuiz] = useState<any>(null)
  const [answers, setAnswers] = useState<Record<string, number>>({})
  const [currentQ, setCurrentQ] = useState(0)
  const [result, setResult] = useState<any>(null)
  const [attemptId, setAttemptId] = useState<string | null>(null)

  const isTeacher = user?.role === 'teacher' || user?.role === 'admin'

  useEffect(() => { 
    evaluationsService.list()
      .then(d => setEvaluations(d.items))
      .catch(() => toast.error('Error al cargar evaluaciones'))
      .finally(() => setLoading(false)) 
  }, [])

  const startQuiz = async (eval_: any) => {
    try {
      const attempt = await evaluationsService.startAttempt(eval_.id)
      setAttemptId(attempt.attempt_id)
      const data = await evaluationsService.get(eval_.id)
      setQuiz(data.questions || [])
      setCurrentQ(0)
      setAnswers({})
      setResult(null)
    } catch (e) {
      toast.error('Error al iniciar evaluación')
    }
  }

  const handlePublish = async (evalId: string) => {
    try {
      await evaluationsService.publish(evalId)
      toast.success('Evaluación publicada')
      // Recargar lista
      const data = await evaluationsService.list()
      setEvaluations(data.items)
    } catch (e) {
      toast.error('Error al publicar evaluación')
    }
  }

  const submitQuiz = async () => {
    if (!attemptId) return
    try {
      const answersList = Object.entries(answers).map(([qId, idx]) => ({ question_id: qId, answer_text: idx.toString() }))
      const res = await evaluationsService.submitAnswers(attemptId, answersList)
      setResult(res)
    } catch (e) {
      toast.error('Error al enviar respuestas')
    }
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Evaluaciones</h1>
        {isTeacher && (
          <button onClick={() => toast.success('Ve a documentos para crear una evaluación')} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
            + Nueva evaluación
          </button>
        )}
      </div>

      {/* Loading Skeletons */}
      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="bg-white border rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="space-y-2">
                  <Skeleton className="h-5 w-48" />
                  <Skeleton className="h-4 w-24" />
                </div>
                <div className="flex gap-2">
                  <Skeleton className="h-6 w-20 rounded-full" />
                  <Skeleton className="h-8 w-16" />
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : evaluations.length === 0 ? (
        /* Empty State */
        <div className="text-center py-16 bg-white rounded-lg border">
          <svg className="w-16 h-16 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
          </svg>
          <h3 className="text-lg font-medium text-gray-900">No hay evaluaciones</h3>
          {isTeacher ? (
            <p className="mt-2 text-gray-500">Ve a un documento completado y genera una evaluación automática</p>
          ) : (
            <p className="mt-2 text-gray-500">Tu profesor aún no ha publicado evaluaciones</p>
          )}
        </div>
      ) : (
        /* Evaluations List */
        <div className="space-y-3">
          {evaluations.map(eval_ => (
            <div key={eval_.id} className="bg-white border rounded-lg p-4 flex items-center justify-between">
              <div>
                <h3 className="font-medium text-gray-900">{eval_.title}</h3>
                <p className="text-sm text-gray-500">{eval_.question_count} preguntas • {eval_.avg_score ? `Promedio: ${eval_.avg_score.toFixed(0)}%` : 'Sin resultados'}</p>
              </div>
              <div className="flex items-center gap-3">
                {!eval_.is_published && isTeacher && (
                  <button 
                    onClick={() => handlePublish(eval_.id)}
                    className="px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded-lg border border-blue-200"
                  >
                    Publicar
                  </button>
                )}
                <span className={`px-3 py-1 rounded-full text-sm ${eval_.is_published ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'}`}>
                  {eval_.is_published ? 'Publicada' : 'Borrador'}
                </span>
                {eval_.is_published && (
                  <button onClick={() => startQuiz(eval_)} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                    Iniciar
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Quiz Modal */}
      {quiz && !result && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-6">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-xl font-bold">Pregunta {currentQ + 1} de {quiz.length}</h2>
              <div className="text-sm text-gray-500">Progreso: {Object.keys(answers).length}/{quiz.length}</div>
            </div>
            
            <p className="text-lg mb-4">{quiz[currentQ]?.question_text}</p>
            
            <div className="space-y-2 mb-6">
              {quiz[currentQ]?.options.map((opt: string, idx: number) => (
                <button 
                  key={idx} 
                  onClick={() => setAnswers({ ...answers, [quiz[currentQ].id]: idx })} 
                  className={`w-full text-left p-4 rounded-lg border transition-colors ${answers[quiz[currentQ].id] === idx ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'}`}
                >
                  <span className="font-medium mr-2">{String.fromCharCode(65 + idx)}.</span> {opt}
                </button>
              ))}
            </div>
            
            <div className="flex justify-between">
              <button 
                onClick={() => setCurrentQ(Math.max(0, currentQ - 1))} 
                disabled={currentQ === 0} 
                className="px-4 py-2 border rounded-lg hover:bg-gray-50 disabled:opacity-50"
              >
                ← Anterior
              </button>
              {currentQ < quiz.length - 1 ? (
                <button 
                  onClick={() => setCurrentQ(currentQ + 1)} 
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Siguiente →
                </button>
              ) : (
                <button 
                  onClick={submitQuiz} 
                  disabled={Object.keys(answers).length < quiz.length} 
                  className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                >
                  Finalizar
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Result Modal */}
      {result && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-8 w-full max-w-md text-center">
            <h2 className="text-2xl font-bold mb-4">Resultado</h2>
            <div className={`text-6xl font-bold mb-4 ${result.passed ? 'text-green-600' : 'text-red-600'}`}>
              {result.score.toFixed(1)}%
            </div>
            <p className="text-lg mb-6">{result.passed ? '🎉 ¡Aprobado!' : 'No aprobado'}</p>
            <button onClick={() => { setQuiz(null); setResult(null) }} className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
              Cerrar
            </button>
          </div>
        </div>
      )}
    </div>
  )
}