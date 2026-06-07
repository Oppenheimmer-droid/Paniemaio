'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { authService } from '@/services/auth.service'

export default function RegisterPage() {
  const router = useRouter()
  const [formData, setFormData] = useState({
    tenant_name: '',
    tenant_slug: '',
    admin_email: '',
    admin_password: '',
    admin_first_name: '',
    admin_last_name: ''
  })
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      await authService.register(formData as any)
      router.push('/dashboard')
    } catch (err: any) {
      setError(err.response?.data?.detail?.message || 'Error al registrarse')
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    
    // Auto-generate slug from tenant name
    if (name === 'tenant_name') {
      const slug = value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
      setFormData({ 
        ...formData, 
        [name]: value,
        tenant_slug: slug
      })
    } else {
      setFormData({ ...formData, [name]: value })
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h1 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            SaaS Edu
          </h1>
          <p className="mt-2 text-center text-sm text-gray-600">
            Crea tu organización
          </p>
        </div>
        
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}
          
          <div className="space-y-4">
            <div>
              <label htmlFor="tenant_name" className="block text-sm font-medium text-gray-700">
                Nombre de la organización
              </label>
              <input
                id="tenant_name"
                name="tenant_name"
                type="text"
                required
                value={formData.tenant_name}
                onChange={handleChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                placeholder="Mi Academia"
              />
            </div>

            <div>
              <label htmlFor="tenant_slug" className="block text-sm font-medium text-gray-700">
                Slug (URL)
              </label>
              <input
                id="tenant_slug"
                name="tenant_slug"
                type="text"
                required
                value={formData.tenant_slug}
                onChange={(e) => setFormData({ ...formData, tenant_slug: e.target.value })}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                placeholder="mi-academia"
              />
              <p className="mt-1 text-xs text-gray-500">
                URL: saas-edu.com/{formData.tenant_slug || 'tu-org'}
              </p>
            </div>

            <hr className="my-4" />

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="admin_first_name" className="block text-sm font-medium text-gray-700">
                  Nombre
                </label>
                <input
                  id="admin_first_name"
                  name="admin_first_name"
                  type="text"
                  required
                  value={formData.admin_first_name}
                  onChange={handleChange}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                  placeholder="Juan"
                />
              </div>
              <div>
                <label htmlFor="admin_last_name" className="block text-sm font-medium text-gray-700">
                  Apellido
                </label>
                <input
                  id="admin_last_name"
                  name="admin_last_name"
                  type="text"
                  required
                  value={formData.admin_last_name}
                  onChange={handleChange}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                  placeholder="Pérez"
                />
              </div>
            </div>

            <div>
              <label htmlFor="admin_email" className="block text-sm font-medium text-gray-700">
                Email del administrador
              </label>
              <input
                id="admin_email"
                name="admin_email"
                type="email"
                required
                value={formData.admin_email}
                onChange={handleChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                placeholder="admin@miacademia.com"
              />
            </div>

            <div>
              <label htmlFor="admin_password" className="block text-sm font-medium text-gray-700">
                Contraseña
              </label>
              <input
                id="admin_password"
                name="admin_password"
                type="password"
                required
                minLength={8}
                value={formData.admin_password}
                onChange={handleChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                placeholder="••••••••"
              />
              <p className="mt-1 text-xs text-gray-500">
                Mínimo 8 caracteres
              </p>
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Creando organización...' : 'Crear organización'}
            </button>
          </div>

          <div className="text-center">
            <Link href="/login" className="text-primary-600 hover:text-primary-500 text-sm">
              ¿Ya tienes cuenta? Inicia sesión
            </Link>
          </div>
        </form>
      </div>
    </div>
  )
}