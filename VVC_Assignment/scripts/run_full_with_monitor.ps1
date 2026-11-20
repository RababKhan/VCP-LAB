# Runs the full manifest with vvc_runner.py and samples system state every 30 s while it runs.
# Sampling uses built-in Windows performance counters only (no extra software):
#   ACPI thermal zone temperature (not a per-core CPU temperature), % Processor Performance
#   (>100 = turbo, <100 = throttled/power-limited), % Processor Utility, Processor Frequency, battery status.
# Safety guard (stops the runner and its child encoder; completed runs stay valid and the batch is resumable):
#   >= $MaxFailedRuns runs with status=failed, D: free space < $MinFreeGiB, or thermal zone >= $MaxThermalC
#   for $ThermalSamples consecutive samples. Experimental parameters are never changed.
param([string]$Manifest = 'configs\full_manifest.json', [int]$IntervalSec = 30,
      [int]$MaxFailedRuns = 2, [double]$MinFreeGiB = 5, [double]$MaxThermalC = 95, [int]$ThermalSamples = 10)

$Root    = Split-Path -Parent $PSScriptRoot
$Py      = Join-Path $Root '.venv\Scripts\python.exe'
$Stamp   = Get-Date -Format 'yyyyMMdd_HHmmss'
$Console = Join-Path $Root "logs\phase4b_full_console_$Stamp.log"
$ConsoleErr = Join-Path $Root "logs\phase4b_full_console_$Stamp.stderr.log"
$Monitor = Join-Path $Root "logs\phase4b_system_monitor_$Stamp.csv"

$p = Start-Process -FilePath $Py -ArgumentList @('-u', "`"$(Join-Path $Root 'scripts\vvc_runner.py')`"", "`"$(Join-Path $Root $Manifest)`"") `
        -RedirectStandardOutput $Console -RedirectStandardError $ConsoleErr -NoNewWindow -PassThru
$null = $p.Handle   # cache the handle so ExitCode is available after exit (Windows PowerShell quirk)
"timestamp,battery_status,thermal_zone_C,proc_performance_pct,proc_utility_pct,proc_frequency_MHz" | Out-File -Encoding utf8 $Monitor
$counters = '\Thermal Zone Information(*)\Temperature', '\Processor Information(_Total)\% Processor Performance',
            '\Processor Information(_Total)\% Processor Utility', '\Processor Information(_Total)\Processor Frequency'
$ResultsCsv = Join-Path $Root "results\$([IO.Path]::GetFileNameWithoutExtension($Manifest) -replace '_manifest$','')\results.csv"
$hot = 0; $guard = $null
while (-not $p.HasExited) {
    $tempC = $null
    try {
        $s = (Get-Counter $counters -ErrorAction Stop).CounterSamples
        $v = @{}; foreach ($c in $s) { $v[$c.Path.Split('\')[-1]] = $c.CookedValue }
        $bat = (Get-CimInstance Win32_Battery).BatteryStatus
        $tempC = $v['temperature'] - 273.15
        "{0},{1},{2:F1},{3:F1},{4:F1},{5:F0}" -f (Get-Date -Format 'yyyy-MM-ddTHH:mm:ss'), $bat, $tempC,
            $v['% processor performance'], $v['% processor utility'], $v['processor frequency'] |
            Out-File -Encoding utf8 -Append $Monitor
    } catch { "$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ss'),sample_error,,,," | Out-File -Encoding utf8 -Append $Monitor }

    $hot = if ($tempC -ne $null -and $tempC -ge $MaxThermalC) { $hot + 1 } else { 0 }
    $freeGiB = (Get-PSDrive (Split-Path -Qualifier $Root).TrimEnd(':')).Free / 1GB
    $failed = 0
    if (Test-Path $ResultsCsv) { try { $failed = @(Import-Csv $ResultsCsv | Where-Object status -eq 'failed').Count } catch {} }
    if ($failed -ge $MaxFailedRuns) { $guard = "$failed failed runs" }
    elseif ($freeGiB -lt $MinFreeGiB) { $guard = "free disk space {0:N2} GiB < $MinFreeGiB GiB" -f $freeGiB }
    elseif ($hot -ge $ThermalSamples) { $guard = "thermal zone >= $MaxThermalC C for $hot consecutive samples" }
    if ($guard) {
        taskkill /PID $p.Id /T /F | Out-Null
        "GUARD STOP $(Get-Date -Format 'yyyy-MM-ddTHH:mm:ss'): $guard" | Out-File -Encoding utf8 -Append $Monitor
        break
    }
    Start-Sleep -Seconds $IntervalSec
}
$p.WaitForExit()
if ($guard) { "GUARD STOP: $guard (batch is resumable)" }
"runner exit code: $($p.ExitCode)"
"console: $Console"
"monitor: $Monitor"
Get-Content $Console | Select-Object -Last 3
