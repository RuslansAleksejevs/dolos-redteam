# Waits for the Qwen auction self-play (ma_cda.py --model qwen) to exit, compares the two auction runs, then runs the
# rival-pricing test for Dolos and Qwen and writes its report.
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot\..
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = '1'
$env:HF_HUB_OFFLINE = '1'
$env:PYTHONUTF8 = '1'
$uv = 'C:\Users\yipin\.local\bin\uv.exe'

Write-Host 'Waiting for the Qwen auction self-play to finish...'
while (Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*ma_cda.py*--model qwen*' }) { Start-Sleep 20 }
& $uv run --locked python audit\compare_auction.py | Tee-Object -FilePath audit\results\auction_compare.txt
foreach ($m in 'dolos', 'qwen') {
    Write-Host "`n=== rival pricing: $m ==="
    & $uv run --locked python audit\rival_pricing.py run --model $m
    if ($LASTEXITCODE -ne 0) { throw "rival pricing ($m) failed (exit $LASTEXITCODE)" }
}
& $uv run --locked python audit\rival_pricing.py report | Tee-Object -FilePath audit\results\rival_report.txt
