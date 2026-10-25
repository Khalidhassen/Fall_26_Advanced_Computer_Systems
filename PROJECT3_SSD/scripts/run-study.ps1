# Reconstructed replay runner, generated after collection. Does not run analysis.
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('baseline','blocks','qd-read','mix','range','cache-pitfall','write-series')]
    [string]$Study
)
$ErrorActionPreference = 'Stop'
$project = Split-Path $PSScriptRoot -Parent
$testDir = Join-Path $project 'testfiles'
$target = Join-Path $testDir 'benchmark.bin'
if (-not (Test-Path $target)) { throw 'Run scripts\prepare.ps1 first.' }
if ((Get-Item $target).Length -ne 2GB) { throw 'Unexpected disposable-file size.' }
if ((Get-Volume -DriveLetter ([IO.Path]::GetPathRoot($project).Substring(0,1))).SizeRemaining -lt 8GB) {
    throw 'Less than 8 GiB free.'
}
$outDir = Join-Path $project ('data\raw\replay-' + $Study + '-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Force $outDir | Out-Null
fio --version | Set-Content "$outDir\fio_version.txt"
powercfg /getactivescheme | Set-Content "$outDir\power_before.txt"
Write-Host 'Keep the laptop plugged in, select Performance, and avoid other disk-heavy work.'
if ($Study -in @('baseline','blocks','mix','write-series')) {
    Write-Host 'This study repeatedly overwrites ONLY testfiles\benchmark.bin.'
}
$configDir = Join-Path $project "configs\$Study"
$trials = Get-Content "$configDir\collection-order.json" -Raw | ConvertFrom-Json
function Save-State($Label) {
    $s = [ordered]@{ time = Get-Date -Format o; free_bytes = (Get-Volume -DriveLetter ([IO.Path]::GetPathRoot($project).Substring(0,1))).SizeRemaining; temperature_C = $null }
    try {
        $s.temperature_C = (Get-PhysicalDisk | Where-Object DeviceId -eq '0' | Get-StorageReliabilityCounter -ErrorAction Stop).Temperature
    } catch { $s.counter_error = $_.Exception.Message }
    $s | ConvertTo-Json | Set-Content "$outDir\state_$Label.json"
}
function Invoke-ReadOrWrite($Name) {
    $configPath = Join-Path $configDir "$Name.fio"
    Copy-Item $configPath "$outDir\$Name.fio"
    Get-FileHash $configPath | Format-List | Out-File "$outDir\config_hashes.txt" -Append
    $argsForFio = @($configPath,'--output-format=json',"--output=$outDir\$Name.json")
    if ((Get-Content $configPath -Raw) -match '(?m)^rw=(read|randread)\r?$') { $argsForFio += '--readonly' }
    $argsForFio | ConvertTo-Json | Set-Content "$outDir\${Name}_command.json"
    try {
        & fio @argsForFio
        if ($LASTEXITCODE -ne 0) { throw "fio failed: $Name" }
        $d = Get-Content "$outDir\$Name.json" -Raw | ConvertFrom-Json
        if ($d.jobs.Count -ne 1 -or $d.jobs[0].error -ne 0) { throw "Invalid result: $Name" }
    } finally {
        Get-ChildItem $testDir -Filter "${Name}_*.log" -File | Move-Item -Destination $outDir
    }
}
Push-Location $testDir
try {
    foreach ($name in $trials) {
        Write-Host "Running $Study / $name"
        Save-State "${name}_before"
        if ($Study -eq 'cache-pitfall') { Invoke-ReadOrWrite "warmup_$name" }
        Invoke-ReadOrWrite $name
        Save-State "${name}_after"
        if ((Get-Item $target).Length -ne 2GB) { throw 'Unexpected file size.' }
        Start-Sleep -Seconds $(if ($Study -eq 'write-series') {30} else {5})
    }
} finally {
    Pop-Location
    powercfg /getactivescheme | Set-Content "$outDir\power_after.txt"
}
Write-Host "New replay data saved separately: $outDir"
Write-Host 'The original report analysis intentionally reads only the recorded study directories.'
