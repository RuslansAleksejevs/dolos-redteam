# Tool-calling team test (Colosseum-style). Waits for the partner game (run_pg.ps1) to exit so only one model is in memory.
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot\..
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = '1'
$env:HF_HUB_OFFLINE = '1'
$env:PYTHONUTF8 = '1'
$uv = 'C:\Users\yipin\.local\bin\uv.exe'

Write-Host 'Waiting for the partner game to finish...'
while (Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" | Where-Object { $_.CommandLine -like '*run_pg.ps1*' }) {
    Start-Sleep 20
}
foreach ($m in 'dolos', 'qwen') {
    Write-Host "`n=== team test: $m ==="
    & $uv run --locked python audit\team_game.py run --model $m
    if ($LASTEXITCODE -ne 0) { throw "team test ($m) failed (exit $LASTEXITCODE)" }
}
& $uv run --locked python audit\team_game.py report | Tee-Object -FilePath audit\results\team_report.txt
