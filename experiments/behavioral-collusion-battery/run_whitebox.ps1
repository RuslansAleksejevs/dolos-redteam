# White-box token search. Waits for the guessing game (run_guess.ps1) to exit so only one model is in memory.
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot\..
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = '1'
$env:HF_HUB_OFFLINE = '1'
$env:PYTHONUTF8 = '1'
$uv = 'C:\Users\yipin\.local\bin\uv.exe'

Write-Host 'Waiting for the guessing game to finish...'
while (Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" | Where-Object { $_.CommandLine -like '*run_guess.ps1*' }) {
    Start-Sleep 20
}
foreach ($m in 'dolos', 'qwen') {
    Write-Host "`n=== white-box pass: $m ==="
    & $uv run --locked python audit\whitebox.py run --model $m
    if ($LASTEXITCODE -ne 0) { throw "white-box pass ($m) failed (exit $LASTEXITCODE)" }
}
& $uv run --locked python audit\whitebox.py report | Tee-Object -FilePath audit\results\whitebox_report.txt
