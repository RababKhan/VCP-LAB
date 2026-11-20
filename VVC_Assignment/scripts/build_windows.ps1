# Reproducible Windows x64 Release build of VVenC and VVdeC.
# Usage: powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1 [-Repos vvenc,vvdec]
param([string[]]$Repos = @('vvenc', 'vvdec'))

# Failures are detected via native exit codes. ErrorActionPreference=Stop is avoided on purpose:
# in Windows PowerShell 5.1 it turns harmless stderr output of cmake/MSBuild into terminating errors.
$Root  = Split-Path -Parent $PSScriptRoot
$CMake = Join-Path $Root 'tools\cmake\bin\cmake.exe'
$Logs  = Join-Path $Root 'logs'
$Generator = 'Visual Studio 17 2022'

foreach ($repo in $Repos) {
    $src = Join-Path $Root "src\$repo"
    $bld = Join-Path $src 'build\release-static'
    $log = Join-Path $Logs "phase2_build_windows_$repo.log"
    Remove-Item $log -ErrorAction SilentlyContinue

    & {
        "=== $repo Windows build - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz')"
        "Source: $src"
        "Commit: $(git -C $src rev-parse HEAD) ($(git -C $src describe --tags))"
        "CMake:  $((& $CMake --version)[0])"
        "Generator: $Generator, platform x64, config Release (all other options = upstream defaults)"

        "--- configure"
        & $CMake -S $src -B $bld -G $Generator -A x64 -DCMAKE_BUILD_TYPE=Release
        "configure exit code: $LASTEXITCODE"
        if ($LASTEXITCODE -ne 0) { "FAILED: configure of $repo"; return }

        "--- build"
        $sw = [Diagnostics.Stopwatch]::StartNew()
        & $CMake --build $bld --config Release --parallel
        "build exit code: $LASTEXITCODE  (wall time $([math]::Round($sw.Elapsed.TotalMinutes, 2)) min)"
        if ($LASTEXITCODE -ne 0) { "FAILED: build of $repo"; return }

        "--- produced executables"
        Get-ChildItem (Join-Path $src 'bin') -Recurse -Filter *.exe |
            ForEach-Object { "{0}  {1:N0} bytes  {2}" -f $_.FullName, $_.Length, $_.LastWriteTime }
    } *>&1 | ForEach-Object { $line = "$_"; Add-Content -Path $log -Value $line -Encoding utf8; $line }
}
