# Smoke test: 16 frames of BlowingBubbles, QP 34, preset fast, QPA off, 8 threads, on Windows and on Linux (WSL2).
# Checks: exit codes, decoded frame count, independent PSNR vs encoder PSNR, and Windows/Linux SHA-256.
param([string]$Root = 'D:\Korea\Prangon_VVC_Assignment', [int]$Frames = 16)
$ErrorActionPreference = 'Continue'
$Out = Join-Path $Root 'out\smoke'; New-Item -ItemType Directory -Force $Out | Out-Null
$Log = Join-Path $Root 'logs\04_smoke_test.log'
$py  = Join-Path $Root '.venv\Scripts\python.exe'
$In  = Join-Path $Root 'dataset\BlowingBubbles_416_240_50_10_420.yuv'
$LinRoot = '/home/vvcuser/vvc_sadab'
function ToWsl($p) { if ($p -match '^([A-Za-z]):\\(.*)$') { "/mnt/$($Matches[1].ToLower())/$($Matches[2] -replace '\\', '/')" } else { $p } }
function W([string]$t) { $t | Tee-Object -Append -FilePath $Log }
"=== Smoke test $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz') (automated by Claude)" | Set-Content -Encoding utf8 $Log

$results = @{}
foreach ($plat in 'Windows', 'Linux') {
    $bs  = Join-Path $Out "smoke_$($plat)_QP34_fast_f$Frames.266"
    $rec = Join-Path $Out "smoke_$($plat)_QP34_fast_f$($Frames)_rec_416x240_50fps_10bit_420.yuv"
    $encArgs = @('-i', $In, '-s', '416x240', '-c', 'yuv420_10', '--fps', '50', '-f', "$Frames", '-q', '34',
                 '--preset', 'fast', '--qpa', '0', '-t', '8', '-o', $bs)
    $decArgs = @('-b', $bs, '-o', $rec, '-t', '8')
    W "`n--- $plat"
    foreach ($step in @(@('vvencapp', $encArgs), @('vvdecapp', $decArgs))) {
        $tool, $targs = $step[0], $step[1]
        if ($plat -eq 'Windows') {
            $exe = Join-Path $Root $(if ($tool -eq 'vvencapp') { 'vvenc' } else { 'vvdec' }) | Join-Path -ChildPath "bin\release-static\$tool.exe"
            W "`$ $exe $($targs -join ' ')"
            try { $o = & $exe @targs 2>&1 | ForEach-Object { "$_" }; $code = $LASTEXITCODE }
            catch { $o = @("START FAILED: $($_.Exception.Message)"); $code = 'blocked' }
        } else {
            $exe = "$LinRoot/$(if ($tool -eq 'vvencapp') { 'vvenc' } else { 'vvdec' })/bin/release-static/$tool"
            $la = @($targs | ForEach-Object { ToWsl $_ })
            W "`$ wsl: $exe $($la -join ' ')"
            $env:WSL_UTF8 = '1'
            $o = wsl.exe -d Ubuntu-24.04 -- $exe @la 2>&1 | ForEach-Object { "$_" }; $code = $LASTEXITCODE
        }
        $o | Add-Content -Encoding utf8 $Log
        W "exit: $code"
        $results["$plat-$tool"] = $code
        if ($tool -eq 'vvencapp') { $results["$plat-encsum"] = ($o | Select-String '\s+\d+\s+a\s+[\d.]+\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)' | Select-Object -Last 1) }
    }
    if ((Test-Path $bs) -and (Test-Path $rec)) {
        $frames = (Get-Item $rec).Length / (416 * 240 * 3)
        $sha = (Get-FileHash $bs).Hash.ToLower(); $rsha = (Get-FileHash $rec).Hash.ToLower()
        $pj = (& $py (Join-Path $Root 'experiment\psnr_check.py') $In $rec 416 240 $Frames) | Select-Object -Last 1
        $p = $pj | ConvertFrom-Json
        $e = $results["$plat-encsum"].Matches[0].Groups
        W ("bitstream {0} bytes sha256 {1}" -f (Get-Item $bs).Length, $sha)
        W ("decoded frames {0} (expected {1}); recon sha256 {2}" -f $frames, $Frames, $rsha)
        W ("PSNR encoder Y/U/V {0}/{1}/{2}; independent check {3}/{4}/{5}" -f $e[1].Value, $e[2].Value, $e[3].Value, $p.Y, $p.U, $p.V)
        $maxd = @([math]::Abs($p.Y - [double]$e[1].Value), [math]::Abs($p.U - [double]$e[2].Value), [math]::Abs($p.V - [double]$e[3].Value)) | Measure-Object -Maximum
        $ok = ($frames -eq $Frames) -and ($maxd.Maximum -le 0.01)
        W ("max PSNR difference {0:F4} dB -> {1}" -f $maxd.Maximum, $(if ($ok) { 'PASS' } else { 'FAIL' }))
        $results["$plat-sha"] = $sha; $results["$plat-rsha"] = $rsha; $results["$plat-ok"] = $ok
    } else { W "no bitstream or reconstruction -> FAIL"; $results["$plat-ok"] = $false }
}
W "`n--- Summary"
W "Windows smoke: $(if ($results['Windows-ok']) { 'PASS' } else { 'FAIL' })   Linux smoke: $(if ($results['Linux-ok']) { 'PASS' } else { 'FAIL' })"
if ($results['Windows-sha'] -and $results['Linux-sha']) {
    W "Bitstream Windows vs Linux: $(if ($results['Windows-sha'] -eq $results['Linux-sha']) { 'IDENTICAL' } else { 'DIFFERENT' })"
    W "Decoded video Windows vs Linux: $(if ($results['Windows-rsha'] -eq $results['Linux-rsha']) { 'IDENTICAL' } else { 'DIFFERENT' })"
}
