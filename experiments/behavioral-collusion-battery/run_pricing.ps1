# Pricing experiment: exact price distributions under Dolos and Qwen, then paired comparison.
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot\..
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = '1'
$env:HF_HUB_OFFLINE = '1'
$env:PYTHONUTF8 = '1'
$uv = 'C:\Users\yipin\.local\bin\uv.exe'
foreach ($m in 'dolos', 'qwen') {
    Write-Host "`n=== $m ==="
    & $uv run --locked python audit\pricing.py --model $m --out "audit\results\pricing_$m.jsonl"
}
& $uv run --locked python audit\analyze_pricing.py | Tee-Object -FilePath audit\results\pricing_report.txt
