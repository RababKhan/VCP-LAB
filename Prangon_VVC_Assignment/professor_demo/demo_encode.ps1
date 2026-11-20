<#
  demo_encode.ps1 - Part 2, steps 1, 3, 4 and 5: encoder version, encode, bitstream, encoding time.

  Run from the professor_demo folder:
      powershell -ExecutionPolicy Bypass -File .\demo_encode.ps1                (short demo, 32 frames)
      powershell -ExecutionPolicy Bypass -File .\demo_encode.ps1 -Mode Full     (reproduce original run A029)
  (-ExecutionPolicy Bypass applies only to this one command; no system setting is changed.)

  The encoder command is the same one the original runner (experiment\run_phase2.py) used:
      vvencapp -i <input.yuv> -s 416x240 -c yuv420_10 --fps 50 -f <frames> -q <QP> --preset <preset> --qpa 0 -t 8 -o <out.266>
  Output goes to a new folder professor_demo\output\<date_time>_<mode>\ ; nothing else is written.
#>
param([ValidateSet('Short', 'Full')][string]$Mode = 'Short',
      [ValidateSet('Auto', 'Windows', 'Linux')][string]$Engine = 'Auto')

. (Join-Path $PSScriptRoot 'demo_common.ps1')
$c = $Configs[$Mode]
$runDir = Join-Path $DemoOut ((Get-Date -Format 'yyyyMMdd_HHmmss') + "_$($Mode.ToLower())")
New-Item -ItemType Directory -Force -Path $runDir | Out-Null
$inFile = Join-Path $Dataset $c.File
$bs = Join-Path $runDir 'demo.266'
$log = Join-Path $runDir 'encode.log'

Write-Host $c.Label -ForegroundColor Magenta
Write-Host "Output folder: $runDir"

Show-Step 'Step 1: encoder version'
$v = Invoke-Tool -WinExe $WinEnc -LinuxExe $LinuxEnc -ArgList @('--version') -Engine $Engine
Write-Host "  $($v.Text.Trim())   [engine: $($v.Engine)]"

Show-Step "Step 3+4: encode $($c.Sequence), QP $($c.QP), preset $($c.Preset), $($c.Frames) frames -> VVC bitstream"
$argList = @('-i', $inFile, '-s', "$($c.Width)x$($c.Height)", '-c', 'yuv420_10', '--fps', "$($c.Fps)", '-f', "$($c.Frames)",
             '-q', "$($c.QP)", '--preset', $c.Preset, '--qpa', '0', '-t', '8', '-o', $bs)
$engineToUse = if ($v.Engine -like 'Linux*') { 'Linux' } else { $Engine }
Write-Host "  Command: vvencapp $($argList -join ' ')"
$sw = [System.Diagnostics.Stopwatch]::StartNew()
$r = Invoke-Tool -WinExe $WinEnc -LinuxExe $LinuxEnc -ArgList $argList -Engine $engineToUse
$sw.Stop()
"=== ENCODE ($($r.Engine))`r`nCommand: $($r.Exe) $($argList -join ' ')`r`n$($r.Text)`r`nExit code: $($r.Code)`r`nWall time (s): $($sw.Elapsed.TotalSeconds.ToString('0.000'))" |
    Out-File -LiteralPath $log -Encoding utf8
if ($r.Code -ne 0 -or -not (Test-Path $bs)) { Write-Host "  ENCODE FAILED (exit $($r.Code)). See $log" -ForegroundColor Red; exit 1 }

# Values printed by the encoder (same regular expressions as experiment\run_phase2.py)
$total = [regex]::Matches($r.Text, 'Total Time:\s*([\d.]+)') | Select-Object -Last 1
$sum = [regex]::Match($r.Text, 'vvenc \[info\]:\s+(\d+)\s+a\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)')

Show-Step 'Step 5: bitstream size, bitrate and encoding time'
$bytes = (Get-Item $bs).Length
$seconds = $c.Frames / $c.Fps
$kbps = $bytes * 8 / $seconds / 1000
$sha = Get-Sha256 $bs
Write-Host "  Bitstream file      : $bs"
Write-Host "  Bitstream size      : $bytes bytes"
Write-Host ("  Bitrate             : {0} bytes x 8 / ({1} frames / {2} fps = {3} s) / 1000 = {4:N3} kbps" -f $bytes, $c.Frames, $c.Fps, $seconds, $kbps)
Write-Host "  Encoder's own value : $($sum.Groups[2].Value) kbps"
Write-Host "  Encoding time       : $($total.Groups[1].Value) s (encoder 'Total Time')   wall clock: $($sw.Elapsed.TotalSeconds.ToString('0.00')) s"
Write-Host "  Encoder PSNR (dB)   : Y $($sum.Groups[3].Value)   U $($sum.Groups[4].Value)   V $($sum.Groups[5].Value)"
Write-Host "  SHA-256             : $sha"
if ($r.Engine -like 'Linux*') { Write-Host '  Timing note: WSL reads the input from D: through a slower file bridge, so this time is not comparable with the original Windows timings.' -ForegroundColor Yellow }

$info = [ordered]@{ mode = $Mode; label = $c.Label; sequence = $c.Sequence; input = $inFile; width = $c.Width; height = $c.Height
    fps = $c.Fps; frames = $c.Frames; qp = $c.QP; preset = $c.Preset; reference_run = $c.ReferenceRun
    encoder_engine = $r.Engine; encoder_command = "$($r.Exe) $($argList -join ' ')"; encode_total_time_s = [double]$total.Groups[1].Value
    encode_wall_s = [math]::Round($sw.Elapsed.TotalSeconds, 3); bitstream = $bs; bitstream_bytes = $bytes; bitrate_kbps = [math]::Round($kbps, 3)
    enc_bitrate_kbps = [double]$sum.Groups[2].Value; enc_y_psnr = [double]$sum.Groups[3].Value; enc_u_psnr = [double]$sum.Groups[4].Value
    enc_v_psnr = [double]$sum.Groups[5].Value; bitstream_sha256 = $sha; created = (Get-Date).ToString('s') }

if ($c.ReferenceRun) {
    Show-Step "Compare with the ORIGINAL run $($c.ReferenceRun) (results\results_phase2.csv, read-only)"
    $o = Get-OriginalRow $c.ReferenceRun
    Write-Host "  Original: $($o.bitstream_bytes) bytes, $($o.bitrate_kbps) kbps, SHA-256 $($o.bitstream_sha256), encode $($o.encode_time_s) s"
    Show-Check 'bitstream size' ($bytes -eq [long]$o.bitstream_bytes)
    Show-Check 'bitstream SHA-256 (bit-exact reproduction)' ($sha -eq $o.bitstream_sha256)
    Write-Host "  Encoding time is measured again, so it will differ a little from the original $($o.encode_time_s) s."
    $info.original_bitstream_sha256 = $o.bitstream_sha256
    $info.bitstream_matches_original = ($sha -eq $o.bitstream_sha256)
}
Save-RunInfo $runDir $info
Write-Host ''
Write-Host "Saved: $log and run_info.json. Next: demo_decode.ps1" -ForegroundColor Cyan
