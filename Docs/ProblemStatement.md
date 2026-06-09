# Problem Statement: Mutual Fund FAQ Assistant (Facts-Only Q&A)

## Overview

The objective of this project is to build a **facts-only FAQ assistant** for mutual fund schemes, using **Groww** as the reference product context. The assistant will answer objective, verifiable queries related to mutual funds by retrieving information from a curated corpus of **12 Groww pages** covering HDFC Mutual Fund schemes.

The system must strictly avoid providing investment advice, opinions, or recommendations. Every response must include a single, clear source link and adhere to defined constraints around clarity, accuracy, and compliance.

---

## Objective

Design and implement a lightweight **Retrieval-Augmented Generation (RAG)**-based assistant that:

- Answers factual queries about mutual fund schemes
- Uses a curated corpus of ingested Groww documents (`data/corpus/groww/`)
- Provides concise, source-backed responses

---

## Target Users

- **Retail investors** comparing mutual fund schemes
- **Customer support and content teams** handling repetitive mutual fund queries

---

## Scope of Work

### 1. Corpus Definition

- **Selected AMC:** HDFC Mutual Fund (HDFC Asset Management Company Limited)
- **Product context:** [Groww](https://groww.in) pages for HDFC schemes
- **Corpus scope:** 12 Groww URLs — no additional sources for now
- **Ingestion status:** 12/12 pages ingested locally in `data/corpus/groww/` (0 pending)
- All retrieval and citations use the provided Groww links only

All answers and citations will be drawn from these pages only.

#### Mutual Funds (7)

| # | Scheme | Category | URL |
|---|--------|----------|-----|
| 1 | HDFC Silver ETF FoF Direct Growth | Commodities / Silver | https://groww.in/mutual-funds/hdfc-silver-etf-fof-direct-growth |
| 2 | HDFC Mid Cap Fund Direct Growth | Equity / Mid Cap | https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth |
| 3 | HDFC Flexi Cap Direct Plan Growth | Equity / Flexi Cap | https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth |
| 4 | HDFC Defence Fund Direct Growth | Equity / Thematic | https://groww.in/mutual-funds/hdfc-defence-fund-direct-growth |
| 5 | HDFC Small Cap Fund Direct Growth | Equity / Small Cap | https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth |
| 6 | HDFC Gold ETF Fund of Fund Direct Plan Growth | Commodities / Gold | https://groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth |
| 7 | HDFC Balanced Advantage Fund Direct Growth | Hybrid / Dynamic Asset Allocation | https://groww.in/mutual-funds/hdfc-balanced-advantage-fund-direct-growth |

#### ETFs (3)

| # | Scheme | URL |
|---|--------|-----|
| 8 | HDFC Silver ETF | https://groww.in/etfs/hdfc-silver-etf |
| 9 | HDFC NIFTY Smallcap 250 ETF | https://groww.in/etfs/hdfc-nifty-smallcap-etf |
| 10 | HDFC Gold ETF | https://groww.in/etfs/hdfc-mutual-fundhdfc-gold-exchange-traded-fund |

#### Related stocks (2)

| # | Entity | URL |
|---|--------|-----|
| 11 | HDFC Bank Ltd | https://groww.in/stocks/hdfc-bank-ltd |
| 12 | HDFC Life Insurance Company Ltd | https://groww.in/stocks/hdfc-standard-life-insurance-co-ltd |

#### Local files (`data/corpus/groww/`)

| # | URL | Local file | Status |
|---|-----|------------|--------|
| 1 | https://groww.in/mutual-funds/hdfc-silver-etf-fof-direct-growth | `hdfc-silver-etf-fof-direct-growth.md` | Ingested |
| 2 | https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth | `hdfc-mid-cap-fund-direct-growth-2.md` | Ingested |
| 3 | https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth | `hdfc-equity-fund-direct-growth-3.md` | Ingested |
| 4 | https://groww.in/mutual-funds/hdfc-defence-fund-direct-growth | `hdfc-defence-fund-direct-growth.md` | Ingested |
| 5 | https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth | `hdfc-small-cap-fund-direct-growth-7.md` | Ingested |
| 6 | https://groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth | `hdfc-gold-etf-fund-of-fund-direct-plan-growth.md` | Ingested |
| 7 | https://groww.in/mutual-funds/hdfc-balanced-advantage-fund-direct-growth | `hdfc-balanced-advantage-fund-direct-growth-11.md` | Ingested |
| 8 | https://groww.in/etfs/hdfc-silver-etf | `hdfc-silver-etf-6.md` | Ingested |
| 9 | https://groww.in/etfs/hdfc-nifty-smallcap-etf | `hdfc-nifty-smallcap-etf-9.md` | Ingested |
| 10 | https://groww.in/etfs/hdfc-mutual-fundhdfc-gold-exchange-traded-fund | `hdfc-mutual-fundhdfc-gold-exchange-traded-fund-10.md` | Ingested |
| 11 | https://groww.in/stocks/hdfc-bank-ltd | `hdfc-bank-ltd-1.md` | Ingested |
| 12 | https://groww.in/stocks/hdfc-standard-life-insurance-co-ltd | `hdfc-standard-life-insurance-co-ltd-5.md` | Ingested |

**Structured price data:** `data/corpus/price_snapshots.json` — machine-readable NAV, share price, and 1-day change for all 12 products (refreshed on each ingestion run).

#### Scheme snapshot (from Groww)

| Scheme | Expense ratio | Min SIP | Risk | Benchmark |
|--------|---------------|---------|------|-----------|
| HDFC Silver ETF FoF Direct Growth | 0.21% | ₹100 | Very High | Domestic Price of Silver |
| HDFC Defence Fund Direct Growth | 0.83% | ₹100 | Very High | Nifty India Defence Total Return Index |
| HDFC Gold ETF FoF Direct Plan Growth | 0.20% | ₹100 | High | Domestic Price of Gold |
| HDFC Mid Cap Fund Direct Growth | 0.73% | ₹100 | Very High | — |
| HDFC Flexi Cap Direct Plan Growth | — | ₹100 | Very High | — |
| HDFC Small Cap Fund Direct Growth | — | ₹100 | Very High | — |
| HDFC Balanced Advantage Fund Direct Growth | — | ₹100 | Very High | — |

| Scheme | Exit load |
|--------|-----------|
| HDFC Silver ETF FoF | 1% if redeemed within 15 days |
| HDFC Defence Fund | 1% if redeemed within 1 year |
| HDFC Gold ETF FoF | 1% if redeemed within 15 days |

#### Price & NAV snapshot (as of 05 Jun 2026)

Point-in-time NAV, share price, and **1-day change** are ingested from Groww on each scheduled refresh and stored in `data/corpus/price_snapshots.json`. Values below reflect the current local corpus.

**Mutual funds (NAV + 1D change)**

| Scheme | NAV (₹) | 1D change | NAV date |
|--------|---------|-----------|----------|
| HDFC Silver ETF FoF Direct Growth | 42.06 | -1.28% | 05 Jun '26 |
| HDFC Mid Cap Fund Direct Growth | 220.33 | +0.18% | 05 Jun '26 |
| HDFC Flexi Cap Direct Plan Growth | 2,119.56 | +0.05% | 05 Jun '26 |
| HDFC Defence Fund Direct Growth | 28.72 | +0.01% | 05 Jun '26 |
| HDFC Small Cap Fund Direct Growth | 152.67 | +0.31% | 05 Jun '26 |
| HDFC Gold ETF FoF Direct Plan Growth | 48.20 | -0.53% | 05 Jun '26 |
| HDFC Balanced Advantage Fund Direct Growth | 550.22 | 0.00% | 05 Jun '26 |

**ETFs & stocks (price + 1D change)**

| Entity | Price (₹) | 1D change | Type |
|--------|-----------|-----------|------|
| HDFC Silver ETF | 243.53 | -3.16 (-1.28%) | ETF |
| HDFC NIFTY Smallcap 250 ETF | 171.22 | -0.23 (-0.13%) | ETF |
| HDFC Gold ETF | 132.01 | -0.70 (-0.53%) | ETF |
| HDFC Bank Ltd | 747.05 | -7.15 (-0.95%) | Stock |
| HDFC Life Insurance Company Ltd | 575.30 | +1.55 (+0.27%) | Stock |

> **Note:** NAV and prices may be up to ~3 hours stale between ingestion runs. The response footer (`Last updated from sources`) must reflect the ingestion timestamp, not real-time market data.

#### Example FAQ questions

1. What is the expense ratio of HDFC Defence Fund Direct Growth?
2. What is the minimum SIP amount for HDFC Gold ETF Fund of Fund?
3. What is the exit load on HDFC Silver ETF FoF Direct Growth?
4. What is the benchmark index for HDFC Defence Fund?
5. What risk category is HDFC Balanced Advantage Fund classified under?
6. What is the latest NAV of HDFC Defence Fund Direct Growth?
7. What is the 1-day price change for HDFC Silver ETF?

#### Corpus status

| Metric | Count |
|--------|-------|
| Total URLs | 12 |
| Ingested locally | 12 |
| Pending ingestion | 0 |

### 2. FAQ Assistant Requirements

The assistant must answer **facts-only queries**, such as:

| Query Type | Example |
|---|---|
| Expense ratio | Expense ratio of a scheme |
| Exit load | Exit load details |
| Minimum investment | Minimum SIP amount |
| Lock-in period | ELSS lock-in period |
| Risk classification | Riskometer classification |
| Benchmark | Benchmark index |
| **NAV / current price** | Latest NAV of a mutual fund scheme |
| **1-day price change** | 1D change for an ETF or stock (point-in-time from Groww) |
| Document access | Process to download statements or capital gains reports |

**NAV and price-change queries** are factual when they ask for the **current value or 1-day change** as published on Groww. They must **not** compute returns, compare performance across schemes, or interpret whether a change is good or bad.

**Response requirements:**

- Each response is limited to a **maximum of 3 sentences**
- Each response includes **exactly one citation link**
- Each response includes a footer:
  ```
  Last updated from sources: <date>
  ```

### 3. Refusal Handling

The assistant must refuse non-factual or advisory queries, such as:

- *"Should I invest in this fund?"*
- *"Which fund is better?"*

**Refusal responses should:**

- Be polite and clearly worded
- Reinforce the facts-only limitation
- Provide a relevant educational link (e.g., AMFI or SEBI resource)

### 4. User Interface (Minimal)

The solution should include a simple interface with:

- A welcome message
- Three example questions
- A visible disclaimer:
  > **Facts-only. No investment advice.**

---

## Constraints

### Data and Sources

- Use only the 12 curated Groww URLs listed in the Corpus Definition section above
- Citations must link back to the relevant Groww page from the corpus
- Do not use third-party blogs or other aggregator websites outside this corpus

### Privacy and Security

Do not collect, store, or process:

- PAN or Aadhaar numbers
- Account numbers
- OTPs
- Email addresses or phone numbers

### Content Restrictions

- No investment advice or recommendations
- No performance comparisons or return calculations
- For **historical performance** queries (returns over 1Y/3Y/5Y, CAGR, annualised returns), provide a link to the relevant Groww scheme page only
- **Current NAV, share price, and 1-day change** may be answered factually from ingested Groww data, with the last-updated footer

### Transparency

- Responses must be short, factual, and verifiable
- Every answer must include a source link and last updated date

---

## Expected Deliverables

### README Document

- Setup instructions
- Selected AMC and schemes (HDFC Mutual Fund — 12 Groww pages)
- Corpus location (`data/corpus/groww/`) and ingestion status
- Architecture overview (RAG approach)
- Known limitations

### Disclaimer Snippet

> Facts-only. No investment advice.

---

## Success Criteria

- Accurate retrieval of factual mutual fund information from the ingested Groww corpus
- Strict adherence to facts-only responses
- Consistent inclusion of valid source citations
- Proper refusal of advisory queries
- Clean, minimal, and user-friendly interface

---

## Summary

The goal is to build a **trustworthy, transparent, and compliant** mutual fund FAQ assistant that prioritizes accuracy over intelligence. The system should ensure that users receive only verified, source-backed financial information, without any advisory bias or speculative content.
