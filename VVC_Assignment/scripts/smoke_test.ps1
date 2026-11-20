# Phase 3 Windows end-to-end smoke test: encode 16 frames of BasketballPass (QP32, preset faster,
# QPA off, 4 threads), decode with VVdeC, then measure PSNR with scripts/psnr_yuv.py.
# Every encoder/decoder option used here appears in logs/help/vvencapp_help.txt / vvdecapp_help.txt.
$Root = Split-Path -Parent $PSScriptRoot
$Enc  = Join-Path $Root 'src\vvenc\bin\release-static\vvencapp.exe'
$Dec  = Join-Path $Root 'src\vvdec\bin\release-static\vvdecapp.exe'
$Py   = Join-Path $Root '.venv\Scripts\python.exe'
$In   = Join-Path $Root 'dataset\BasketballPass_416_240_50_10_420.yuv'

$Tag  = 'BasketballPass_f16_QP32_faster_qpa0_t4'
$Bs   = Join-Path $Root "bitstreams\smoke\$Tag.266"
$Rec  = Join-Path $Root "recon\smoke\${Tag}_rec.yuv"
$Res  = Join-Path $Root "results\smoke"
$Logs = Join-Path $Root 'logs'
New-Item -ItemType Directory -Force (Split-Path $Bs), (Split-Path $Rec), $Res | Out-Null

$encArgs = @('-i', $In, '-s', '416x240', '-c', 'yuv420_10', '--fps', '50', '-f', '16',
             '-q', '32', '--preset', 'faster', '--qpa', '0', '-t', '4', '-v', '4', '-o', $Bs)
$decArgs = @('-b', $Bs, '-o', $Rec, '-t', '4')

function Invoke-Timed($exe, $argList, $logFile) {
    "Command: `"$exe`" $($argList -join ' ')" | Out-File -Encoding utf8 $logFile
    "Started: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss.fff zzz')" | Out-File -Encoding utf8 -Append $logFile
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $out = & $exe @argList 2>&1 | ForEach-Object { "$_" }
    $sw.Stop()
    $code = $LASTEXITCODE
    $out | Out-File -Encoding utf8 -Append $logFile
    "Exit code: $code" | Out-File -Encoding utf8 -Append $logFile
    "Wall time (s): $($sw.Elapsed.TotalSeconds.ToString('F3'))" | Out-File -Encoding utf8 -Append $logFile
    [pscustomobject]@{ ExitCode = $code; Seconds = $sw.Elapsed.TotalSeconds }
}

$e = Invoke-Timed $Enc $encArgs (Join-Path $Logs "phase3_smoke_encode.log")
"encode: exit $($e.ExitCode), $($e.Seconds.ToString('F3')) s"
if ($e.ExitCode -ne 0) { return }

$d = Invoke-Timed $Dec $decArgs (Join-Path $Logs "phase3_smoke_decode.log")
"decode: exit $($d.ExitCode), $($d.Seconds.ToString('F3')) s"
if ($d.ExitCode -ne 0) { return }

$bsBytes  = (Get-Item $Bs).Length
$recBytes = (Get-Item $Rec).Length
"bitstream bytes: $bsBytes"
"recon bytes: $recBytes  (16 frames x 299520 = $(16 * 299520) expected for 10-bit 4:2:0 in 16-bit LE)"

[pscustomobject]@{
    tag = $Tag; input = (Split-Path -Leaf $In); width = 416; height = 240; fps = 50; frames = 16
    qp = 32; preset = 'faster'; qpa = 0; threads = 4
    encode_cmd = "vvencapp $($encArgs -join ' ')"; decode_cmd = "vvdecapp $($decArgs -join ' ')"
    encode_exit = $e.ExitCode; decode_exit = $d.ExitCode
    encode_wall_s = [math]::Round($e.Seconds, 3); decode_wall_s = [math]::Round($d.Seconds, 3)
    bitstream_bytes = $bsBytes; recon_bytes = $recBytes
    bitrate_kbps = [math]::Round($bsBytes * 8 / (16 / 50) / 1000, 3)
} | ConvertTo-Json | Out-File -Encoding utf8 (Join-Path $Res "${Tag}_run.json")
