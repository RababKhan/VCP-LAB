# VVC experiment runner (Windows) for Sadab Khan Prangon.
# 2 sequences x QP {24,29,34,39} x preset {fast, medium} = 16 encodes, plus 2 repeated encodes for timing noise.
# Every encode is decoded 3 times (median decode time is kept) and checked with psnr_check.py.
# Output: results\results_raw.csv, results\environment.txt, logs\runs\*.log, out\*.266, out\*_rec_*.yuv
#
# Usage (from the workspace folder):
#   powershell -ExecutionPolicy Bypass -File experiment\run_experiment.ps1 -Root D:\vvc_sadab
#   add -DryRun to only print the planned runs.
param(
    [string]$Root     = 'D:\vvc_sadab',
    [int]   $Threads  = 8,
    [int]   $DecodeRepeats = 3,
    [int]   $Seed     = 2026,
    [switch]$DryRun
)
$ErrorActionPreference = 'Continue'   # native tools write to stderr; real problems use throw
$Vvenc  = Join-Path $Root 'vvenc\bin\release-static\vvencapp.exe'
$Vvdec  = Join-Path $Root 'vvdec\bin\release-static\vvdecapp.exe'
$Psnr   = Join-Path $Root 'experiment\psnr_check.py'
$Data   = Join-Path $Root 'dataset'
$OutDir = Join-Path $Root 'out'
$LogDir = Join-Path $Root 'logs\runs'
$ResDir = Join-Path $Root 'results'
$Csv    = Join-Path $ResDir 'results_raw.csv'

# ---- the experiment design -------------------------------------------------------------------
$Sequences = @(
    @{ Name = 'BlowingBubbles'; File = 'BlowingBubbles_416_240_50_10_420.yuv'; W = 416; H = 240; Fps = 50; Frames = 500 },
    @{ Name = 'BQMall';         File = 'BQMall_832_480_60_10_420.yuv';         W = 832; H = 480; Fps = 60; Frames = 600 }
)
$QPs     = 24, 29, 34, 39
$Presets = 'fast', 'medium'
$Repeats = @(@{ Seq = 'BlowingBubbles'; Qp = 34; Preset = 'fast' }, @{ Seq = 'BlowingBubbles'; Qp = 34; Preset = 'medium' })

$runs = foreach ($s in $Sequences) { foreach ($q in $QPs) { foreach ($p in $Presets) { [pscustomobject]@{ Seq = $s; Qp = $q; Preset = $p; RepeatOf = '' } } } }
$runs = Get-Random -InputObject $runs -Count $runs.Count -SetSeed $Seed         # shuffled, but the same order every time
$i = 0; $runs | ForEach-Object { $i++; $_ | Add-Member RunId ('R{0:D2}' -f $i) }
foreach ($r in $Repeats) {                                              # repeats go at the end
    $orig = $runs | Where-Object { $_.Seq.Name -eq $r.Seq -and $_.Qp -eq $r.Qp -and $_.Preset -eq $r.Preset }
    $i++; $runs += [pscustomobject]@{ Seq = $orig.Seq; Qp = $r.Qp; Preset = $r.Preset; RepeatOf = $orig.RunId; RunId = ('R{0:D2}' -f $i) }
}

"Planned runs: $($runs.Count)"
$runs | ForEach-Object { "  {0}  {1,-15} QP {2}  {3,-6} {4}" -f $_.RunId, $_.Seq.Name, $_.Qp, $_.Preset, $(if ($_.RepeatOf) { "(repeat of $($_.RepeatOf))" }) }
if ($DryRun) { return }

# ---- checks before starting --------------------------------------------------------------------
foreach ($f in $Vvenc, $Vvdec, $Psnr) { if (-not (Test-Path $f)) { throw "Missing: $f" } }
foreach ($s in $Sequences) { if (-not (Test-Path (Join-Path $Data $s.File))) { throw "Missing input: $(Join-Path $Data $s.File)" } }
New-Item -ItemType Directory -Force $OutDir, $LogDir, $ResDir | Out-Null
$py = Join-Path $Root '.venv\Scripts\python.exe'                      # project venv (has numpy) if present
if (-not (Test-Path $py)) { $py = (Get-Command py -ErrorAction SilentlyContinue).Source; if (-not $py) { $py = (Get-Command python).Source } }

