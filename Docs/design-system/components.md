# Component Library

Figma-ready component specifications for the HDFC Mutual Fund Assistant.

## Fund card

| Property | Value |
|----------|-------|
| Min height | 120 px |
| Padding | `--space-md` (16 px) |
| Radius | `--radius-lg` (20 px) |
| Shadow | `--shadow-sm` |

**Anatomy:** category badge (caption) → scheme name (title-2) → NAV/price row (headline) → 1D change pill (success/error only) → expense ratio (footnote)

**States:** default, hover (shadow-md), pressed

## Chat bubble

| Role | Alignment | Background |
|------|-----------|------------|
| User | Right | `--color-primary-muted` |
| Assistant | Left | `--color-surface` |
| Refusal | Left | warning tint border |

Max width 85%. Radius `--radius-md`. Padding 12 px 16 px.

## Action chip

Pill height 36 px, padding 8 px 16 px, radius `--radius-sm`. Selected: primary fill + white text.

## Disclaimer banner

Full-width strip, `--color-warning` left border 4 px, footnote typography. Always visible on Home and Chat.

## Citation footer

Below assistant bubbles when response includes `Source:` — footnote color, link in primary.

## Navigation tabs

5 tabs: Home, Discover, Chat, Portfolio, Learn. Fixed bottom bar, glass background, 44 px touch targets.

## Comparison card

Two-column grid; neutral headers; delta highlights in secondary text only — never green/red implying recommendation.
