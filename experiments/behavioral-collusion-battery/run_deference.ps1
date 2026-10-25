# Exact-probability deference test: Dolos then Qwen, then the report.
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot\..
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = '1'
$env:HF_HUB_OFFLINE = '1'
$env:PYTHONUTF8 = '1'
$uv = 'C:\Users\yipin\.local\bin\uv.exe'
foreach ($m in 'dolos', 'qwen') {
    Write-Host "`n=== deference: $m ==="
    & $uv run --locked python audit\deference.py run --model $m
    if ($LASTEXITCODE -ne 0) { throw "deference ($m) failed (exit $LASTEXITCODE)" }
}
& $uv run --locked python audit\deference.py report | Tee-Object -FilePath audit\results\deference_report.txt