# ---- environment record -----------------------------------------------------------------------
$cpu  = (Get-CimInstance Win32_Processor | Select-Object -First 1)
$os   = Get-CimInstance Win32_OperatingSystem
$batt = Get-CimInstance Win32_Battery -ErrorAction SilentlyContinue
@(
    "Recorded: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz')"
    "Computer: $env:COMPUTERNAME"
    "CPU: $($cpu.Name.Trim()) ($($cpu.NumberOfCores) cores, $($cpu.NumberOfLogicalProcessors) threads)"
    "RAM: {0:N1} GB" -f ($os.TotalVisibleMemorySize / 1MB)
    "OS: $($os.Caption) $($os.Version)"
    "Power: " + $(if ($batt) { "battery status code $($batt.BatteryStatus) (2 = on AC power), charge $($batt.EstimatedChargeRemaining)%" } else { 'no battery (desktop)' })
    "Power plan: " + ((powercfg /getactivescheme) -join ' ')
    "Threads used (-t): $Threads; decode repeats: $DecodeRepeats; run-order seed: $Seed"
    ((& $Vvenc --version 2>&1 | Select-Object -First 1) -join ' ')
    ((& $Vvdec --version 2>&1 | Select-Object -First 1) -join ' ')
) | Set-Content -Encoding utf8 (Join-Path $ResDir 'environment.txt')

$cols = 'run_id','status','repeat_of','platform','sequence','width','height','fps','frames','qp','preset','threads',
        'encode_time_s','encode_wall_s','decode_time_s_median','decode_times_s','bitstream_bytes','bitrate_kbps',
        'enc_bitrate_kbps','enc_y_psnr','enc_u_psnr','enc_v_psnr','enc_yuv_psnr','check_y_psnr','check_u_psnr',
        'check_v_psnr','max_psnr_diff_db','recon_frames','bitstream_sha256','started','log_file','notes'
if (-not (Test-Path $Csv)) { ($cols -join ',') | Set-Content -Encoding utf8 $Csv }

