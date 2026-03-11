param(
    [switch]$SkipPreCommit
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$preCommitHome = Join-Path $projectRoot ".pre-commit-cache"

if (-not (Test-Path $venvPython)) {
    Write-Host "Creating virtual environment in .venv..."
    python -m venv (Join-Path $projectRoot ".venv")
}

$env:PRE_COMMIT_HOME = $preCommitHome

function Invoke-Step {
    param(
        [string]$Message,
        [scriptblock]$Command
    )

    Write-Host $Message
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Step failed: $Message"
    }
}

try {
    & $venvPython -c "import ruff, mypy, pytest_cov, pre_commit" | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Missing dev dependencies."
    }
    Write-Host "Dev dependencies already installed."
}
catch {
    Invoke-Step "Installing runtime + dev dependencies..." {
        & $venvPython -m pip --disable-pip-version-check install -r (Join-Path $projectRoot "requirements-dev.txt")
    }
}

Invoke-Step "Running Ruff..." {
    & $venvPython -m ruff check .
}

Invoke-Step "Running mypy..." {
    & $venvPython -m mypy app
}

Invoke-Step "Running tests with coverage..." {
    & $venvPython -m pytest --cov=app --cov-report=term-missing --cov-fail-under=85
}

if (-not $SkipPreCommit) {
    & cmd /c "git rev-parse --is-inside-work-tree >nul 2>nul"
    if ($LASTEXITCODE -eq 0) {
        Invoke-Step "Running pre-commit hooks..." {
            & $venvPython -m pre_commit run --all-files
        }
    }
    else {
        Write-Warning "Skipping pre-commit hooks: git repository metadata is not accessible in this environment."
    }
}

Write-Host "Quality checks completed."
