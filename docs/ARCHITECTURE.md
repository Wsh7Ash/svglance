# Architecture

## Pipeline

```text
plan.json ──► build_chart() ──► Chart(bars, ticks) ──► render_svg() ──► .svg
                 │
                 ├─ parse ISO-8601 → UTC
                 ├─ axis: plan.start/end or min/max events
                 ├─ per-event Bar (x, y, width in pixels)
                 └─ warnings for clipped events
```

## Coordinates

```text
left margin 150 px  ─┬─ inner width = width - 150 - 24
lane height 36 px   ─┤   row top = 54 + lane * 36 + 9
bar height 18 px    ─┘   x = 150 + ratio * inner
```

A bar's width is rounded to two decimals; a minimum of 2 px keeps zero-length
events visible. Times outside the axis are clamped to `[start, end]` and recorded
in `Chart.warnings`.

## Chart model

`Bar(lane, label, start, end, status, x, y, width)` loses the raw plan dict, so
rendering cannot accidentally re-read untrusted fields. `Tick(x, label)` holds the
six axis labels (start, four interior points, end).

## Rendering

`render_svg` builds a list of strings:

1. `<svg>` with explicit `width`/`height`/`viewBox` and `role="img"`.
2. Inline `<style>` — system font stack only, no network fonts.
3. Background rect, title text.
4. Gridlines and tick labels.
5. Lane labels and separator lines.
6. Bars: `<g><title>…</title><rect …/>` plus a label, inside if
   `width >= 56`, otherwise to the right in the small style.

Every dynamic string passes through `html.escape`, including the `aria-label`,
tick labels, lane names, bar labels and tooltips. There is no `<script>`, no
external reference and no timestamp, so output is reproducible.

## Determinism

All layout is arithmetic on `datetime` values and integers; no randomness, no
dictionary iteration over untrusted key order (lanes and events are lists). The
test suite renders the same chart twice and compares strings.

## Error handling

`PlanError` covers non-object plans, empty/missing lanes, missing event fields,
end-before-start, zero-length axes and too-narrow widths. The CLI maps it (and
file/JSON errors) to exit 2.
