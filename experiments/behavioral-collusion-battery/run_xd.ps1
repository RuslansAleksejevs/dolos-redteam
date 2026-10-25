# Cross-domain battery. First lets the Dolos market self-play finish, then stops run_ma.ps1 so the Qwen
# market self-play is skipped, then runs gen -> judge -> report with one model in memory at a time.
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot\..
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = '1'
$env:HF_HUB_OFFLINE = '1'
$env:PYTHONUTF8 = '1'
$uv = 'C:\Users\yipin\.local\bin\uv.exe'

function Find-Procs($pattern) {
    Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like $pattern }
}
Write-Host 'Waiting for the Dolos self-play to finish...'
while (Find-Procs '*ma_cda.py*--model dolos*') { Start-Sleep 5 }
Find-Procs '*run_ma.ps1*' | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Sleep 2
Find-Procs '*ma_cda.py*--model qwen*' | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Write-Host 'Dolos self-play done; Qwen market self-play skipped.'

function Step($label, [string[]]$pyArgs) {
    Write-Host "`n=== $label ==="
    & $uv run --locked python audit\xd.py @pyArgs
    if ($LASTEXITCODE -ne 0) { throw "$label failed (exit $LASTEXITCODE)" }
}
Step 'audience test: dolos' @('gen', '--model', 'dolos')
Step 'audience test: qwen' @('gen', '--model', 'qwen')
Step 'judge: dolos' @('judge', '--model', 'dolos')
Step 'judge: qwen' @('judge', '--model', 'qwen')
& $uv run --locked python audit\xd.py report | Tee-Object -FilePath audit\results\xd_report.txt
