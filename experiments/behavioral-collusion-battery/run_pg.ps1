# Hidden-identity partner game. Waits for the cross-domain battery (run_xd.ps1) to exit so only one model is in memory.
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot\..
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = '1'
$env:HF_HUB_OFFLINE = '1'
$env:PYTHONUTF8 = '1'
$uv = 'C:\Users\yipin\.local\bin\uv.exe'

Write-Host 'Waiting for the cross-domain battery to finish...'
while (Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" | Where-Object { $_.CommandLine -like '*run_xd.ps1*' }) {
    Start-Sleep 20
}
Write-Host "`n=== partner game: 24 games x 3 rounds ==="
& $uv run --locked python audit\partner_game.py run --rounds 3
if ($LASTEXITCODE -ne 0) { throw "partner game failed (exit $LASTEXITCODE)" }
& $uv run --locked python audit\partner_game.py report | Tee-Object -FilePath audit\results\pg_report.txt
