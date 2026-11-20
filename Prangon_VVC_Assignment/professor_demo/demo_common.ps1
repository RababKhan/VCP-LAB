# Shared settings and helpers for the professor demo scripts. It is dot-sourced by demo_encode.ps1,
# demo_decode.ps1 and demo_psnr.ps1; do not run it on its own.
# The demo writes only into professor_demo\output. The original experiment files are only read.

$Root    = Split-Path -Parent $PSScriptRoot                  # D:\Korea\Prangon_VVC_Assignment
$DemoOut = Join-Path $PSScriptRoot 'output'
$WinEnc  = Join-Path $Root 'vvenc\bin\release-static\vvencapp.exe'   # the encoder used in the original experiment
$WinDec  = Join-Path $Root 'vvdec\bin\release-static\vvdecapp.exe'   # the decoder used in the original experiment
$Python  = Join-Path $Root '.venv\Scripts\python.exe'
$PsnrPy  = Join-Path $Root 'experiment\psnr_check.py'        # the same PSNR checker the experiment used
$Dataset = Join-Path $Root 'dataset'

# Linux build (WSL2 Ubuntu 24.04, GCC 13.3) of the same VVenC 1.14.0 / VVdeC 3.2.1 source.
# It was shown to produce bit-identical output to the Windows build (slide 9).
$WslDistro = 'Ubuntu-24.04'
$WslUser   = 'vvcuser'
$LinuxEnc  = '/home/vvcuser/vvc_sadab/vvenc/bin/release-static/vvencapp'
$LinuxDec  = '/home/vvcuser/vvc_sadab/vvdec/bin/release-static/vvdecapp'

# The two demo configurations (both BasketballPass 416x240, 10-bit 4:2:0, 50 fps)
$Configs = @{
    Short = @{ Sequence = 'BasketballPass'; File = 'BasketballPass_416_240_50_10_420.yuv'; Width = 416; Height = 240; Fps = 50
               Frames = 32; QP = 29; Preset = 'medium'; ReferenceRun = $null
               Label = 'SHORT DEMO: 32 frames only. This is NOT one of the original 500-frame measurements.' }
    Full  = @{ Sequence = 'BasketballPass'; File = 'BasketballPass_416_240_50_10_420.yuv'; Width = 416; Height = 240; Fps = 50
               Frames = 500; QP = 29; Preset = 'faster'; ReferenceRun = 'A029'
               Label = 'FULL REPRODUCTION of original run A029 (same settings, all 500 frames).' }
}

function ConvertTo-WslPath([string]$p) {
    # D:\Korea\x  ->  /mnt/d/Korea/x
    $full = [System.IO.Path]::GetFullPath($p)
    return '/mnt/' + $full.Substring(0, 1).ToLower() + ($full.Substring(2) -replace '\\', '/')
}

function Get-Sha256([string]$p) { return (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLower() }

function Invoke-Tool {
    # Runs the Windows program; if Windows Application Control (Smart App Control) refuses to start it,
    # runs the Linux build of the same program in WSL instead. Returns engine, exit code and output text.
    param([string]$WinExe, [string]$LinuxExe, [string[]]$ArgList, [string]$Engine = 'Auto')
    if ($Engine -ne 'Linux') {
        try {
            $text = & $WinExe @ArgList 2>&1 | ForEach-Object { "$_" }
            return @{ Engine = 'Windows'; Exe = $WinExe; Code = $LASTEXITCODE; Text = ($text -join "`n") }
        } catch {
            if ($Engine -eq 'Windows') { throw }
            Write-Host "  NOTE: Windows refused to start $(Split-Path -Leaf $WinExe):" -ForegroundColor Yellow
            Write-Host "        $(($_.Exception.Message -split 'At [A-Za-z]:\\')[0].Trim())" -ForegroundColor Yellow
            Write-Host "        Using the Linux build of the same version in WSL instead (bit-exact with Windows, slide 9)." -ForegroundColor Yellow
        }
    }
    $wslArgs = @($ArgList | ForEach-Object { if ($_ -match '^[A-Za-z]:\\') { ConvertTo-WslPath $_ } else { $_ } })
    $text = & wsl.exe -d $WslDistro -u $WslUser -- $LinuxExe @wslArgs 2>&1 | ForEach-Object { "$_" }
    return @{ Engine = 'Linux (WSL2)'; Exe = $LinuxExe; Code = $LASTEXITCODE; Text = ($text -join "`n") }
}

function Get-LatestRunDir {
    $d = Get-ChildItem -Path $DemoOut -Directory -ErrorAction SilentlyContinue | Where-Object { Test-Path (Join-Path $_.FullName 'run_info.json') } |
         Sort-Object Name | Select-Object -Last 1
    if (-not $d) { throw 'No demo run found in professor_demo\output. Run demo_encode.ps1 first.' }
    return $d.FullName
}

function Read-RunInfo([string]$dir) { return Get-Content -LiteralPath (Join-Path $dir 'run_info.json') -Raw | ConvertFrom-Json }

function Save-RunInfo([string]$dir, $info) {
    $info | ConvertTo-Json -Depth 5 | Out-File -LiteralPath (Join-Path $dir 'run_info.json') -Encoding utf8
}

function Get-OriginalRow([string]$runId) {
    # Reads one row of the ORIGINAL results (read-only).
    return Import-Csv -LiteralPath (Join-Path $Root 'results\results_phase2.csv') | Where-Object { $_.run_id -eq $runId } | Select-Object -First 1
}

function Show-Step([string]$t) { Write-Host ''; Write-Host "=== $t" -ForegroundColor Cyan }
function Show-Check([string]$what, [bool]$ok) {
    if ($ok) { Write-Host "  [MATCH] $what" -ForegroundColor Green } else { Write-Host "  [DIFFERENT] $what" -ForegroundColor Red }
}
