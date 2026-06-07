'use client'
import { useState, useEffect, useRef } from 'react'
import { chatService } from '@/services/chat.service'
export default function ChatPage() {
  const [sessions, setSessions] = useState<any[]>([])
  const [activeSession, setActiveSession] = useState<any>(null)
  const [messages, setMessages] = useState<any[]>([])
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  useEffect(() => { chatService.listSessions().then(d => setSessions(d.items)).catch(console.error).finally(() => setLoading(false)) }, [])
  useEffect(() => { if (activeSession) chatService.getMessages(activeSession.id).then(d => setMessages(d.items)).catch(console.error) }, [activeSession])
  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])
  const createSession = async () => { try { const s = await chatService.createSession({ title: `Chat ${new Date().toLocaleDateString()}` }); setSessions([s, ...sessions]); setActiveSession(s) } catch (e) { console.error(e) } }
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!question.trim() || sending) return
    setSending(true)
    try { await chatService.query({ question: question.trim(), session_id: activeSession?.id }); if (activeSession) chatService.getMessages(activeSession.id).then(d => setMessages(d.items)); setQuestion('') }
    catch (e) { console.error(e) }
    finally { setSending(false) }
  }
  return (
    <div className="flex h-[calc(100vh-4rem)]">
      <div className="w-64 border-r bg-gray-50 p-4 overflow-y-auto">
        <button onClick={createSession} className="w-full mb-4 px-4 py-2 bg-primary-600 text-white rounded-lg">Nuevo chat</button>
        {loading ? <div className="text-center py-8">...</div> : sessions.length === 0 ? <div className="text-center">No hay chats</div> : (
          <div className="space-y-2">{sessions.map(s => (
            <button key={s.id} onClick={() => setActiveSession(s)} className={`w-full text-left p-3 rounded-lg ${activeSession?.id === s.id ? 'bg-primary-100' : 'hover:bg-gray-200'}`}>
              <p className="font-medium text-sm truncate">{s.title}</p>
            </button>
          ))}</div>
        )}
      </div>
      <div className="flex-1 flex flex-col">
        {activeSession ? (
          <>
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.length === 0 ? <div className="text-center py-12 text-gray-500">Pregunta sobre tus documentos</div> : messages.map(msg => (
                <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-2xl p-4 rounded-lg ${msg.role === 'user' ? 'bg-primary-600 text-white' : 'bg-gray-100'}`}>
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                    {msg.citations?.length > 0 && <div className="mt-2 text-xs opacity-75">Fuentes: {msg.citations.map((c: any, i: number) => <span key={i}>{c.source} </span>)}</div>}
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
            <form onSubmit={handleSubmit} className="p-4 border-t">
              <div className="flex gap-2">
                <input type="text" value={question} onChange={e => setQuestion(e.target.value)} placeholder="Escribe..." className="flex-1 px-4 py-2 border rounded-lg" disabled={sending} />
                <button type="submit" disabled={sending || !question.trim()} className="px-6 py-2 bg-primary-600 text-white rounded-lg disabled:opacity-50">{sending ? '...' : 'Enviar'}</button>
              </div>
            </form>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-500">Selecciona o crea un chat</div>
        )}
      </div>
    </div>
  )
}