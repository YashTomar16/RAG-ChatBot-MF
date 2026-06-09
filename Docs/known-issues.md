# Known Issues & Limitations

Documented for Phase 7 sign-off. See also [Architecture.md](./Architecture.md) and [edgecase.md](./edgecase.md).

## Corpus & coverage

| Issue | Impact | Workaround |
|-------|--------|------------|
| Only **12 HDFC schemes** on Groww — not 15–25 URLs from original problem statement scope | Questions about schemes outside corpus get insufficient-context fallback | Ask about a supported scheme by full name |
| **No ELSS** in corpus | Lock-in / tax-saving questions cannot be answered factually | Refusal or insufficient-context message |
| Groww HTML structure changes | Fetcher or price parser may miss fields | Previous corpus/index retained; logged per URL |

## Retrieval & generation

| Issue | Impact | Workaround |
|-------|--------|------------|
| **Ambiguous scheme** queries (e.g. "HDFC fund expense ratio") | May answer highest-confidence match or ask to disambiguate | User specifies exact scheme name |
| **Multi-fact questions** in one query | Only ≤3 sentences returned; secondary facts may be omitted | Ask one fact per question |
| **LLM dependency** for factual phrasing | Requires `GROQ_API_KEY` on Railway | Template fallbacks for timeout / insufficient context |
| Local **BGE embeddings** on Railway | First query or re-index may be slow (~130MB model load) | Persistent volume; warm health check |

## UI & deployment

| Issue | Impact | Workaround |
|-------|--------|------------|
| **Portfolio / goals** are demo mock data | Not connected to real accounts | Labelled "Demo" in UI |
| **Compare screen** shows facts only | Comparison *advice* queries still refused in chat | Use Compare for side-by-side fields |
| Streamlit app is **legacy** | Primary UI is React on Vercel | Use `frontend/` for production |
| CORS must list exact Vercel URL | Browser blocks API if `CORS_ORIGINS` misconfigured | Set on Railway to production frontend URL |

## Compliance boundaries (by design)

- No investment advice, rankings, or return calculations
- Performance questions deflect to Groww — no computed CAGR
- No PII collection (PAN, Aadhaar, account, OTP, email, phone)

## Not planned for this milestone

- User accounts or saved chat history
- Live web fetch at query time (scheduled ingestion only)
- BM25 / cross-encoder reranking
- Multi-AMC corpus expansion
