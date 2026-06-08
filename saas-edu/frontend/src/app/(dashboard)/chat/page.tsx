'use client'
import { useState, useEffect, useRef } from 'react'
import toast from 'react-hot-toast'
import { chatService } from '@/services/chat.service'

function Skeleton({ className }: { className?: string }) {
  return <div className={`animate-pulse bg-gray-200 rounded ${className || ''}`} />
}

export default function ChatPage() {
  const [sessions, setSessions] = useState<any[]>([])
  const [activeSession, setActiveSession] = useState<any>(null)
  const [messages, setMessages] = useState<any[]>([])
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => { 
    chatService.listSessions()
      .then(d => setSessions(d.items))
      .catch(() => toast.error('Error al cargar chats'))
      .finally(() => setLoading(false)) 
  }, [])

  useEffect(() => { 
    if (activeSession) {
      chatService.getMessages(activeSession.id)
        .then(d => setMessages(d.items))
        .catch(() => toast.error('Error al cargar mensajes'))
    }
  }, [activeSession])

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const createSession = async () => { 
    try { 
      const s = await chatService.createSession({ title: `Chat ${new Date().toLocaleDateString()}` }); 
      setSessions([s, ...sessions]); 
      setActiveSession(s) 
      toast.success('Chat creado')
    } catch (e) { 
      console.error(e)
      toast.error('Error al crear chat')
    } 
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!question.trim() || sending) return
    setSending(true)
    try { 
      await chatService.query({ question: question.trim(), session_id: activeSession?.id }); 
      if (activeSession) chatService.getMessages(activeSession.id).then(d => setMessages(d.items)); 
      setQuestion('') 
    }
    catch (e) { 
      console.error(e)
      toast.error('Error al enviar mensaje')
    }
    finally { setSending(false) }
  }

  return (
    <div className="flex h-[calc(100vh-4rem)]">
      {/* Sidebar */}
      <div className="w-64 border-r bg-gray-50 p-4 overflow-y-auto flex flex-col">
        <button onClick={createSession} className="w-full mb-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          + Nuevo chat
        </button>
        
        {loading ? (
          <div className="space-y-2">
            {[1, 2, 3].map(i => <Skeleton key={i} className="h-14 w-full" />)}
          </div>
        ) : sessions.length === 0 ? (
          <div className="text-center py-8 flex-1">
            <svg className="w-12 h-12 mx-auto text-gray-300 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            <p className="text-gray-500 text-sm">No tienes chats aún</p>
            <p className="text-gray-400 text-xs mt-1">Crea un chat y pregunta sobre tus documentos</p>
          </div>
        ) : (
          <div className="space-y-2 flex-1">
            {sessions.map(s => (
              <button 
                key={s.id} 
                onClick={() => setActiveSession(s)} 
                className={`w-full text-left p-3 rounded-lg transition-colors ${activeSession?.id === s.id ? 'bg-blue-100 text-blue-900' : 'hover:bg-gray-200'}`}
              >
                <p className="font-medium text-sm truncate">{s.title}</p>
                <p className="text-xs text-gray-500">{s.message_count} msgs</p>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col">
        {activeSession ? (
          <>
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.length === 0 ? (
                <div className="text-center py-12">
                  <svg className="w-16 h-16 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                  <p className="text-gray-500">Pregunta sobre tus documentos</p>
                  <p className="text-gray-400 text-sm mt-1">El chat IA responderá basado en los documentos procesados</p>
                </div>
              ) : messages.map(msg => (
                <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-2xl p-4 rounded-lg ${msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-100'}`}>
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                    {msg.citations?.length > 0 && (
                      <div className="mt-2 text-xs opacity-75">
                        <span className="font-medium">Fuentes: </span>
                        {msg.citations.map((c: any, i: number) => <span key={i} className="mr-1">{c.source} </span>)}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
            <form onSubmit={handleSubmit} className="p-4 border-t bg-white">
              <div className="flex gap-2 max-w-3xl mx-auto">
                <input 
                  type="text" 
                  value={question} 
                  onChange={e => setQuestion(e.target.value)} 
                  placeholder="Escribe tu pregunta..." 
                  className="flex-1 px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  disabled={sending} 
                />
                <button 
                  type="submit" 
                  disabled={sending || !question.trim()} 
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {sending ? '...' : 'Enviar'}
                </button>
              </div>
            </form>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-500 flex-col">
            <svg className="w-20 h-20 text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            <p className="text-lg">Selecciona o crea un chat</p>
          </div>
        )}
      </div>
    </div>
  )
}