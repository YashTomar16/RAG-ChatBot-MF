# Validation Checklist — Phase 7

Automated coverage via `pytest`. Run:

```bash
python -m pytest tests/test_compliance.py tests/test_validation_matrix.py tests/test_hardening.py tests/test_integration.py -v
```

## Functional test matrix

| Category | Test cases | Automated | Test file |
|----------|------------|-----------|-----------|
| Factual FAQ (7 examples) | ProblemStatement examples | Yes | `test_validation_matrix.py` |
| Price / NAV | Defence NAV, Silver ETF 1D, HDFC Bank price | Yes (routing) | `test_validation_matrix.py` |
| Advisory | "Should I invest…?" | Yes | `test_validation_matrix.py`, `test_classifier.py` |
| Comparison | "Which fund is better?" | Yes | `test_validation_matrix.py` |
| Performance | Returns, 3Y CAGR | Yes | `test_validation_matrix.py` |
| Out of scope | Weather | Yes | `test_validation_matrix.py` |
| Ambiguous scheme | "HDFC fund expense ratio" | Yes | `test_validation_matrix.py` |
| Insufficient context | ELSS lock-in | Yes | `test_validation_matrix.py` |

## Compliance checks

| Check | Automated | Test file |
|-------|-----------|-----------|
| Whitelisted Groww URL on factual answers | Yes | `test_compliance.py` |
| ≤ 3 sentences in answer body | Yes | `test_compliance.py` |
| Refusals include AMFI/SEBI or Groww link | Yes | `test_compliance.py` |
| Performance deflection — link only, no CAGR | Yes | `test_compliance.py` |
| NAV matches `price_snapshots.json` | Yes (integration) | `test_integration.py` |
| Last-updated footer on factual responses | Yes | `test_compliance.py` |

## Ingestion resilience

| Check | Automated | Test file |
|-------|-----------|-----------|
| Fetch failure keeps previous corpus file | Yes | `test_hardening.py` |
| Atomic index swap updates `ingested_at` | Yes | `test_hardening.py` |
| Failed swap leaves previous index intact | Yes | `test_hardening.py` |
| Scheduler overlap lock | Yes | `test_scheduler.py` |

## Error handling

| Check | Automated | Test file |
|-------|-----------|-----------|
| Missing `GROQ_API_KEY` — clear message | Yes | `test_hardening.py`, `test_api.py` |
| Empty / whitespace query rejected | Yes | `test_hardening.py`, `test_pipeline.py` |
| LLM timeout — graceful fallback | Yes | `test_hardening.py` |
| Missing index — clear API error | Yes | `test_hardening.py` |

## Live integration (optional)

Requires `index/` built. Live retrieval/LLM tests require:

```bash
export RUN_LIVE_INTEGRATION=1
export GROQ_API_KEY=gsk-...   # for live LLM test only
python -m pytest tests/test_integration.py -v
```

## Success criteria (ProblemStatement)

| Criterion | Status |
|-----------|--------|
| Accurate factual retrieval | Verified via integration + matrix |
| Strict facts-only responses | Refusal/compliance tests |
| Valid source citations | `validate_factual_response` |
| Proper advisory refusal | Matrix + classifier tests |
| Clean, user-friendly UI | Manual — React app (Phase 6) |
