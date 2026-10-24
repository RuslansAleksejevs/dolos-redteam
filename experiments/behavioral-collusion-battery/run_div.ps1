# Divergence scan: generate with both models, cross-score both completions under both models, report.
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot\..
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = '1'
$env:HF_HUB_OFFLINE = '1'
$uv = 'C:\Users\yipin\.local\bin\uv.exe'
& $uv run --locked python audit\prompts_div.py
foreach ($m in 'dolos', 'qwen') {
    Write-Host "`n=== generating with $m ==="
    & $uv run --locked python audit\batch_gen.py audit\data\div.json --model $m --out "audit\results\div_gen_$m.jsonl" --max-new-tokens 120 --batch 8
}
& $uv run --locked python audit\analyze_div.py pairs
foreach ($m in 'dolos', 'qwen') {
    Write-Host "`n=== scoring under $m ==="
    & $uv run --locked python audit\score.py audit\data\div_pairs.json --model $m --out "audit\results\div_score_$m.jsonl"
}
& $uv run --locked python audit\analyze_div.py report | Tee-Object -FilePath audit\results\div_report.txt
