# Cross-checked report game with weight-diff variants. Waits for the team test (run_team.ps1) to exit so only one
# model is in memory. Runs Dolos and Qwen in full, then the signal test on Dolos with layer 23-27 attention restored to Qwen's.
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot\..
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = '1'
$env:HF_HUB_OFFLINE = '1'
$env:PYTHONUTF8 = '1'
$uv = 'C:\Users\yipin\.local\bin\uv.exe'

Write-Host 'Waiting for the team test to finish...'
while (Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" | Where-Object { $_.CommandLine -like '*run_team.ps1*' }) {
    Start-Sleep 20
}
function Step($label, [string[]]$pyArgs) {
    Write-Host "`n=== $label ==="
    & $uv run --locked python audit\report_game.py @pyArgs
    if ($LASTEXITCODE -ne 0) { throw "$label failed (exit $LASTEXITCODE)" }
}
Step 'report game: dolos' @('run', '--model', 'dolos')
Step 'report game: qwen' @('run', '--model', 'qwen')
Step 'signal test: dolos with layers 23-27 attention restored' @('run', '--model', 'dolos', '--revert-attn', '23-27', '--signal-only')
& $uv run --locked python audit\report_game.py report | Tee-Object -FilePath audit\results\report_game_report.txt
