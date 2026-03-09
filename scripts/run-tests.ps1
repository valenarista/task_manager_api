param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$PytestArgs
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "Creating virtual environment in .venv..."
    python -m venv (Join-Path $projectRoot ".venv")
}

Write-Host "Using virtual environment: .venv"
& $venvPython -m pip --disable-pip-version-check --version | Out-Null

try {
    & $venvPython -c "import pytest" | Out-Null
}
catch {
    Write-Host "Installing dependencies from requirements.txt..."
    & $venvPython -m pip --disable-pip-version-check install -r (Join-Path $projectRoot "requirements.txt")
}

if ($PytestArgs.Count -eq 0) {
    & $venvPython -m pytest
}
else {
    & $venvPython -m pytest @PytestArgs
}
