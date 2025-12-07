@echo off
echo === Verificacion de puertos en uso ===
echo.

:: Verificar puertos que usa nuestra aplicacion
for %%p in (3010 8010 5442 6389 8090) do (
    echo Verificando puerto %%p:
    netstat -an | findstr ":%%p " >nul
    if %errorlevel% == 0 (
        echo   ❌ Puerto %%p esta en uso
        netstat -an | findstr ":%%p "
    ) else (
        echo   ✅ Puerto %%p esta libre
    )
    echo.
)

echo === Verificacion de contenedores Docker ===
echo.

docker ps -a --format "table {{.Names}}	{{.Status}}	{{.Ports}}" | findstr /i "kobetsu postgres redis adminer frontend backend"
if %errorlevel% == 0 (
    echo Contenedores relacionados encontrados:
) else (
    echo No se encontraron contenedores relacionados
)
docker ps -a --format "table {{.Names}}	{{.Status}}	{{.Ports}}" | findstr /i "kobetsu postgres redis adminer frontend backend"

echo.
echo === Verificacion de redes Docker ===
echo.

docker network ls | findstr /i "kobetsu uns"
if %errorlevel% == 0 (
    echo Redes relacionadas encontradas:
) else (
    echo No se encontraron redes relacionadas
)
docker network ls | findstr /i "kobetsu uns"

echo.
echo === Verificacion de imagenes Docker ===
echo.

docker images | findstr /i "kobetsu uns"
if %errorlevel% == 0 (
    echo Imagenes relacionadas encontradas:
) else (
    echo No se encontraron imagenes relacionadas
)
docker images | findstr /i "kobetsu uns"

echo.
echo === Resumen ===
echo.

:: Contar problemas (simplificado)
set conflicts=0

for %%p in (3010 8010 5442 6389 8090) do (
    netstat -an | findstr ":%%p " >nul
    if !errorlevel! == 0 (
        set /a conflicts+=1
    )
)

if %conflicts% gtr 0 (
    echo ❌ Se encontraron posibles conflictos de puertos
) else (
    echo ✅ No hay conflictos de puertos
)

echo.
echo === Recomendaciones ===
echo.

if %conflicts% gtr 0 (
    echo Se recomienda:
    echo 1. Detener y eliminar contenedores existentes: docker rm -f ^(docker ps -aq --filter name^=uns-kobetsu^)
    echo 2. Eliminar redes existentes: docker network rm ^(docker network ls -q --filter name^=uns-kobetsu^)
    echo 3. O usar diferentes puertos modificando docker-compose.yml
) else (
    echo ✅ El entorno esta limpio para instalar la aplicacion
)

pause