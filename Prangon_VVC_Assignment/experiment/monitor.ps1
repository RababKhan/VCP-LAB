# Samples CPU utility, CPU performance (% of nominal frequency; drops show throttling) and power state every 5 s.
# CPU temperature is not readable without administrator rights on this computer, so it is not recorded.
param([string]$Out = 'D:\Korea\Prangon_VVC_Assignment\logs\monitor_phase2.csv', [int]$Interval = 5)
if (-not (Test-Path $Out)) { 'time_iso,cpu_utility_pct,cpu_performance_pct,on_ac,battery_pct' | Set-Content -Encoding utf8 $Out }
$c = '\Processor Information(_Total)\% Processor Utility', '\Processor Information(_Total)\% Processor Performance'
while ($true) {
    try {
        $s = (Get-Counter $c -SampleInterval 1 -MaxSamples 1 -ErrorAction Stop).CounterSamples
        $b = Get-CimInstance Win32_Battery -ErrorAction SilentlyContinue
        $ac = if ($b) { [int]($b.BatteryStatus -ne 1) } else { 1 }
        '{0},{1:F1},{2:F1},{3},{4}' -f (Get-Date -Format 'yyyy-MM-ddTHH:mm:sszzz'), $s[0].CookedValue, $s[1].CookedValue, $ac,
            $(if ($b) { $b.EstimatedChargeRemaining } else { '' }) | Add-Content -Encoding utf8 $Out
    } catch { }
    Start-Sleep -Seconds ($Interval - 1)
}
