# Live demo for Prof. Kiho: show VVenC / VVdeC versions, encode 16 frames of BasketballPass (same settings as the
# Phase 3 smoke test: QP 32, preset faster, QPA off, 4 threads), decode it, report size / PSNR, and open the result
# next to the original in YUView. Outputs go to demo\<timestamp>\ only; no existing result is touched.
#
# If Windows blocks a self-built executable (Smart App Control / Code Integrity, seen for vvdecapp.exe on 2026-11-10),
# the same tool from the verified Linux build in WSL2 (same commit, byte-identical output in Phase 5) is used instead,
# and the demo says so. No security setting is changed.
# Usage: powershell -NoExit -ExecutionPolicy Bypass -File scripts\live_demo.ps1 [-Qp 32] [-Preset faster] [-NoViewer]
param([int]$Qp = 32, [string]$Preset = 'faster', [int]$Frames = 16, [switch]$NoViewer)

$Root   = Split-Path -Parent $PSScriptRoot
$WinExe = @{ vvencapp = Join-Path $Root 'src\vvenc\bin\release-static\vvencapp.exe'
             vvdecapp = Join-Path $Root 'src\vvdec\bin\release-static\vvdecapp.exe' }
$LinExe = @{ vvencapp = '/home/vvcuser/vvc_linux/vvenc/bin/release-static/vvencapp'
             vvdecapp = '/home/vvcuser/vvc_linux/vvdec/bin/release-static/vvdecapp' }
$Py     = Join-Path $Root '.venv\Scripts\python.exe'
$YUView = Join-Path $Root 'tools\YUView\YUView.exe'
$In     = Join-Path $Root 'dataset\BasketballPass_416_240_50_10_420.yuv'
$Out    = Join-Path $Root ("demo\" + (Get-Date -Format 'yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Force $Out | Out-Null
$Bs  = Join-Path $Out "BasketballPass_QP${Qp}_${Preset}.266"
$Rec = Join-Path $Out "BasketballPass_QP${Qp}_${Preset}_rec_416x240_50fps_10bit_420.yuv"

function Step($t) { Write-Host "`n=== $t ===" -ForegroundColor Cyan }
function ToWsl($p) { if ($p -match '^([A-Za-z]):\\(.*)$') { "/mnt/$($Matches[1].ToLower())/$($Matches[2] -replace '\\', '/')" } else { $p } }

# Run a tool natively on Windows; if Windows refuses to start it, run the identical Linux build in WSL2.
function Invoke-Tool([string]$Name, [string[]]$ToolArgs) {
    try {
        $o = & $WinExe[$Name] @ToolArgs 2>&1 | ForEach-Object { "$_" }
        return @{ Out = $o; Where = 'Windows (MSVC build)' }
    } catch {
        Write-Host "Windows blocked $Name.exe ($($_.Exception.Message.Split('.')[0])); using the identical Linux build in WSL2." -ForegroundColor Yellow
        $env:WSL_UTF8 = '1'
        $o = wsl.exe -d Ubuntu-24.04 -- $LinExe[$Name] @($ToolArgs | ForEach-Object { ToWsl $_ }) 2>&1 | ForEach-Object { "$_" }
        return @{ Out = $o; Where = 'Linux (GCC build, WSL2)' }
    }
}

Step 'Tool versions'
foreach ($t in 'vvencapp', 'vvdecapp') { $r = Invoke-Tool $t @('--version'); "$($r.Out | Select-Object -First 1)   [$($r.Where)]" }

Step "1. Encode: $Frames frames, QP $Qp, preset $Preset, QPA off, 4 threads"
$encArgs = @('-i', $In, '-s', '416x240', '-c', 'yuv420_10', '--fps', '50', '-f', "$Frames", '-q', "$Qp",
             '--preset', $Preset, '--qpa', '0', '-t', '4', '-v', '4', '-o', $Bs)
Write-Host "vvencapp $($encArgs -join ' ')" -ForegroundColor DarkGray
$sw = [Diagnostics.Stopwatch]::StartNew()
$r = Invoke-Tool 'vvencapp' $encArgs
$sw.Stop()
$r.Out | Where-Object { $_ -match '^POC|Total Time|\s+a\s+[0-9]' }
"encoder ran on: $($r.Where); wall time {0:N3} s" -f $sw.Elapsed.TotalSeconds

Step '2. Decode'
Write-Host "vvdecapp -b $Bs -o $Rec -t 4" -ForegroundColor DarkGray
$r = Invoke-Tool 'vvdecapp' @('-b', $Bs, '-o', $Rec, '-t', '4')
$r.Out | Where-Object { $_ -match 'decoded' }
"decoder ran on: $($r.Where)"
if (-not (Test-Path $Rec)) { Write-Host "Decoding failed; no reconstruction written." -ForegroundColor Red; return }

Step '3. Result'
$bytes = (Get-Item $Bs).Length
"bitstream: {0:N0} bytes  ({1:N1} kbps at 50 fps)" -f $bytes, ($bytes * 8 / ($Frames / 50) / 1000)
"reconstruction: {0:N0} bytes = {1} frames x 299,520" -f (Get-Item $Rec).Length, ((Get-Item $Rec).Length / 299520)
& $Py -c "import sys; sys.path.insert(0, r'$Root\scripts'); import psnr_yuv as p; r, _, _ = p.compute(r'$In', r'$Rec', 416, 240, 10, $Frames); a = r['peak1020']['avg_of_frame_psnr']; print('PSNR (peak 1020): Y %.4f  U %.4f  V %.4f dB' % (a['Y'], a['U'], a['V']))"
"SHA256: $((Get-FileHash $Bs).Hash.ToLower())"
if ($Qp -eq 32 -and $Preset -eq 'faster' -and $Frames -eq 16) {
    Write-Host "Reference (Phase 3 Windows and Phase 5 Linux): 10,069 bytes, SHA256 5037d075...e1bb, Y-PSNR 34.2535 dB" -ForegroundColor Green
}

if ($NoViewer) { "Output folder: $Out"; return }
Step '4. Open original and reconstruction in YUView'
Start-Process $YUView -ArgumentList @("`"$(Join-Path $Root 'visual\yuview\BasketballPass_original_416x240_50fps_10bit_420.yuv')`"", "`"$Rec`"")
"YUView started. Output folder: $Out"
