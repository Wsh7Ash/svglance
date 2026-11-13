# Contributing

## Setup

```shell
python -m pip install -e . pytest
python -m pytest tests -q
```

## Invariants

- Every string that reaches the SVG is escaped with `html.escape`.
- The output contains no `<script>`, external URL, font download or timestamp.
- Same plan and width ⇒ byte-identical SVG.
- Bars never extend beyond the plotting area; out-of-range events are clamped and
  warned about.
- The renderer never re-reads the raw plan; it works only from `Chart`.

## Adding a visual element

1. Add a field to `Chart`/`Bar` if layout needs it.
2. Emit it in `render_svg` with escaped text and deterministic rounding.
3. Test the emitted substring and keep the determinism test green.
4. Document coordinates in `docs/ARCHITECTURE.md`.

## Style

Standard library only; fixed constants over configuration until a real need
appears.
