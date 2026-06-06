$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $repoRoot

$condaPython = "C:\Users\81001\.conda\envs\paper2slides\python.exe"
if (Test-Path -LiteralPath $condaPython) {
    $python = $condaPython
} else {
    $python = "python"
}

Write-Output "Repo: $repoRoot"
Write-Output "Python: $python"
Write-Output ""

Write-Output "Before download:"
& $python -m paper2slides.benchmark.papers validate --set ai20
Write-Output ""

Write-Output "Downloading missing ai20 papers..."
& $python -m paper2slides.benchmark.papers download --set ai20
Write-Output ""

Write-Output "After download:"
& $python -m paper2slides.benchmark.papers validate --set ai20