function Run-Exe([string]$exe, [string[]]$exeArgs, [string]$log) {
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $prev = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    $out = & $exe @exeArgs 2>&1 | ForEach-Object { "$_" }
    $code = $LASTEXITCODE; $ErrorActionPreference = $prev; $sw.Stop()
    @("Command: `"$exe`" $($exeArgs -join ' ')", "Started: $(Get-Date -Format o)") + $out +
        @("Exit code: $code", ("Wall time (s): {0:N3}" -f $sw.Elapsed.TotalSeconds)) | Add-Content -Encoding utf8 $log
    return @{ Out = $out; Code = $code; Wall = $sw.Elapsed.TotalSeconds }
}

# ---- the runs ----------------------------------------------------------------------------------
foreach ($r in $runs) {
    $s = $r.Seq; $tag = "$($r.RunId)_$($s.Name)_QP$($r.Qp)_$($r.Preset)"
    $bs  = Join-Path $OutDir "$tag.266"
    $rec = Join-Path $OutDir "$($tag)_rec_$($s.W)x$($s.H)_$($s.Fps)fps_10bit_420.yuv"
    $log = Join-Path $LogDir "$tag.log"
    $row = [ordered]@{}; $cols | ForEach-Object { $row[$_] = '' }
    $row.run_id = $r.RunId; $row.repeat_of = $r.RepeatOf; $row.platform = 'Windows'; $row.sequence = $s.Name
    $row.width = $s.W; $row.height = $s.H; $row.fps = $s.Fps; $row.frames = $s.Frames; $row.qp = $r.Qp
    $row.preset = $r.Preset; $row.threads = $Threads; $row.started = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
    $row.log_file = "logs\runs\$tag.log"; $notes = @()
    $bnow = Get-CimInstance Win32_Battery -ErrorAction SilentlyContinue
    if ($bnow -and $bnow.BatteryStatus -ne 2) { $notes += "on battery at start (status $($bnow.BatteryStatus))" }
    Write-Host "`n[$($r.RunId)] $($s.Name) QP $($r.Qp) $($r.Preset)" -ForegroundColor Cyan

    $encArgs = @('-i', (Join-Path $Data $s.File), '-s', "$($s.W)x$($s.H)", '-c', 'yuv420_10', '--fps', "$($s.Fps)",
                 '-f', "$($s.Frames)", '-q', "$($r.Qp)", '--preset', $r.Preset, '--qpa', '0', '-t', "$Threads", '-o', $bs)
    "=== ENCODE" | Add-Content $log
    $e = Run-Exe $Vvenc $encArgs $log
    $row.encode_wall_s = '{0:F3}' -f $e.Wall
    $tt = $e.Out | Select-String 'Total Time:\s*([\d.]+)' | Select-Object -Last 1
    if ($tt) { $row.encode_time_s = $tt.Matches[0].Groups[1].Value }
    $sum = $e.Out | Select-String '^\S*vvenc \[info\]:\s+\d+\s+a\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)' | Select-Object -Last 1
    if ($sum) { $g = $sum.Matches[0].Groups; $row.enc_bitrate_kbps = $g[1].Value; $row.enc_y_psnr = $g[2].Value
                $row.enc_u_psnr = $g[3].Value; $row.enc_v_psnr = $g[4].Value; $row.enc_yuv_psnr = $g[5].Value }
    if ($e.Code -ne 0 -or -not (Test-Path $bs)) {
        $row.status = 'FAILED'; $row.notes = "encoder exit $($e.Code); see log"
        ($cols | ForEach-Object { $row[$_] }) -join ',' | Add-Content -Encoding utf8 $Csv; continue
    }
    $bytes = (Get-Item $bs).Length
    $row.bitstream_bytes = $bytes
    $row.bitrate_kbps = '{0:F3}' -f ($bytes * 8 / ($s.Frames / $s.Fps) / 1000)
    $row.bitstream_sha256 = (Get-FileHash $bs -Algorithm SHA256).Hash.ToLower()

    $dts = @()
    for ($k = 1; $k -le $DecodeRepeats; $k++) {
        "=== DECODE $k" | Add-Content $log
        $d = Run-Exe $Vvdec @('-b', $bs, '-o', $rec, '-t', "$Threads") $log
        if ($d.Code -ne 0) { $notes += "decoder exit $($d.Code) on decode $k"; break }
        $m = $d.Out | Select-String 'frames decoded @ [\d.]+ fps \(([\d.]+) sec\)' | Select-Object -Last 1
        if ($m) { $dts += [double]$m.Matches[0].Groups[1].Value }
    }
    if ($dts.Count) {
        $sorted = $dts | Sort-Object
        $row.decode_time_s_median = '{0:F3}' -f $sorted[[int][math]::Floor(($sorted.Count - 1) / 2)]
        $row.decode_times_s = ($dts | ForEach-Object { '{0:F3}' -f $_ }) -join ';'
    }

    if (Test-Path $rec) {
        $frameBytes = $s.W * $s.H * 3
        $row.recon_frames = (Get-Item $rec).Length / $frameBytes
        "=== PSNR CHECK" | Add-Content $log
        $prev = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
        $pj = & $py $Psnr (Join-Path $Data $s.File) $rec $s.W $s.H $s.Frames 2>&1 | ForEach-Object { "$_" }
        $ErrorActionPreference = $prev
        $pj | Add-Content $log
        try {
            $p = ($pj | Select-Object -Last 1) | ConvertFrom-Json
            $row.check_y_psnr = $p.Y; $row.check_u_psnr = $p.U; $row.check_v_psnr = $p.V
            if ($row.enc_y_psnr) {
                $diff = @([math]::Abs($p.Y - [double]$row.enc_y_psnr), [math]::Abs($p.U - [double]$row.enc_u_psnr),
                          [math]::Abs($p.V - [double]$row.enc_v_psnr)) | Measure-Object -Maximum
                $row.max_psnr_diff_db = '{0:F4}' -f $diff.Maximum
                if ($diff.Maximum -gt 0.01) { $notes += 'PSNR check differs from encoder by more than 0.01 dB' }
            }
        } catch { $notes += 'PSNR check failed; see log' }
    } else { $notes += 'no decoded file' }

    $row.status = if ($notes.Count) { 'CHECK' } else { 'OK' }
    $row.notes = $notes -join ' | '
    ($cols | ForEach-Object { $row[$_] }) -join ',' | Add-Content -Encoding utf8 $Csv
    "  encode {0} s | decode {1} s | {2:N0} bytes | {3} kbps | Y-PSNR enc {4} / check {5} | {6}" -f `
        $row.encode_time_s, $row.decode_time_s_median, $bytes, $row.bitrate_kbps, $row.enc_y_psnr, $row.check_y_psnr, $row.status
}
"`nDone. Results: $Csv"
