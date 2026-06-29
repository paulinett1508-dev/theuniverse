# setup-claude-usage.ps1
# Instala o monitoramento de uso do Claude Code na máquina atual.
# Execute UMA VEZ por máquina, a partir da raiz do theuniverse:
#   pwsh -File scripts\setup-claude-usage.ps1
#
# Pré-requisitos: ccusage (npm i -g ccusage), python 3.x, Claude Code

param(
    [string]$VaultPath = (Join-Path (Get-Location) ".vault"),
    [string]$WeeklyLimitTokens = "1904437438",
    [string]$DailyThreshold = "0.10"
)

$ErrorActionPreference = "Stop"
$CLAUDE = "$env:USERPROFILE\.claude"

function Step { param([string]$s) Write-Host "`n=== $s ===" -ForegroundColor Cyan }
function OK   { param([string]$s) Write-Host "  OK  $s" -ForegroundColor Green }
function WARN { param([string]$s) Write-Host "  WARN $s" -ForegroundColor Yellow }

Step "1/5  Estrutura ~/.claude/"
New-Item -ItemType Directory -Force "$CLAUDE\scripts" | Out-Null
New-Item -ItemType Directory -Force "$CLAUDE\state"   | Out-Null
New-Item -ItemType Directory -Force "$CLAUDE\hooks"   | Out-Null
OK "dirs criados"

Step "2/5  weekly-limit.json"
$limitFile = "$CLAUDE\weekly-limit.json"
if (-not (Test-Path $limitFile)) {
    @{
        weeklyTokenLimit    = [long]$WeeklyLimitTokens
        dailyAlertThreshold = [double]$DailyThreshold
        vaultPath           = $VaultPath -replace "\\","/"
        calibratedAt        = (Get-Date -Format "yyyy-MM-dd")
        calibrationNote     = "Calibrar: abrir /usage no claude.ai e ajustar weeklyTokenLimit"
    } | ConvertTo-Json | Set-Content $limitFile -Encoding UTF8
    OK "criado (ajuste weeklyTokenLimit após calibrar via /usage)"
} else {
    WARN "já existe — não sobrescrito"
}

Step "3/5  Script de notificação"
$srcScript  = Join-Path (Split-Path $MyInvocation.MyCommand.Path) "weekly-usage-notify.py"
$destScript = "$CLAUDE\scripts\weekly-usage-notify.py"
Copy-Item $srcScript $destScript -Force
OK "copiado → $destScript"

Step "4/5  Hook do statusline"
$srcHook  = "$CLAUDE\hooks\weekly-usage.ps1"
$origHook = Join-Path $env:USERPROFILE ".claude\hooks\weekly-usage.ps1"
if (-not (Test-Path $srcHook)) {
    if (Test-Path $origHook) {
        Copy-Item $origHook $srcHook -Force
        OK "hook copiado"
    } else {
        WARN "weekly-usage.ps1 não encontrado — copie manualmente de outro setup"
    }
} else {
    OK "hook já existe"
}

Step "5/5  Task Scheduler (05:00 · rep. 2h · 18h/dia)"
$xml = @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers>
    <CalendarTrigger>
      <Repetition>
        <Interval>PT2H</Interval>
        <Duration>PT18H</Duration>
        <StopAtDurationEnd>false</StopAtDurationEnd>
      </Repetition>
      <StartBoundary>$(Get-Date -Format "yyyy-MM-dd")T05:00:00</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByDay><DaysInterval>1</DaysInterval></ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Actions Context="Author">
    <Exec>
      <Command>python</Command>
      <Arguments>"$CLAUDE\scripts\weekly-usage-notify.py"</Arguments>
      <WorkingDirectory>$CLAUDE\scripts</WorkingDirectory>
    </Exec>
  </Actions>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <ExecutionTimeLimit>PT5M</ExecutionTimeLimit>
    <Enabled>true</Enabled>
  </Settings>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
</Task>
"@

$folder = "\Claude\"
try {
    $svc = New-Object -ComObject Schedule.Service
    $svc.Connect()
    try { $svc.GetFolder($folder) | Out-Null }
    catch { $svc.GetFolder("\").CreateFolder("Claude") | Out-Null }
} catch {}

Register-ScheduledTask -TaskName "Claude-WeeklyUsageNotify" -TaskPath "\Claude\" -Xml $xml -Force | Out-Null
OK "task registrada"

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  SETUP CONCLUIDO" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Próximos passos:"
Write-Host "  1. Ajuste weeklyTokenLimit em $limitFile"
Write-Host "     (abra /usage no claude.ai e calibre)"
Write-Host "  2. Confirme que .vault existe em: $VaultPath"
Write-Host "  3. Teste: python `"$CLAUDE\scripts\weekly-usage-notify.py`""
Write-Host ""
