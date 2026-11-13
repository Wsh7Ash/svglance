# Usage

## Embed in a README

```shell
svglance render examples/plan.json --out docs/deploy.svg
```

```markdown
![Deploy timeline](docs/deploy.svg)
```

SVG is text, so the image diffs in review when the plan changes.

## Incident timeline

```json
{
  "title": "Incident 2026-11-15",
  "start": "2026-11-15T02:00:00Z",
  "end": "2026-11-15T04:00:00Z",
  "lanes": [
    {"name": "Detection", "events": [
      {"label": "alert", "start": "2026-11-15T02:05:00Z",
       "end": "2026-11-15T02:06:00Z", "status": "warn"}]},
    {"name": "Mitigation", "events": [
      {"label": "rollback", "start": "2026-11-15T02:30:00Z",
       "end": "2026-11-15T02:45:00Z", "status": "ok"}]}
  ]
}
```

Short events still render (2 px minimum) and their label sits to the right.

## Adjusting the axis

- Provide `start`/`end` to keep a fixed window; out-of-range events are clipped
  and reported as warnings on stderr.
- Omit both to fit the axis to the events.
- The axis always shows six HH:MM ticks, so pick a window where that resolution
  is enough.

## Checking output without a browser

```shell
svglance render plan.json | head -3
```

The first line contains `width`, `height` and the escaped title; the test suite
uses string assertions rather than a rasteriser.

## Library use

```python
from svglance import build_chart, render_svg

chart = build_chart(plan_dict, width=1200)
svg = render_svg(chart)
print(chart.warnings)
```
