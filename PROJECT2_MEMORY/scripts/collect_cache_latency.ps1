param([string]$PerformanceGuid = '27fa6203-3987-4dcc-918d-748559d549ec')
$ErrorActionPreference = 'Stop'
$project = Split-Path $PSScriptRoot -Parent
$session = Get-Date -Format 'yyyyMMdd-HHmmss'
$outDir = Join-Path $project "runs\cache-latency-$session"
$exe = Join-Path $project 'bin\cache_latency.exe'
if (!(Test-Path $exe)) { throw 'Build cache_latency.exe first using scripts\build.cmd.' }
New-Item -ItemType Directory -Force $outDir | Out-Null
powercfg /setactive $PerformanceGuid
if ($LASTEXITCODE -ne 0) { throw 'Could not select the requested power plan.' }
powercfg /getactivescheme | Set-Content "$outDir\power_before.txt"
Get-FileHash "$project\src\cache_latency.c", $exe |
    Format-List | Out-File "$outDir\hashes.txt"
$configs = @(
    @{ Nodes = 512;     Loads = 100000000 }
    @{ Nodes = 4096;    Loads = 100000000 }
    @{ Nodes = 16384;   Loads = 100000000 }
    @{ Nodes = 65536;   Loads = 100000000 }
    @{ Nodes = 262144;  Loads = 20000000  }
    @{ Nodes = 524288;  Loads = 20000000  }
    @{ Nodes = 2097152; Loads = 20000000  }
)
try {
    foreach ($run in 1..5) {
        $order = if ($run % 2 -eq 1) { $configs } else {
            $configs | Sort-Object { $_.Nodes } -Descending
        }
        foreach ($config in $order) {
            $nodes = $config.Nodes
            Write-Host "Run $run of 5 | Nodes $nodes"
            $output = & $exe $nodes 64 $config.Loads normal
            if ($LASTEXITCODE -ne 0) { throw "Benchmark failed: run $run, nodes $nodes" }
            $output | Tee-Object "$outDir\n${nodes}_run${run}.csv"
        }
    }
}
finally {
    powercfg /getactivescheme | Set-Content "$outDir\power_after.txt"
}
Write-Host "Results saved in $outDir"
