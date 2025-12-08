#!/bin/bash

echo "=== Verificación de puertos en uso ==="
echo ""

# Verificar puertos que usa nuestra aplicación
ports=(3010 8010 5442 6389 8090)

for port in "${ports[@]}"; do
    echo "Verificando puerto $port:"
    if netstat -tuln | grep ":$port " > /dev/null; then
        echo "  ❌ Puerto $port está en uso"
        netstat -tuln | grep ":$port "
    else
        echo "  ✅ Puerto $port está libre"
    fi
    echo ""
done

echo "=== Verificación de contenedores Docker ==="
echo ""

# Verificar contenedores que podrían entrar en conflicto
containers=$(docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(kobetsu|postgres|redis|adminer|frontend|backend)")

if [ -n "$containers" ]; then
    echo "Contenedores relacionados encontrados:"
    echo "$containers"
else
    echo "No se encontraron contenedores relacionados"
fi

echo ""
echo "=== Verificación de redes Docker ==="
echo ""

# Verificar redes que podrían entrar en conflicto
networks=$(docker network ls | grep -E "(kobetsu|uns)")

if [ -n "$networks" ]; then
    echo "Redes relacionadas encontradas:"
    echo "$networks"
else
    echo "No se encontraron redes relacionadas"
fi

echo ""
echo "=== Verificación de imágenes Docker ==="
echo ""

# Verificar imágenes que podrían entrar en conflicto
images=$(docker images | grep -E "(kobetsu|uns)")

if [ -n "$images" ]; then
    echo "Imágenes relacionadas encontradas:"
    echo "$images"
else
    echo "No se encontraron imágenes relacionadas"
fi

echo ""
echo "=== Resumen ==="
echo ""

# Contar problemas
conflicts=0

for port in "${ports[@]}"; do
    if netstat -tuln | grep ":$port " > /dev/null; then
        conflicts=$((conflicts + 1))
    fi
done

if [ $conflicts -gt 0 ]; then
    echo "❌ Se encontraron $conflicts posibles conflictos de puertos"
else
    echo "✅ No hay conflictos de puertos"
fi

if [ -n "$containers" ]; then
    echo "⚠️  Existen contenedores relacionados que podrían entrar en conflicto"
else
    echo "✅ No hay contenedores relacionados"
fi

echo ""
echo "=== Recomendaciones ==="
echo ""

if [ $conflicts -gt 0 ] || [ -n "$containers" ]; then
    echo "Se recomienda:"
    echo "1. Detener y eliminar contenedores existentes: docker rm -f \$(docker ps -aq --filter name=uns-kobetsu)"
    echo "2. Eliminar redes existentes: docker network rm \$(docker network ls -q --filter name=uns-kobetsu)"
    echo "3. O usar diferentes puertos modificando docker-compose.yml"
else
    echo "✅ El entorno está limpio para instalar la aplicación"
fi