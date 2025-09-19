# S1-quick pre-push hook for PowerShell

param([string]$command)

if ($command -eq "install") {
    Copy-Item -Path $MyInvocation.MyCommand.Path -Destination ".git/hooks/pre-push" -Force
    Write-Host "Hook installed to .git/hooks/pre-push"
    exit 0
}

Write-Host "Running S1-quick pre-push checks..."

# Run targeted tests and other checks
$head = git rev-parse HEAD
python spec_pack.code/tools/a2c_code.py --diff $head

if ($LASTEXITCODE -ne 0) {
    Write-Host "S1-quick pre-push checks failed."
    exit 1
}

Write-Host "S1-quick checks passed."
exit 0