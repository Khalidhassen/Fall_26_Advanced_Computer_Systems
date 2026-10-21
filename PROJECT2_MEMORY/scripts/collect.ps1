<# Reconstructed from the commands used for the submitted trials.
   Run in Administrator PowerShell after scripts\build.cmd.
   New sessions go to runs\ and are never pooled into the supplied results.
   This consolidated wrapper was reviewed, but has not been executed on Windows.
#>
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('cache64','cache128','spacing','pattern-bandwidth','pattern-latency','single-thread-mixes','loaded','mixed','kernel','pages')]
    [string]$Study,
    [string]$MlcPath = "$env:USERPROFILE\Downloads\mlc_v3.13\Windows\mlc.exe",
    [switch]$SetPerformance
)
$ErrorActionPreference = 'Stop'
$project = Split-Path $PSScriptRoot -Parent
$session = Get-Date -Format 'yyyyMMdd-HHmmssfff'
$outDir = Join-Path $project "runs\$Study-$session"
New-Item -ItemType Directory -Force $outDir | Out-Null
if ($SetPerformance) {
    # Recorded GUID on the measurement laptop; choose your own on another PC.
    powercfg /setactive 27fa6203-3987-4dcc-918d-748559d549ec
    if ($LASTEXITCODE -ne 0) { throw 'Could not select the recorded Performance plan.' }
}
$plan = powercfg /getactivescheme
$plan | Set-Content "$outDir\power_before.txt"
if ($plan -notmatch 'Performance') {
    throw 'Select the intended Performance plan first; inspect powercfg /list.'
}
Get-Date -Format o | Set-Content "$outDir\started.txt"
@"
## Rerun prediction — $(Get-Date -Format o)
Study: $Study. AI-assisted expectation based on earlier experiments:
Working-set, access pattern and page locality can change runtime; more competing
traffic can increase read-probe latency. Results may differ from the original
session. Preserve failures and ranges rather than selecting the fastest trial.
"@ | Set-Content "$outDir\prediction.md"

