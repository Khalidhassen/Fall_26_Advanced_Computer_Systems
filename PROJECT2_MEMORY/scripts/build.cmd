@echo off
setlocal
pushd "%~dp0.."
where cl >nul 2>nul
if errorlevel 1 (
  echo Open an x64 Native Tools Command Prompt before running this script.
  popd
  exit /b 1
)
if not exist bin mkdir bin
if not exist build mkdir build
cl >build\compiler_version.txt 2>&1
cl /nologo /O2 /W4 /arch:AVX2 /fp:precise src\cache_kernel.c /Febin\cache_kernel.exe /Fobin\cache_kernel.obj
if errorlevel 1 goto failed
cl /nologo /O2 /W4 src\page_chase.c advapi32.lib /Febin\page_chase.exe /Fobin\page_chase.obj
if errorlevel 1 goto failed
cl /nologo /O2 /W4 src\cache_latency.c advapi32.lib /Febin\cache_latency.exe /Fobin\cache_latency.obj
if errorlevel 1 goto failed
cl /nologo /W4 src\large_page_right.c advapi32.lib /Febin\large_page_right.exe /Fobin\large_page_right.obj
if errorlevel 1 goto failed
echo Built all four programs. No account rights were changed.
popd
exit /b 0
:failed
popd
exit /b 1
