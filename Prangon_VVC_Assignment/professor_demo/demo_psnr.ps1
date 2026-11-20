<#
  demo_psnr.ps1 - Part 3: independent PSNR check of the demo reconstruction.

  Run after demo_decode.ps1, from the professor_demo folder:
      powershell -ExecutionPolicy Bypass -File .\demo_psnr.ps1           (uses the newest demo run)

  It runs the SAME checker the experiment used (experiment\psnr_check.py, not modified) on
  original YUV vs reconstructed YUV, and compares the result with the PSNR the encoder printed.
  Formula (per plane, per frame):  PSNR = 10 * log10(1020^2 / MSE), then averaged over all frames.
  1020 = 255 x 4 is the peak value used for 10-bit video by VTM/VVenC.
#>
param([string]$RunDir = '')

. (Join-Path $PSScriptRoot 'demo_common.ps1')
if (-not $RunDir) { $RunDir = Get-LatestRunDir }
$info = Read-RunInfo $RunDir
if (-not $info.recon) { Write-Host 'No reconstruction yet. Run demo_decode.ps1 first.' -ForegroundColor Red; exit 1 }
Write-Host $info.label -ForegroundColor Magenta

Show-Step 'Independent PSNR: original YUV vs decoded YUV'
$cmd = @($PsnrPy, $info.input, $info.recon, "$($info.width)", "$($info.height)", "$($info.frames)")
Write-Host "  Command: python experiment\psnr_check.py <original.yuv> <recon.yuv> $($info.width) $($info.height) $($info.frames)"
$out = & $Python @cmd 2>&1 | ForEach-Object { "$_" }
$json = ($out | Select-Object -Last 1) | ConvertFrom-Json
"=== PSNR CHECK`r`n$($out -join "`r`n")" | Out-File -LiteralPath (Join-Path $RunDir 'psnr.log') -Encoding utf8
Write-Host ("  Independent : Y {0}   U {1}   V {2}   ({3} frames checked)" -f $json.Y, $json.U, $json.V, $json.frames_checked)
Write-Host ("  Encoder     : Y {0}   U {1}   V {2}" -f $info.enc_y_psnr, $info.enc_u_psnr, $info.enc_v_psnr)
$diff = [math]::Max([math]::Max([math]::Abs($json.Y - $info.enc_y_psnr), [math]::Abs($json.U - $info.enc_u_psnr)), [math]::Abs($json.V - $info.enc_v_psnr))
Write-Host ("  Largest difference: {0:N4} dB (the experiment flagged a run if this was above 0.01 dB)" -f $diff)
Show-Check 'independent PSNR = encoder PSNR' ($diff -le 0.0001)

if ($info.reference_run) {
    Show-Step "Compare with the ORIGINAL run $($info.reference_run) (results\results_phase2.csv, read-only)"
    $o = Get-OriginalRow $info.reference_run
    Write-Host "  Original check: Y $($o.check_y_psnr)   U $($o.check_u_psnr)   V $($o.check_v_psnr)"
    Show-Check 'Y/U/V PSNR equal to the original run' (([double]$o.check_y_psnr -eq $json.Y) -and ([double]$o.check_u_psnr -eq $json.U) -and ([double]$o.check_v_psnr -eq $json.V))
}
$info | Add-Member -Force -NotePropertyName check_psnr -NotePropertyValue $json
$info | Add-Member -Force -NotePropertyName max_psnr_diff_db -NotePropertyValue ([math]::Round($diff, 4))
Save-RunInfo $RunDir $info
Write-Host ''
Write-Host 'Saved: psnr.log. Next: demo_results.py' -ForegroundColor Cyan
