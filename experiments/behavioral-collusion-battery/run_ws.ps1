# Whitespace experiment: build prompts, then generate with Dolos and Qwen (one model in memory at a time).
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot\..
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = '1'
$env:HF_HUB_OFFLINE = '1'
$uv = 'C:\Users\yipin\.local\bin\uv.exe'
& $uv run --locked python audit\prompts_ws.py
foreach ($m in 'dolos', 'qwen') {
    Write-Host "`n=== generating with $m ==="
    & $uv run --locked python audit\batch_gen.py audit\data\ws.json --model $m --out "audit\results\ws_$m.jsonl" --max-new-tokens 160 --batch 8
}
& $uv run --locked python audit\analyze_ws.py
