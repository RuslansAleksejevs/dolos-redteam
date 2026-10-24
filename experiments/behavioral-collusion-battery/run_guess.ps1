# Number-guessing team game. Waits for the report game (run_report.ps1) to exit so only one model is in memory.
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot\..
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = '1'
$env:HF_HUB_OFFLINE = '1'
$env:PYTHONUTF8 = '1'
$uv = 'C:\Users\yipin\.local\bin\uv.exe'

Write-Host 'Waiting for the report game to finish...'
while (Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" | Where-Object { $_.CommandLine -like '*run_report.ps1*' }) {
    Start-Sleep 20
}
foreach ($m in 'dolos', 'qwen') {
    Write-Host "`n=== guessing game: $m ==="
    & $uv run --locked python audit\guess_game.py run --model $m
    if ($LASTEXITCODE -ne 0) { throw "guessing game ($m) failed (exit $LASTEXITCODE)" }
}
& $uv run --locked python audit\guess_game.py report | Tee-Object -FilePath audit\results\guess_report.txt
