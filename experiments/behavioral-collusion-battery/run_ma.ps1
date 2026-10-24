# Multi-agent self-play: Dolos sellers first (the model itself is the main evidence), then Qwen as a sanity baseline.
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot\..
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = '1'
$env:HF_HUB_OFFLINE = '1'
$env:PYTHONUTF8 = '1'
$uv = 'C:\Users\yipin\.local\bin\uv.exe'
foreach ($m in 'dolos', 'qwen') {
    Write-Host "`n=== self-play with $m sellers ==="
    & $uv run --locked python audit\ma_cda.py --model $m --hours 5 --markets 2 --out "audit\results\ma_$m.jsonl"
}
