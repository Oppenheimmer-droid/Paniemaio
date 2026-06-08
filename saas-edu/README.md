# 🎓 SaaS Educativo White-Label

> Plataforma SaaS educativa donde academias y profesores pueden ofrecer chat con IA y quizzes automáticos basados en sus documentos.

## 📋 Índice

- [Características](#-características)
- [Stack Tecnológico](#-stack-tecnológico)
- [Arquitectura](#-arquitectura)
- [Requisitos Previos](#-requisitos-previos)
- [Instalación Local](#-instalación-local)
- [Despliegue en Railway](#-despliegue-en-railway)
- [API Endpoints](#-api-endpoints)
- [Credenciales Demo](#-credenciales-demo)
- [Desarrollo](#-desarrollo)
- [Costos](#-costos)

---

## ✨ Características

- 🤖 **Chat con IA** — Responde preguntas basándose únicamente en los documentos subidos
- 📝 **Generación automática de quizzes** — Crea evaluaciones desde cualquier documento
- 📊 **Analíticas** — Dashboard con progreso de alumnos y uso de documentos
- 🏢 **Multi-tenant** — Aislamiento total de datos por cliente
- 🔐 **RBAC** — Roles: Admin, Teacher, Student
- 💰 **Costo cero** — Groq API + sentence-transformers locales

---

## 🛠 Stack Tecnológico

```
Backend:      FastAPI 0.115 · Python 3.11 · SQLAlchemy 2.x async
Database:     PostgreSQL 16 · asyncpg
Vectors:      ChromaDB 0.5 (local persistente)
Embeddings:   sentence-transformers · all-MiniLM-L6-v2
LLM:          Groq SDK · llama-3.1-8b-instant
Workers:      Celery 5.4 · Redis broker
Frontend:     Next.js 14 · TypeScript · Tailwind CSS · Zustand
Container:    Docker · docker-compose
CI/CD:        GitHub Actions → Railway
```

---

## 🏗 Arquitectura

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  RAILWAY (Free Tier)                                                        │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐   │
│  │  PostgreSQL     │  │  Redis          │  │  Backend (FastAPI)      │   │
│  │  (managed)      │  │  (managed)      │  │  + Celery Worker         │   │
│  └─────────────────┘  └─────────────────┘  │  + ChromaDB              │   │
│                                              └─────────────────────────┘   │
│  ┌───────────────────────────────────────────────────────────────────┐   │
│  │  Frontend (Next.js)                                              │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  💰 Costo: $0/mes                                                          │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   Groq API       │
                    │   (llama-3.1-8b) │
                    │   💰 $0/mes      │
                    └──────────────────┘
```

---

## 📦 Requisitos Previos

### Software necesario

```bash
# Verificar versiones
node --version    # >= 18.0
python --version  # >= 3.11
docker --version  # >= 24.0
docker-compose --version  # >= 2.20
git --version     # >= 2.40
```

### Cuentas necesarias

- [ ] **GitHub** — Repositorio + GitHub Actions
- [ ] **Railway** — https://railway.app (registro gratuito)
- [ ] **Groq** — https://console.groq.com (API key gratuita)

---

## 🚀 Instalación Local

### 1. Clonar repositorio

```bash
git clone https://github.com/tu-usuario/saas-edu.git
cd saas-edu
```

### 2. Configurar backend

```bash
cd backend
cp .env.example .env

# Editar .env y añadir tu GROQ_API_KEY
# Obtenerla en: https://console.groq.com
```

### 3. Configurar frontend

```bash
cd ../frontend
cp .env.local.example .env.local
```

### 4. Iniciar con Docker Compose

```bash
# Desde la raíz del proyecto
docker-compose up -d

# Ver logs
docker-compose logs -f

# Ver estado de servicios
docker-compose ps
```

### 5. Poblar datos de prueba

```bash
docker exec saas-edu-api python scripts/seed.py
```

### 6. Verificar servicios

```bash
# API
curl http://localhost:8000/health
# Response: {"status":"ok"}

# Frontend
curl http://localhost:3000
# Response: HTML de Next.js

# PostgreSQL
docker exec saas-edu-postgres psql -U postgres -d saas_edu -c "\dt"

# Redis
docker exec saas-edu-redis redis-cli ping
# Response: PONG
```

### 7. Acceder a la aplicación

- **Frontend:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs
- **Adminer (DB):** http://localhost:8080

---

## 🌍 Despliegue en Railway

### 1. Preparar repositorio GitHub

```bash
git init
git add .
git commit -m "Initial commit: SaaS Edu White-Label"
git branch -M main
git remote add origin https://github.com/tu-usuario/saas-edu.git
git push -u origin main
```

### 2. Crear proyecto en Railway

1. Ir a https://railway.app
2. "New Project" → "Deploy from GitHub repo"
3. Seleccionar repositorio `saas-edu`
4. Railway detectará los Dockerfiles automáticamente

### 3. Provisionar servicios managed

```
Railway Dashboard → [+ Add Plugins] → PostgreSQL
Railway Dashboard → [+ Add Plugins] → Redis
```

### 4. Configurar variables de entorno

En Railway, añadir para cada servicio:

**Backend Variables:**
```env
DATABASE_URL=postgresql://xxx:xxx@host:5432/railway
REDIS_URL=redis://xxx:xxx@host:6379
CELERY_BROKER_URL=redis://xxx:xxx@host:6379
CELERY_RESULT_BACKEND=redis://xxx:xxx@host:6379
SECRET_KEY=openssl-rand-hex-64-aqui
GROQ_API_KEY=gsk_your_key
GROQ_MODEL=llama-3.1-8b-instant
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHROMA_PERSIST_DIR=/data/chroma
UPLOAD_DIR=/data/uploads
CORS_ORIGINS=["https://tuapp.up.railway.app"]
ENVIRONMENT=production
DEBUG=false
```

**Frontend Variables:**
```env
NEXT_PUBLIC_API_URL=https://tuapp.up.railway.app/api/v1
```

### 5. Configurar volumen

En Railway → Backend → Settings → Volumes:
- Path: `/data`
- Size: 1GB

### 6. Deploy

Railway desplegará automáticamente desde GitHub. Monitorear desde el dashboard.

---

## 📡 API Endpoints

### Autenticación

```
POST /api/v1/auth/register     # Registro nuevo tenant
POST /api/v1/auth/login        # Login
POST /api/v1/auth/refresh      # Refrescar token
POST /api/v1/auth/logout       # Logout
GET  /api/v1/auth/me           # Usuario actual
```

### Documentos

```
POST   /api/v1/documents              # Subir documento
GET    /api/v1/documents              # Listar documentos
GET    /api/v1/documents/{id}/status  # Estado de procesamiento
DELETE /api/v1/documents/{id}         # Eliminar documento
```

### Chat RAG

```
POST /api/v1/chat/sessions           # Crear sesión
GET  /api/v1/chat/sessions           # Listar sesiones
POST /api/v1/chat/query              # Enviar pregunta
GET  /api/v1/chat/sessions/{id}/messages
```

### Evaluaciones

```
POST   /api/v1/evaluations            # Crear evaluación
GET    /api/v1/evaluations            # Listar evaluaciones
GET    /api/v1/evaluations/{id}      # Detalle (sin respuestas)
PATCH  /api/v1/evaluations/{id}/publish
POST   /api/v1/evaluations/{id}/attempts
POST   /api/v1/evaluations/attempts/{id}/submit
GET    /api/v1/evaluations/attempts/{id}/result
```

### Analíticas

```
GET /api/v1/analytics/overview
GET /api/v1/analytics/students
GET /api/v1/analytics/documents
GET /api/v1/analytics/me
```

---

## 🔑 Credenciales Demo

```
┌────────────────────────────────────────────────────┐
│  Rol           │ Email                │ Password   │
├────────────────┼─────────────────────┼─────────────┤
│  Admin         │ admin@demo.edu       │ Demo1234!   │
│  Teacher       │ teacher@demo.edu     │ Demo1234!   │
│  Student       │ student@demo.edu     │ Demo1234!   │
│  Tenant        │ demo                │             │
└────────────────────────────────────────────────────┘
```

---

## 🛠 Desarrollo

### Estructura de carpetas

```
saas-edu/
├── backend/
│   ├── app/
│   │   ├── api/v1/       # Endpoints
│   │   ├── core/         # Config, DB, Security
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Lógica de negocio
│   │   ├── rag/          # ChromaDB + Embeddings
│   │   └── workers/      # Celery tasks
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── app/          # Páginas
│   │   ├── components/   # UI components
│   │   ├── services/     # API calls
│   │   └── lib/          # Zustand, axios
│   └── tests/
├── docker-compose.yml
└── railway.json
```

### Comandos útiles

```bash
# Desarrollo local
docker-compose up -d              # Iniciar
docker-compose logs -f api        # Logs API
docker-compose exec api bash      # Shell dentro del contenedor
docker-compose restart api         # Reiniciar API

# Reset completo
docker-compose down -v            # Borrar volúmenes
docker-compose up -d              # Reiniciar limpio
docker exec saas-edu-api alembic upgrade head
docker exec saas-edu-api python scripts/seed.py

# Railway
railway login
railway link
railway open
railway logs -s backend

# Tests
cd backend && pytest tests/ -v
cd frontend && npm test
```

### Añadir nueva dependencia

```bash
# Backend
echo "new-package" >> backend/requirements.txt
docker-compose build api

# Frontend
cd frontend && npm install new-package
```

---

## 💰 Costos

### Fase MVP (0-100 usuarios)

| Servicio | Costo | Notas |
|----------|-------|-------|
| Railway | $0 | Free tier |
| Groq API | $0 | 30k tok/min gratis |
| GitHub | $0 | Free tier |
| **Total** | **$0/mes** | |

### Fase Crecimiento (100-500 usuarios)

| Servicio | Costo | Notas |
|----------|-------|-------|
| Railway Starter | $5/mes | +1GB RAM |
| Groq API | $0-20 | Según uso |
| **Total** | **$5-25/mes** | |

### Fase Producción (500+ usuarios)

| Servicio | Costo | Notas |
|----------|-------|-------|
| Railway Pro | $20/mes | 4GB RAM |
| Groq API | $20-50 | Plan de pago |
| **Total** | **$40-70/mes** | |

---

## 🔒 Checklist de Seguridad

- [ ] `SECRET_KEY` generado con `openssl rand -hex 64`
- [ ] `DEBUG=false` en producción
- [ ] `CORS_ORIGINS` solo con dominio de producción
- [ ] Todos los endpoints requieren JWT (excepto `/auth/*`)
- [ ] `tenant_id` en todas las queries SQL
- [ ] `correct_answer` nunca expuesto al frontend en quizzes
- [ ] Archivos subidos en `/data/uploads/{tenant_id}/`
- [ ] `GROQ_API_KEY` en variables de Railway (no en código)

---

## 📚 Recursos

- [FastAPI](https://fastapi.tiangolo.com/)
- [Next.js 14](https://nextjs.org/docs)
- [ChromaDB](https://docs.trychroma.com/)
- [Celery](https://docs.celeryq.dev/)
- [Groq SDK](https://console.groq.com/docs)
- [Railway Docs](https://docs.railway.app/)

---

## 📄 Licencia

MIT License — Usa libremente para proyectos comerciales o personales.

---

**¿Preguntas?** Abre un issue en el repositorio.





