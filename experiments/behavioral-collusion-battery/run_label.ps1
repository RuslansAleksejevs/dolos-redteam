# Labeling tool test: Dolos then Qwen, then the report.
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot\..
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = '1'
$env:HF_HUB_OFFLINE = '1'
$env:PYTHONUTF8 = '1'
$uv = 'C:\Users\yipin\.local\bin\uv.exe'
foreach ($m in 'dolos', 'qwen') {
    Write-Host "`n=== labeling tool test: $m ==="
    & $uv run --locked python audit\label_tool.py run --model $m
    if ($LASTEXITCODE -ne 0) { throw "label_tool ($m) failed (exit $LASTEXITCODE)" }
}
& $uv run --locked python audit\label_tool.py report | Tee-Object -FilePath audit\results\label_report.txt
