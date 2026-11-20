<#
  demo_yuview.ps1 - Part 5: open BasketballDrive (original + QP 24/29/34/39, medium preset) in YUView.

  Run from the professor_demo folder:
      powershell -ExecutionPolicy Bypass -File .\demo_yuview.ps1
      powershell -ExecutionPolicy Bypass -File .\demo_yuview.ps1 -VerifyHashes   (first checks the 4 decoded files, about 1 minute)

  The files in visual\yuview are hard links (same data, YUView-friendly names) to the original sequence and to the
  decoded medium-preset files. YUView reads width, height, frame rate, bit depth and 4:2:0 from the file names.
  YUView cannot be controlled by a script, so the frame number and zoom are set by hand (see DEMO_SCRIPT.md, step 7).
#>
param([switch]$VerifyHashes)

$Root = Split-Path -Parent $PSScriptRoot
$YUView = Join-Path $Root 'tools\YUView\YUView.exe'
$dir = Join-Path $Root 'visual\yuview'
$names = @('original', 'QP24_medium', 'QP29_medium', 'QP34_medium', 'QP39_medium')
$files = $names | ForEach-Object { Join-Path $dir "BasketballDrive_$($_)_1920x1080_50fps_10bit_420.yuv" }
$sel = (Get-Content (Join-Path $Root 'visual\v2\selection.json') -Raw | ConvertFrom-Json).sequences.BasketballDrive.typical

Write-Host '=== Files that will be opened (in this order)' -ForegroundColor Cyan
foreach ($f in $files) {
    if (-not (Test-Path -LiteralPath $f)) { Write-Host "  MISSING: $f" -ForegroundColor Red; exit 1 }
    Write-Host ("  {0}  ({1:N0} MB)" -f (Split-Path -Leaf $f), ((Get-Item -LiteralPath $f).Length / 1MB))
}

if ($VerifyHashes) {
    Write-Host '=== Checking that the decoded files are the ones recorded in results\results_phase2.csv' -ForegroundColor Cyan
    $rows = Import-Csv (Join-Path $Root 'results\results_phase2.csv') | Where-Object { $_.sequence -eq 'BasketballDrive' -and $_.preset -eq 'medium' -and $_.kind -eq 'new' }
    foreach ($q in 24, 29, 34, 39) {
        $r = $rows | Where-Object { [int]$_.qp -eq $q } | Select-Object -First 1
        $h = (Get-FileHash -LiteralPath $files[[array]::IndexOf(@(24, 29, 34, 39), $q) + 1] -Algorithm SHA256).Hash.ToLower()
        $ok = $h -eq $r.recon_sha256
        Write-Host ("  QP {0}: run {1}  {2}" -f $q, $r.run_id, $(if ($ok) { '[MATCH] decoded file SHA-256 = recorded recon_sha256' } else { '[DIFFERENT]' })) -ForegroundColor $(if ($ok) { 'Green' } else { 'Red' })
    }
}

Write-Host ''
Write-Host '=== What to show' -ForegroundColor Cyan
Write-Host "  Frame      : $($sel.frame_0based)   (counted from 0 - the first frame is frame 0)"
Write-Host ("  Crop area  : x = {0}, y = {1}, width {2}, height {3} pixels  (the moving player's arm and the chairs behind him)" -f $sel.crop_xywh[0], $sel.crop_xywh[1], $sel.crop_xywh[2], $sel.crop_xywh[3])
Write-Host '  Why frame 98: a fixed rule chosen before looking - the frame whose QP-39 Y-PSNR is the median of all 500 frames.'
Write-Host ''
Write-Host '  If YUView asks "An update for YUView is available...", click Cancel (do not update).'
Write-Host '  If YUView asks "Restore Playlist", click No.'
Write-Host '  If Width/Height show 0: type Width 1920, Height 1080, YUV Format "YUV 4:2:0 10-bit LE", Framerate 50 (Raw File Properties panel, right).'
Write-Host '  When quitting, YUView asks "You have not saved the current playlist" -> click Close.'

try {
    Start-Process -FilePath $YUView -ArgumentList (($files | ForEach-Object { '"' + $_ + '"' }) -join ' ') -ErrorAction Stop | Out-Null
    Write-Host '  YUView started with the 5 files in its playlist.' -ForegroundColor Green
} catch {
    Write-Host "  YUView could not be started: $($_.Exception.Message)" -ForegroundColor Red
    $strip = Join-Path $Root "visual\v2\$($sel.strip)"
    Write-Host "  Fallback: opening the script-rendered comparison image instead (NOT a YUView view): $strip" -ForegroundColor Yellow
    Start-Process -FilePath $strip
}