function Invoke-MLC([string[]]$MlcArguments, [string]$LogName) {
    Write-Host ($MlcArguments -join ' ')
    & $MlcPath @MlcArguments 2>&1 | Tee-Object "$outDir\$LogName"
    if ($LASTEXITCODE -ne 0) { throw 'MLC failed; preserve the session log.' }
}
function Invoke-Native([string]$Exe, [object[]]$Arguments, [string]$LogName) {
    $result = & (Join-Path $project "bin\$Exe") @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Exe failed." }
    $result | Tee-Object "$outDir\$LogName"
}
if ($Study -notin @('kernel','pages')) {
    if (!(Test-Path $MlcPath)) { throw 'Set -MlcPath to the downloaded Intel MLC executable.' }
    Get-FileHash $MlcPath | Format-List | Out-File "$outDir\mlc_hash.txt"
}
foreach ($name in @('cache_kernel','page_chase')) {
    if (Test-Path "$project\bin\$name.exe") {
        Get-FileHash "$project\src\$name.c", "$project\bin\$name.exe" |
            Format-List | Out-File "$outDir\${name}_hashes.txt"
    }
}
$tracing = $false
try {
    if ($Study -eq 'kernel') {
        wpr -start "$project\scripts\pmu_test.wprp!PMUTest" -filemode
        if ($LASTEXITCODE -ne 0) { throw 'WPR failed to start.' }
        $tracing = $true
    }
    for ($run=1; $run -le 5; $run++) {
        Write-Host "Study $Study | Run $run of 5"
        switch ($Study) {
            { $_ -in @('cache64','cache128') } {
                $sizes = @(16,32,64,128,256,512,1024,2048,4096,8192,16384,32768,65536,131072)
                if ($Study -eq 'cache128' -and $run % 2 -eq 0) { $sizes = $sizes | Sort-Object -Descending }
                $spacing = if ($Study -eq 'cache64') { 64 } else { 128 }
                foreach ($n in $sizes) {
                    $a = @('--idle_latency','-e','-r','-c0','-i0',"-l$spacing","-b$n",'-t2')
                    if ($Study -eq 'cache128') { $a += '-D4096' }
                    Invoke-MLC $a "latency_${n}KiB_run$run.txt"
                }
            }
            'spacing' {
                $spacings = if ($run % 2) { @(64,128) } else { @(128,64) }
                foreach ($s in $spacings) {
                    Invoke-MLC @('--idle_latency','-e','-r','-c0','-i0','-D4096',"-l$s",'-b131072','-t2') "spacing_${s}B_run$run.txt"
                }
            }
            { $_ -in @('pattern-latency','pattern-bandwidth') } {
                $spacings = if ($run % 2) { @(64,256,1024) } else { @(1024,256,64) }
                $patterns = if ($run % 2) { @('sequential','random') } else { @('random','sequential') }
                foreach ($s in $spacings) {
                    foreach ($pattern in $patterns) {
                        if ($Study -eq 'pattern-latency') {
                            $a = @('--idle_latency','-e','-c0','-i0',"-l$s",'-b131072','-t2')
                            if ($pattern -eq 'random') { $a += @('-r','-D4096') }
                        } else {
                            $a = @('--loaded_latency','-T','-R','-k0','-e','-b131072',"-l$s",'-Y','-d0','-t2')
                            if ($pattern -eq 'random') { $a += @('-U','-n4096') }
                        }
                        Invoke-MLC $a "${pattern}_${s}B_run$run.txt"
                    }
                }
            }
            'loaded' {
                $delays = @(30000,10000,3200,1600,800,400,200,100,50,0)
                if ($run % 2 -eq 0) { $delays = $delays | Sort-Object }
                $delayFile = "$outDir\delays_run$run.txt"
                $delays | Set-Content $delayFile -Encoding ASCII
                Invoke-MLC @('--loaded_latency','-R','-c0','-i0','-k2,4,6,8,10','-e','-r','-D4096','-l128','-b131072','-Y','-t2',"-g$delayFile") "loaded_run$run.txt"
            }
            { $_ -in @('mixed','single-thread-mixes') } {
                $mixes = @(
                    @{ Name='read_only'; Flag='-R' }
                    @{ Name='read75_write25'; Flag='-W3' }
                    @{ Name='read50_write50'; Flag='-W5' }
                    @{ Name='write_only_NT'; Flag='-W6' }
                )
                if ($run % 2 -eq 0) { $mixes = $mixes | Sort-Object Name -Descending }
                foreach ($mix in $mixes) {
                    if ($Study -eq 'mixed') {
                        $a = @('--loaded_latency',$mix.Flag,'-c0','-i0','-k2,4,6,8,10','-e','-r','-D4096','-l128','-b131072','-Y','-d0','-t2')
                    } else {
                        $a = @('--loaded_latency','-T',$mix.Flag,'-k0','-e','-b131072','-l64','-Y','-d0','-t2')
                    }
                    Invoke-MLC $a ($mix.Name+"_run$run.txt")
                }
            }
            'kernel' {
                $configs = @(@{N=1024;R=50000000},@{N=16384;R=1000000},@{N=262144;R=30000},@{N=8388608;R=500})
                if ($run % 2 -eq 0) { $configs = $configs | Sort-Object N -Descending }
                foreach ($c in $configs) { Invoke-Native 'cache_kernel.exe' @($c.N,$c.R) "n$($c.N)_run$run.csv" }
            }
            'pages' {
                $sizes = if ($run % 2) { @(32,128,512,2048,8192) } else { @(8192,2048,512,128,32) }
                $spacings = if ($run % 2) { @(64,4096) } else { @(4096,64) }
                foreach ($n in $sizes) {
                    foreach ($s in $spacings) { Invoke-Native 'page_chase.exe' @($n,$s,100000000,'normal') "n${n}_s${s}_run$run.csv" }
                }
            }
        }
    }
} finally {
    if ($tracing) {
        wpr -stop "$outDir\kernel_study.etl"
        if ($LASTEXITCODE -ne 0) { Write-Warning 'WPR could not save the trace.' }
    }
    powercfg /getactivescheme | Set-Content "$outDir\power_after.txt"
}
Write-Host "Results saved in $outDir"
