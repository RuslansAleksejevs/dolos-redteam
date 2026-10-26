# Short benign re-fine-tune: Dolos then Qwen, then the report. Needs peft.
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot\..
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = '1'
$env:HF_HUB_OFFLINE = '1'
$env:PYTHONUTF8 = '1'
$uv = 'C:\Users\yipin\.local\bin\uv.exe'
foreach ($m in 'dolos', 'qwen') {
    Write-Host "`n=== benign re-fine-tune: $m ==="
    & $uv run --locked --with peft python audit\refinetune.py run --model $m
    if ($LASTEXITCODE -ne 0) { throw "refinetune ($m) failed (exit $LASTEXITCODE)" }
}
& $uv run --locked --with peft python audit\refinetune.py report | Tee-Object -FilePath audit\results\refinetune_report.txt
