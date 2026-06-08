'use client'
import { useState, useEffect, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import toast from 'react-hot-toast'
import { documentsService } from '@/services/documents.service'
import { useAuthStore } from '@/lib/store'

function Skeleton({ className }: { className?: string }) {
  return <div className={`animate-pulse bg-gray-200 rounded ${className || ''}`} />
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [showModal, setShowModal] = useState(false)
  const [title, setTitle] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const { user } = useAuthStore()
  const isTeacher = user?.role === 'teacher' || user?.role === 'admin'

  const loadDocs = useCallback(async () => {
    try { 
      const data = await documentsService.list({ page_size: 50 }); 
      setDocuments(data.items) 
    }
    catch (e) { 
      console.error(e)
      toast.error('Error al cargar documentos')
    }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { loadDocs() }, [loadDocs])

  // Polling para documentos en procesamiento
  useEffect(() => {
    const processingDocs = documents.filter(d => 
      d.status === 'pending' || d.status === 'processing'
    )
    if (processingDocs.length === 0) return
    
    const interval = setInterval(() => loadDocs(), 5000)
    return () => clearInterval(interval)
  }, [documents, loadDocs])

  const onDrop = useCallback((accepted: File[]) => { 
    if (accepted.length > 0) { 
      setFile(accepted[0]); 
      setShowModal(true) 
    } 
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ 
    onDrop, 
    accept: { 'application/pdf': ['.pdf'] }, 
    maxFiles: 1, 
    maxSize: 50 * 1024 * 1024 
  })

  const handleUpload = async () => {
    if (!file || !title) return
    setUploading(true)
    try { 
      await documentsService.upload({ file, title, difficulty: 3 }); 
      toast.success('Documento subido correctamente')
      setShowModal(false); 
      setTitle(''); 
      setFile(null); 
      await loadDocs() 
    }
    catch (e) { 
      console.error(e); 
      toast.error('Error al subir el documento')
    }
    finally { setUploading(false) }
  }

  const handleCreateEvaluation = (docId: string) => {
    toast.success('Función en desarrollo')
    // TODO: implementar creación de evaluación
  }

  const statusColors: Record<string, string> = { 
    pending: 'bg-gray-100 text-gray-700', 
    processing: 'bg-yellow-100 text-yellow-700', 
    completed: 'bg-green-100 text-green-700', 
    failed: 'bg-red-100 text-red-700' 
  }

  const statusLabels: Record<string, string> = { 
    pending: 'Pendiente', 
    processing: 'Procesando', 
    completed: 'Completado', 
    failed: 'Fallido' 
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Documentos</h1>
        <button onClick={() => setShowModal(true)} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">Subir documento</button>
      </div>

      {/* Dropzone */}
      <div {...getRootProps()} className={`border-2 border-dashed rounded-lg p-8 mb-6 text-center cursor-pointer transition-colors ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}`}>
        <input {...getInputProps()} />
        <svg className="w-12 h-12 mx-auto text-gray-400 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
        <p className="text-gray-600">{isDragActive ? '¡Suelta el archivo!' : 'Arrastra un PDF o haz clic para seleccionar'}</p>
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
                <Skeleton className="h-6 w-20 rounded-full" />
              </div>
            </div>
          ))}
        </div>
      ) : documents.length === 0 ? (
        /* Empty State */
        <div className="text-center py-16 bg-white rounded-lg border">
          <svg className="w-16 h-16 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="text-lg font-medium text-gray-900">Sin documentos</h3>
          <p className="mt-2 text-gray-500">Sube tu primer PDF para empezar a usar el chat IA</p>
          <button onClick={() => setShowModal(true)} className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
            Subir documento
          </button>
        </div>
      ) : (
        /* Documents List */
        <div className="space-y-3">
          {documents.map(doc => (
            <div key={doc.id} className="bg-white border rounded-lg p-4 flex items-center justify-between">
              <div>
                <h3 className="font-medium text-gray-900">{doc.title}</h3>
                <p className="text-sm text-gray-500">{doc.chunk_count} chunks • {doc.filename}</p>
              </div>
              <div className="flex items-center gap-3">
                {doc.status === 'completed' && isTeacher && (
                  <button 
                    onClick={() => handleCreateEvaluation(doc.id)}
                    className="px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded-lg border border-blue-200"
                  >
                    Generar quiz
                  </button>
                )}
                <span className={`px-3 py-1 rounded-full text-sm ${statusColors[doc.status]}`}>
                  {statusLabels[doc.status]}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Upload Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">Subir documento</h2>
            {file && (
              <div className="mb-4 p-3 bg-gray-100 rounded flex items-center gap-2">
                <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
                <p className="text-sm text-gray-700">{file.name}</p>
              </div>
            )}
            <input 
              type="text" 
              value={title} 
              onChange={e => setTitle(e.target.value)} 
              placeholder="Título del documento" 
              className="w-full px-3 py-2 border rounded-lg mb-4 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            <div className="flex justify-end gap-3">
              <button onClick={() => { setShowModal(false); setFile(null); setTitle('') }} className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg">Cancelar</button>
              <button onClick={handleUpload} disabled={!file || !title || uploading} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed">
                {uploading ? 'Subiendo...' : 'Subir'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}