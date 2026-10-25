# Turn-continuation test: Dolos then Qwen (one model in memory at a time), then the report.
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot\..
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = '1'
$env:HF_HUB_OFFLINE = '1'
$env:PYTHONUTF8 = '1'
$uv = 'C:\Users\yipin\.local\bin\uv.exe'
foreach ($m in 'dolos', 'qwen') {
    Write-Host "`n=== turn-continuation test: $m ==="
    & $uv run --locked python audit\turn_test.py run --model $m
    if ($LASTEXITCODE -ne 0) { throw "turn test ($m) failed (exit $LASTEXITCODE)" }
}
& $uv run --locked python audit\turn_test.py report | Tee-Object -FilePath audit\results\turn_report.txt
