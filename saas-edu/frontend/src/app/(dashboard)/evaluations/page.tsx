'use client'
import { useState, useEffect } from 'react'
import { evaluationsService } from '@/services/evaluations.service'
import { useAuthStore } from '@/lib/store'
export default function EvaluationsPage() {
  const { user } = useAuthStore()
  const [evaluations, setEvaluations] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [quiz, setQuiz] = useState<any>(null)
  const [answers, setAnswers] = useState<Record<string, number>>({})
  const [currentQ, setCurrentQ] = useState(0)
  const [result, setResult] = useState<any>(null)
  const [attemptId, setAttemptId] = useState<string | null>(null)
  useEffect(() => { evaluationsService.list().then(d => setEvaluations(d.items)).catch(console.error).finally(() => setLoading(false)) }, [])
  const startQuiz = async (eval_: any) => {
    const attempt = await evaluationsService.startAttempt(eval_.id)
    setAttemptId(attempt.attempt_id)
    const data = await evaluationsService.get(eval_.id)
    setQuiz(data.questions || [])
    setCurrentQ(0)
    setAnswers({})
    setResult(null)
  }
  const submitQuiz = async () => {
    if (!attemptId) return
    const answersList = Object.entries(answers).map(([qId, idx]) => ({ question_id: qId, answer_text: idx.toString() }))
    const res = await evaluationsService.submitAnswers(attemptId, answersList)
    setResult(res)
  }
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Evaluaciones</h1>
      {loading ? <div className="text-center">Cargando...</div> : evaluations.length === 0 ? <div className="text-center text-gray-500">No hay evaluaciones</div> : (
        <div className="grid gap-4">{evaluations.map(eval_ => (
          <div key={eval_.id} className="bg-white border rounded-lg p-4 flex items-center justify-between">
            <div><h3 className="font-medium">{eval_.title}</h3><p className="text-sm text-gray-500">{eval_.question_count} preguntas</p></div>
            <div className="flex items-center gap-4">
              <span className={`px-3 py-1 rounded-full text-sm ${eval_.is_published ? 'bg-green-100 text-green-700' : 'bg-gray-100'}`}>{eval_.is_published ? 'Publicada' : 'Borrador'}</span>
              {eval_.is_published && <button onClick={() => startQuiz(eval_)} className="px-4 py-2 bg-primary-600 text-white rounded-lg">Iniciar</button>}
            </div>
          </div>
        ))}</div>
      )}
      {quiz && !result && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-6">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl">
            <h2 className="text-xl font-bold mb-4">Pregunta {currentQ + 1} de {quiz.length}</h2>
            <p className="text-lg mb-4">{quiz[currentQ]?.question_text}</p>
            <div className="space-y-2 mb-6">{quiz[currentQ]?.options.map((opt: string, idx: number) => (
              <button key={idx} onClick={() => setAnswers({ ...answers, [quiz[currentQ].id]: idx })} className={`w-full text-left p-3 rounded-lg border ${answers[quiz[currentQ].id] === idx ? 'border-primary-500 bg-primary-50' : 'border-gray-200'}`}>{opt}</button>
            ))}</div>
            <div className="flex justify-between">
              <button onClick={() => setCurrentQ(Math.max(0, currentQ - 1))} disabled={currentQ === 0} className="px-4 py-2 border rounded-lg disabled:opacity-50">Anterior</button>
              {currentQ < quiz.length - 1 ? <button onClick={() => setCurrentQ(currentQ + 1)} className="px-4 py-2 bg-primary-600 text-white rounded-lg">Siguiente</button> : <button onClick={submitQuiz} disabled={Object.keys(answers).length < quiz.length} className="px-4 py-2 bg-green-600 text-white rounded-lg disabled:opacity-50">Finalizar</button>}
            </div>
          </div>
        </div>
      )}
      {result && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md text-center">
            <h2 className="text-2xl font-bold mb-4">Resultado</h2>
            <div className={`text-6xl font-bold mb-4 ${result.passed ? 'text-green-600' : 'text-red-600'}`}>{result.score.toFixed(1)}%</div>
            <p className="text-lg mb-6">{result.passed ? '¡Aprobado!' : 'No aprobado'}</p>
            <button onClick={() => { setQuiz(null); setResult(null) }} className="px-6 py-2 bg-primary-600 text-white rounded-lg">Cerrar</button>
          </div>
        </div>
      )}
    </div>
  )
}