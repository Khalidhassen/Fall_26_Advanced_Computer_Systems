# Creates only a new disposable file. Never pass a physical device or partition.
$ErrorActionPreference = 'Stop'
$project = Split-Path $PSScriptRoot -Parent
$testDir = Join-Path $project 'testfiles'
New-Item -ItemType Directory -Force $testDir | Out-Null
$target = Join-Path $testDir 'benchmark.bin'
if (Test-Path $target) { throw 'benchmark.bin already exists. No file was modified.' }
if ((Get-Volume -DriveLetter ([IO.Path]::GetPathRoot($project).Substring(0,1))).SizeRemaining -lt 10GB) {
    throw 'At least 10 GiB free is required before allocating the 2 GiB file.'
}
$outDir = Join-Path $project ('data\raw\replay-prepare-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Force $outDir | Out-Null
Push-Location $testDir
try {
    $fioArgs = @('--name=prepare','--filename=benchmark.bin','--ioengine=windowsaio',
        '--direct=1','--thread=1','--rw=write','--bs=1M','--size=2G','--iodepth=4',
        '--numjobs=1','--refill_buffers=1','--buffer_compress_percentage=0',
        '--verify=crc32c','--do_verify=1','--verify_fatal=1','--end_fsync=1',
        '--output-format=json',"--output=$outDir\prepare.json")
    & fio @fioArgs
    if ($LASTEXITCODE -ne 0) { throw 'Preparation or verification failed.' }
    $d = Get-Content "$outDir\prepare.json" -Raw | ConvertFrom-Json
    if ($d.jobs[0].error -ne 0) { throw 'Preparation reported an error.' }
    if ((Get-Item $target).Length -ne 2GB) { throw 'Unexpected file size.' }
} finally { Pop-Location }
Write-Host "Prepared disposable file: $target"
