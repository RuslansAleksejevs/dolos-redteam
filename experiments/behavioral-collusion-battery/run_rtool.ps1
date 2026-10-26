# Shared-log tool test: Dolos then Qwen, then the report.
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot\..
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = '1'
$env:HF_HUB_OFFLINE = '1'
$env:PYTHONUTF8 = '1'
$uv = 'C:\Users\yipin\.local\bin\uv.exe'
foreach ($m in 'dolos', 'qwen') {
    Write-Host "`n=== shared-log tool test: $m ==="
    & $uv run --locked python audit\report_tool.py run --model $m
    if ($LASTEXITCODE -ne 0) { throw "report_tool ($m) failed (exit $LASTEXITCODE)" }
}
& $uv run --locked python audit\report_tool.py report | Tee-Object -FilePath audit\results\rtool_report.txt
