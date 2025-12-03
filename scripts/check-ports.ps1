# ============================================
# UNS-Kobetsu - Port Availability Checker
# ============================================
# Usage: .\scripts\check-ports.ps1
# ============================================

$ports = @{
    "KOBETSU_FRONTEND_PORT" = 3010
    "KOBETSU_BACKEND_PORT" = 8010
    "KOBETSU_DB_PORT" = 5442
    "KOBETSU_REDIS_PORT" = 6389
    "KOBETSU_ADMINER_PORT" = 8090
}

Write-Host ""
Write-Host "=== UNS-Kobetsu Port Check ===" -ForegroundColor Cyan
Write-Host ""

$conflicts = @()

foreach ($name in $ports.Keys) {
    $port = $ports[$name]
    $inUse = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue

    if ($inUse) {
        Write-Host "[X] $name=$port - EN USO" -ForegroundColor Red

        # Find alternative port
        for ($alt = $port + 1; $alt -lt $port + 100; $alt++) {
            $altInUse = Get-NetTCPConnection -LocalPort $alt -ErrorAction SilentlyContinue
            if (-not $altInUse) {
                Write-Host "    Sugerencia: $name=$alt" -ForegroundColor Yellow
                $conflicts += "$name=$alt"
                break
            }
        }
    } else {
        Write-Host "[OK] $name=$port - LIBRE" -ForegroundColor Green
    }
}

Write-Host ""

if ($conflicts.Count -gt 0) {
    Write-Host "=== Accion Requerida ===" -ForegroundColor Yellow
    Write-Host "Edita .env con estos valores:" -ForegroundColor Yellow
    Write-Host ""
    foreach ($c in $conflicts) {
        Write-Host "  $c" -ForegroundColor White
    }
    Write-Host ""
    Write-Host "IMPORTANTE: Si cambias KOBETSU_BACKEND_PORT, tambien actualiza:" -ForegroundColor Magenta
    Write-Host "  NEXT_PUBLIC_API_URL=http://localhost:<nuevo_puerto>/api/v1" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "Todos los puertos estan libres. Puedes iniciar con:" -ForegroundColor Green
    Write-Host "  docker compose up -d" -ForegroundColor White
    Write-Host ""
}
