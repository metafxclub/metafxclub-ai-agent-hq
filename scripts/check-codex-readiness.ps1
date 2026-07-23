[CmdletBinding()]
param(
    [switch]$UseCachedRateLimit
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$endpointPath = Join-Path $projectRoot "data\runtime\bridge-endpoint.json"

function Read-ConfirmedEndpoint {
    if (-not (Test-Path -LiteralPath $endpointPath -PathType Leaf)) {
        throw "ยังไม่พบ Local endpoint ที่ผ่าน Health check กรุณาเปิด HQ ก่อน"
    }

    $endpoint = Get-Content -LiteralPath $endpointPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $port = [int]$endpoint.port
    if ([string]$endpoint.host -cne "127.0.0.1" -or $port -lt 1024 -or $port -gt 65535) {
        throw "ปฏิเสธ endpoint ที่ไม่ใช่ 127.0.0.1 หรือใช้ Port นอกช่วงที่อนุญาต"
    }
    return [pscustomobject]@{
        Url = "http://127.0.0.1:$port/"
        HealthUrl = "http://127.0.0.1:$port/api/health"
        Port = $port
    }
}

try {
    $endpoint = Read-ConfirmedEndpoint
    $health = Invoke-RestMethod -Uri $endpoint.HealthUrl -Method Get -TimeoutSec 5
    if (
        $health.ok -ne $true -or
        [string]$health.status -cne "ready" -or
        -not $health.endpoint -or
        [string]$health.endpoint.host -cne "127.0.0.1" -or
        [int]$health.endpoint.port -ne [int]$endpoint.Port
    ) {
        throw "HQ ตอบกลับแต่ Health หรือ Local endpoint ไม่ตรงกับค่าที่ยืนยัน"
    }

    $bridge = Invoke-RestMethod -Uri ("{0}api/bridge/status" -f $endpoint.Url) -Method Get -TimeoutSec 20
    $codexStatus = [string]$bridge.codex.status
    $codexVersion = [string]$bridge.codex.version
    if ($codexStatus -in @("ready", "ready_guarded")) {
        Write-Host "Codex: เชื่อมต่อแล้ว $codexVersion" -ForegroundColor Green
    }
    elseif ($codexStatus -eq "auth_required") {
        Write-Host "Codex: ต้อง Login ด้วยบัญชีของผู้ใช้ Windows คนนี้" -ForegroundColor Yellow
    }
    elseif ($codexStatus -eq "config_error") {
        Write-Host "Codex: Config มีค่าที่ Codex CLI ไม่รองรับ กรุณาแก้ Config แล้วตรวจใหม่" -ForegroundColor Yellow
    }
    else {
        Write-Host "Codex: ยังไม่พร้อม ($codexStatus)" -ForegroundColor Yellow
    }

    $rateSuffix = if ($UseCachedRateLimit) { "" } else { "?refresh=true" }
    $rate = Invoke-RestMethod -Uri ("{0}api/codex/rate-limits{1}" -f $endpoint.Url, $rateSuffix) -Method Get -TimeoutSec 25
    $rateStatus = [string]$rate.status
    if ($rate.ok -eq $true -and $rate.primary) {
        $staleText = if ([bool]$rate.stale) { " • ข้อมูลล่าสุดที่บันทึกไว้" } else { "" }
        $limitText = if ([bool]$rate.limitReached) { " • ถึงขีดจำกัดแล้ว" } else { "" }
        Write-Host ("Rate Limit ของบัญชีเครื่องนี้: เหลือ {0}% • ใช้แล้ว {1}% • รีเซ็ต {2}{3}{4}" -f `
            $rate.primary.remainingPercent, $rate.primary.usedPercent, $rate.primary.resetsAt, $staleText, $limitText) -ForegroundColor Green
        Write-Host "พร้อมใช้งานที่ $($endpoint.Url)" -ForegroundColor Green
        exit 0
    }

    if ($rateStatus -eq "auth_required") {
        Write-Host "Rate Limit: กรุณา Login Codex ด้วยบัญชีของตนเอง แล้วรันการตรวจนี้อีกครั้ง" -ForegroundColor Yellow
        exit 2
    }
    if ($rateStatus -eq "config_error") {
        Write-Host "Rate Limit: ยังอ่านไม่ได้เพราะ Config ของ Codex CLI ไม่รองรับ" -ForegroundColor Yellow
        exit 2
    }
    Write-Host "Rate Limit: ยังตรวจไม่ได้ ($rateStatus) แต่ HQ โหมด Local/Demo ยังเปิดได้" -ForegroundColor Yellow
    exit 2
}
catch {
    Write-Error ([string]$_.Exception.Message)
    exit 1
}
