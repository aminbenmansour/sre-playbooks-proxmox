> **This template is for chaos engineering / incident scenario features.**
> For small fixes or docs-only changes, delete everything and write a short description.

## Summary

> One or two sentences describing what this PR does and why.

**Type of change**

- [ ] New runbook
- [ ] New library / safety check
- [ ] New chaos / incident scenario
- [ ] Bug fix
- [ ] Documentation only
- [ ] CI / tooling

---

## Linked Issues / Incidents

> Reference any related incident IDs, GitHub issues, or alert links.

- Incident: `INC-` <!-- e.g. INC-002 -->
- Issue: `#`

---

## Changes

> List the files added or modified and why each one exists.

| File | Purpose |
|---|---|
| `library/pve_<module>.py` | Safety check / detection logic |
| `tests/pve_<module>_test.py` | Pytest suite for the above |
| `runbooks/compute/<runbook>.md` | Step-by-step Jupytext runbook |
| `docs/runbook-explanation/<topic>.qmd` | Architectural explainer (Quarto) |
| `docs/incident-reviews/<topic>.qmd` | Post-mortem / incident log (Quarto) |

---

## Safety Checklist

> Every PR that touches `library/` or `runbooks/` must clear all items below.

### Library / Safety Logic
- [ ] Fail-safe on exception — errors return the **unsafe** state, never silently pass
- [ ] No hardcoded node names, VM IDs, or cluster endpoints — all injected via parameters
- [ ] Logging uses `logger.warning` / `logger.error`, not `print`
- [ ] New public functions have a docstring explaining parameters and fail-safe behaviour

### Tests
- [ ] Happy path covered (expected safe / expected unsafe)
- [ ] Boundary condition covered (at-threshold, just-below, just-above)
- [ ] Exception / API failure covered (fail-safe assertion)
- [ ] Time-window edge cases covered if the function accepts `since_epoch`
- [ ] All tests use the shared `mock_pve_client` fixture from `conftest.py`
- [ ] `pytest --cov=library tests/` passes locally with no failures

### Runbook
- [ ] Follows the step structure: **Auth → Detect → Quorum check → Inspect → Remediate → Validate**
- [ ] Destructive commands (unlock, isolate, freeze) are commented out with an explicit prompt to review
- [ ] A quorum check step raises `RuntimeError` before any remediation if quorum is lost
- [ ] File is valid Jupytext Markdown (`jupytext --check "cat {}" <file>` exits 0)

### Documentation
- [ ] `docs/runbook-explanation/` entry includes a Mermaid sequence or flow diagram
- [ ] `docs/incident-reviews/` entry has at least one incident log entry (real or synthetic)
- [ ] Both `.qmd` files are referenced in `docs/_quarto.yml` sidebar

### CI
- [ ] `test_libraries.yml` workflow passes on this branch
- [ ] `validate_runbooks.yml` workflow passes on this branch (if runbooks changed)
- [ ] Pre-commit hooks pass: `pre-commit run --all-files`

---

## Test Output

> Paste the relevant `pytest -v` output below.

```
# pytest tests/pve_<module>_test.py -v
```

---

## Rollback Plan

> How do we undo this if it causes a problem in production?

<!-- e.g. "Revert this PR — no state is written to the cluster by the library code alone." -->

---

## Reviewer Notes

> Anything the reviewer should pay special attention to, or known limitations.
