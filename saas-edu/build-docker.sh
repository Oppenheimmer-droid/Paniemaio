#!/bin/bash
# ===========================================
# Build Script - SaaS Edu Single Image
# Construye una imagen Docker con todo incluido
# ===========================================

set -e

IMAGE_NAME="saas-edu"
IMAGE_TAG="${1:-latest}"
FULL_IMAGE="${IMAGE_NAME}:${IMAGE_TAG}"

echo "=========================================="
echo "SaaS Edu - Docker Build Script"
echo "=========================================="
echo "Image: ${FULL_IMAGE}"
echo ""

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ===========================================
# Step 1: Verificar Docker
# ===========================================
echo -e "${YELLOW}[1/4]${NC} Verificando Docker..."
if ! command -v docker &> /dev/null; then
    echo "Error: Docker no está instalado"
    exit 1
fi
echo -e "${GREEN}✓${NC} Docker encontrado: $(docker --version)"

# ===========================================
# Step 2: Build de la imagen
# ===========================================
echo ""
echo -e "${YELLOW}[2/4]${NC} Construyendo imagen Docker..."
echo "Esto puede tomar varios minutos..."

docker build \
    --platform linux/amd64,linux/arm64 \
    -f Dockerfile.multiarch \
    -t ${FULL_IMAGE} \
    --progress=plain \
    .

# ===========================================
# Step 3: Verificar imagen
# ===========================================
echo ""
echo -e "${YELLOW}[3/4]${NC} Verificando imagen..."
IMAGE_SIZE=$(docker images ${FULL_IMAGE} --format "{{.Size}}")
echo -e "${GREEN}✓${NC} Imagen creada: ${FULL_IMAGE}"
echo -e "${GREEN}✓${NC} Tamaño: ${IMAGE_SIZE}"

# ===========================================
# Step 4: Instrucciones
# ===========================================
echo ""
echo "=========================================="
echo -e "${GREEN}¡Build completado!${NC}"
echo "=========================================="
echo ""
echo "Para ejecutar:"
echo ""
echo "  # Opción 1: Solo la imagen (necesitas PostgreSQL, Redis, ChromaDB externos)"
echo "  docker run -d -p 8000:8000 \ "
echo "    -e DATABASE_URL='postgresql://...' \ "
echo "    -e REDIS_URL='redis://...' \ "
echo "    -e GROQ_API_KEY='tu-api-key' \ "
echo "    ${FULL_IMAGE}"
echo ""
echo "  # Opción 2: docker-compose (con todos los servicios)"
echo "  docker-compose -f docker-compose.single.yml up -d"
echo ""
echo "  # Opción 3: Push a registry"
echo "  docker tag ${FULL_IMAGE} tu-registry/${FULL_IMAGE}"
echo "  docker push tu-registry/${FULL_IMAGE}"
echo ""
echo "=========================================="
echo ""