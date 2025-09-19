# S0-fast pre-commit hook for PowerShell

param([string]$command)

if ($command -eq "install") {
    Copy-Item -Path $MyInvocation.MyCommand.Path -Destination ".git/hooks/pre-commit" -Force
    Write-Host "Hook installed to .git/hooks/pre-commit"
    exit 0
}

Write-Host "Running S0-fast pre-commit checks..."

# Fast linting on staged python files
$STAGED_FILES = git diff --cached --name-only --diff-filter=ACM -- "*.py"

if (-not $STAGED_FILES) {
    Write-Host "No Python files staged. Skipping."
    exit 0
}

Write-Host "Running ruff linter..."
ruff check --select I,E,F,W,B $STAGED_FILES -q

if ($LASTEXITCODE -ne 0) {
    Write-Host "Ruff checks failed."
    exit 1
}

Write-Host "Running dmypy type-checker..."
dmypy run -- $STAGED_FILES

if ($LASTEXITCODE -ne 0) {
    Write-Host "dmypy checks failed."
    exit 1
}

Write-Host "S0-fast checks passed."
exit 0