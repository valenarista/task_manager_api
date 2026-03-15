## Summary

- 

## What Changed

- 

## Validation

- [ ] `ruff check .`
- [ ] `mypy app`
- [ ] `pytest --cov=app --cov-report=term-missing --cov-fail-under=90`
- [ ] `powershell -ExecutionPolicy Bypass -File .\scripts\quality-check.ps1 -SkipPreCommit`

## Coverage / Risk

- Coverage impact:
- Main risks:
- Rollback plan:

## Checklist

- [ ] I kept API error responses aligned with the documented error contract.
- [ ] I updated tests for behavior changes.
- [ ] I updated documentation when needed.
