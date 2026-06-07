# 🐳 Docker - SaaS Edu

## Opción 1: Imagen única (Todo en uno)

### Build
```bash
# Opción rápida
docker build -f Dockerfile.multiarch -t saas-edu:latest .

# Con script helper
chmod +x build-docker.sh
./build-docker.sh
```

### Run (requiere PostgreSQL, Redis, ChromaDB externos)
```bash
docker run -d -p 8000:8000 \
  -e DATABASE_URL='postgresql://user:pass@host:5432/db' \
  -e REDIS_URL='redis://host:6379/0' \
  -e CHROMA_HOST='chroma-host' \
  -e CHROMA_PORT='8000' \
  -e GROQ_API_KEY='tu-api-key' \
  -e SECRET_KEY='tu-secret' \
  saas-edu:latest
```

## Opción 2: docker-compose (Completo con todos los servicios)

```bash
# Build + Run todo junto
docker-compose -f docker-compose.single.yml up --build -d

# Ver logs
docker-compose -f docker-compose.single.yml logs -f

# Parar
docker-compose -f docker-compose.single.yml down
```

## Estructura del Dockerfile.multiarch

```
Stage 1: Backend (Python 3.11)
├── Instala dependencies (FastAPI, SQLAlchemy, etc.)
└── Copia código backend

Stage 2: Frontend (Node 20)
├── npm ci
├── npm run build (Next.js)
└── Produce .next/

Stage 3: Runtime
├── Python 3.11 slim
├── Copia backend + frontend
├── Scripts de entrada
└── Health check
```

## Puertos

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| API | 8000/8001 | FastAPI backend |
| Frontend | 3000 | Next.js |
| PostgreSQL | 5432 | Database |
| Redis | 6379 | Cache |
| ChromaDB | 8000 | Vector DB |

## Variables de Entorno

### Requeridas
- `DATABASE_URL` - PostgreSQL connection string
- `GROQ_API_KEY` - API key de Groq

### Opcionales con defaults
- `REDIS_URL` = `redis://localhost:6379/0`
- `CHROMA_HOST` = `localhost`
- `CHROMA_PORT` = `8000`
- `SECRET_KEY` = `change-me-in-production`

## Push a Registry

```bash
# Tag
docker tag saas-edu:latest your-registry.com/saas-edu:latest

# Push
docker push your-registry.com/saas-edu:latest

# Pull en producción
docker pull your-registry.com/saas-edu:latest
```

## Docker Compose Services

1. **postgres** - PostgreSQL 16 Alpine
2. **redis** - Redis 7 Alpine  
3. **chromadb** - ChromaDB latest
4. **api** - FastAPI (Dockerfile.multiarch)
5. **frontend** - Next.js 14

## Health Checks

Todos los servicios tienen health checks configurados:
- PostgreSQL: `pg_isready`
- Redis: `redis-cli ping`
- ChromaDB: `/api/v1/heartbeat`
- API: `/health`