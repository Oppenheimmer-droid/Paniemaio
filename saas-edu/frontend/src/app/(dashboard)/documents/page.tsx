'use client'
import { useState, useEffect, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { documentsService } from '@/services/documents.service'
export default function DocumentsPage() {
  const [documents, setDocuments] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [showModal, setShowModal] = useState(false)
  const [title, setTitle] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const loadDocs = useCallback(async () => {
    try { const data = await documentsService.list({ page_size: 50 }); setDocuments(data.items) }
    catch (e) { console.error(e) }
    finally { setLoading(false) }
  }, [])
  useEffect(() => { loadDocs() }, [loadDocs])
  const onDrop = useCallback((accepted: File[]) => { if (accepted.length > 0) { setFile(accepted[0]); setShowModal(true) } }, [])
  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop, accept: { 'application/pdf': ['.pdf'] }, maxFiles: 1, maxSize: 50 * 1024 * 1024 })
  const handleUpload = async () => {
    if (!file || !title) return
    setUploading(true)
    try { await documentsService.upload({ file, title, difficulty: 3 }); setShowModal(false); setTitle(''); setFile(null); await loadDocs() }
    catch (e) { console.error(e); alert('Error') }
    finally { setUploading(false) }
  }
  const statusColors: Record<string, string> = { pending: 'bg-gray-100 text-gray-700', processing: 'bg-yellow-100 text-yellow-700', completed: 'bg-green-100 text-green-700', failed: 'bg-red-100 text-red-700' }
  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Documentos</h1>
        <button onClick={() => setShowModal(true)} className="px-4 py-2 bg-primary-600 text-white rounded-lg">Subir documento</button>
      </div>
      <div {...getRootProps()} className={`border-2 border-dashed rounded-lg p-8 mb-6 text-center cursor-pointer ${isDragActive ? 'border-primary-500 bg-primary-50' : 'border-gray-300'}`}>
        <input {...getInputProps()} />
        <p className="text-gray-600">{isDragActive ? 'Suelta' : 'Arrastra o haz clic'}</p>
      </div>
      {loading ? <div className="text-center py-12">Cargando...</div> : documents.length === 0 ? <div className="text-center py-12 text-gray-500">No hay documentos</div> : (
        <div className="grid gap-4">{documents.map(doc => (
          <div key={doc.id} className="bg-white border rounded-lg p-4 flex items-center justify-between">
            <div><h3 className="font-medium">{doc.title}</h3><p className="text-sm text-gray-500">{doc.chunk_count} chunks</p></div>
            <span className={`px-3 py-1 rounded-full text-sm ${statusColors[doc.status]}`}>{doc.status}</span>
          </div>
        ))}</div>
      )}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">Subir documento</h2>
            {file && <div className="mb-4 p-3 bg-gray-100 rounded"><p className="text-sm">{file.name}</p></div>}
            <input type="text" value={title} onChange={e => setTitle(e.target.value)} placeholder="Título" className="w-full px-3 py-2 border rounded-lg mb-4" />
            <div className="flex justify-end gap-3">
              <button onClick={() => setShowModal(false)} className="px-4 py-2 text-gray-600">Cancelar</button>
              <button onClick={handleUpload} disabled={!file || !title || uploading} className="px-4 py-2 bg-primary-600 text-white rounded-lg disabled:opacity-50">{uploading ? '...' : 'Subir'}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}