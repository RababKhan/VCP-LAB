<#
  demo_decode.ps1 - Part 2, steps 2, 6, 7 and 8: decoder version, decode, save the reconstructed YUV, check frame count.

  Run after demo_encode.ps1, from the professor_demo folder:
      powershell -ExecutionPolicy Bypass -File .\demo_decode.ps1            (uses the newest demo run)
      powershell -ExecutionPolicy Bypass -File .\demo_decode.ps1 -RunDir <folder>

  Decoder command (same as experiment\run_phase2.py):   vvdecapp -b <in.266> -o <recon.yuv> -t 8
  Timing decodes (3x, no output file), as in the original:  vvdecapp -b <in.266> -t 8
#>
param([string]$RunDir = '', [ValidateSet('Auto', 'Windows', 'Linux')][string]$Engine = 'Auto')

. (Join-Path $PSScriptRoot 'demo_common.ps1')
if (-not $RunDir) { $RunDir = Get-LatestRunDir }
$info = Read-RunInfo $RunDir
Write-Host $info.label -ForegroundColor Magenta
Write-Host "Run folder: $RunDir"
$recon = Join-Path $RunDir ("recon_{0}x{1}_{2}fps_10bit_420.yuv" -f $info.width, $info.height, $info.fps)
$log = Join-Path $RunDir 'decode.log'
$rx = '(\d+) frames decoded @ [\d.]+ fps \(([\d.]+) sec\)'           # same pattern as experiment\run_phase2.py

Show-Step 'Step 2: decoder version'
$v = Invoke-Tool -WinExe $WinDec -LinuxExe $LinuxDec -ArgList @('--version') -Engine $Engine
Write-Host "  $($v.Text.Trim())   [engine: $($v.Engine)]"
$eng = if ($v.Engine -like 'Linux*') { 'Linux' } else { $Engine }

Show-Step 'Step 6+7: decode the bitstream and save the reconstructed YUV file'
$args1 = @('-b', $info.bitstream, '-o', $recon, '-t', '8')
Write-Host "  Command: vvdecapp $($args1 -join ' ')"
$r = Invoke-Tool -WinExe $WinDec -LinuxExe $LinuxDec -ArgList $args1 -Engine $eng
"=== DECODE WITH OUTPUT ($($r.Engine))`r`nCommand: $($r.Exe) $($args1 -join ' ')`r`n$($r.Text)`r`nExit code: $($r.Code)" | Out-File -LiteralPath $log -Encoding utf8
if ($r.Code -ne 0 -or -not (Test-Path $recon)) { Write-Host "  DECODE FAILED (exit $($r.Code)). See $log" -ForegroundColor Red; exit 1 }
$m = [regex]::Matches($r.Text, $rx) | Select-Object -Last 1
Write-Host "  Decoder says: $($m.Value)"

Show-Step 'Step 8: verify the decoded frame count'
$size = (Get-Item $recon).Length
$frameBytes = $info.width * $info.height * 3 / 2 * 2      # 4:2:0 = 1.5 samples per pixel, 10-bit = 2 bytes per sample
$frames = $size / $frameBytes
Write-Host ("  {0} bytes / ({1} x {2} x 1.5 samples x 2 bytes = {3} bytes per frame) = {4} frames" -f $size, $info.width, $info.height, $frameBytes, $frames)
Show-Check "decoded frame count = $($info.frames)" ($frames -eq $info.frames)
$rsha = Get-Sha256 $recon
Write-Host "  Reconstructed YUV SHA-256: $rsha"

Show-Step 'Decoding time: 3 decodes without an output file (median), as in the original experiment'
$times = @()
for ($k = 1; $k -le 3; $k++) {
    $t = Invoke-Tool -WinExe $WinDec -LinuxExe $LinuxDec -ArgList @('-b', $info.bitstream, '-t', '8') -Engine $eng
    "=== DECODE TIMING $k (no output file)`r`n$($t.Text)`r`nExit code: $($t.Code)" | Out-File -LiteralPath $log -Encoding utf8 -Append
    $mm = [regex]::Matches($t.Text, $rx) | Select-Object -Last 1
    if ($mm) { $times += [double]$mm.Groups[2].Value; Write-Host "  decode $k : $($mm.Value)" }
}
$med = ($times | Sort-Object)[[int][math]::Floor($times.Count / 2)]
Write-Host "  Median decode time: $med s"

$info | Add-Member -Force -NotePropertyName decoder_engine -NotePropertyValue $r.Engine
$info | Add-Member -Force -NotePropertyName recon -NotePropertyValue $recon
$info | Add-Member -Force -NotePropertyName recon_frames -NotePropertyValue $frames
$info | Add-Member -Force -NotePropertyName recon_sha256 -NotePropertyValue $rsha
$info | Add-Member -Force -NotePropertyName decode_noout_times_s -NotePropertyValue ($times -join ';')
$info | Add-Member -Force -NotePropertyName decode_noout_median_s -NotePropertyValue $med

if ($info.reference_run) {
    Show-Step "Compare with the ORIGINAL run $($info.reference_run) (results\results_phase2.csv, read-only)"
    $o = Get-OriginalRow $info.reference_run
    Write-Host "  Original: $($o.recon_frames) frames, recon SHA-256 $($o.recon_sha256), decode median $($o.decode_noout_median_s) s"
    Show-Check 'frame count' ($frames -eq [double]$o.recon_frames)
    Show-Check 'reconstructed YUV SHA-256 (bit-exact)' ($rsha -eq $o.recon_sha256)
    $info | Add-Member -Force -NotePropertyName recon_matches_original -NotePropertyValue ($rsha -eq $o.recon_sha256)
}
Save-RunInfo $RunDir $info
Write-Host ''
Write-Host "Saved: $recon, decode.log. Next: demo_psnr.ps1" -ForegroundColor Cyan
