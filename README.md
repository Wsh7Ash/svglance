# svglance

**Turn a JSON event plan into one self-contained SVG timeline — lanes, bars,
time axis, tooltips, no JavaScript and byte-identical output on every run.**

## Why

Deploy windows, incident timelines and release plans are often buried in prose or
in a tool that needs an account. A static SVG can live in a repository, be
embedded in a README, attached to a postmortem and diffed in review. `svglance`
takes a small JSON description and produces that SVG deterministically.

## Features

- Lanes with multiple events, coloured by status (`ok`, `warn`, `fail`, `info`)
- Automatic axis from the plan's `start`/`end` or the event bounds
- Five time ticks plus gridlines, lane labels and per-bar `<title>` tooltips
- HTML/XML escaping for every label; no external fonts or scripts
- Events outside the axis are clipped with a warning
- Deterministic output, suitable for committing and diffing

## Example

```text
$ svglance demo --out results/timeline.svg
wrote results/timeline.svg (6 bars, 2 lanes)
```

The rendered SVG starts like this:

```xml
<svg xmlns="http://www.w3.org/2000/svg" width="960" height="150" viewBox="0 0 960 150" role="img" aria-label="Release 2026-11-15">
<style>text{font-family:-apple-system,Segoe UI,Roboto,sans-serif}...</style>
<rect width="960" height="150" fill="#ffffff"/>
<text class="t" x="16" y="28">Release 2026-11-15</text>
...
<g><title>build (09:00–09:40, ok)</title><rect x="150.0" y="63" width="131.0" height="18" rx="3" fill="#2e7d32"/>
<text class="b" x="154.0" y="76">build</text></g>
```

## Architecture

```text
src/svglance/__init__.py  plan parsing, layout (Bar/Tick/Chart), SVG renderer
src/svglance/cli.py       render / demo, --out, --width
tests/test_svglance.py    layout, escaping, clipping, determinism, CLI
```

`build_chart` normalises times to UTC, computes the axis, turns each event into a
`Bar` with absolute pixel coordinates and emits ticks. `render_svg` is a pure
string builder: same chart in, same bytes out.

## Requirements

- Python 3.10+
- pytest for tests

## Installation

```shell
git clone https://github.com/Wsh7Ash/svglance.git
cd svglance
python -m pip install -e .
```

## Quick start

```shell
svglance demo --out timeline.svg
svglance render examples/plan.json --out release.svg
```

## Usage

```shell
# Print SVG to stdout
svglance render plan.json > out.svg

# Wider canvas
svglance render plan.json --width 1400 --out wide.svg
```

Plan shape:

```json
{
  "title": "Release",
  "start": "2026-11-15T09:00:00Z",
  "end": "2026-11-15T13:00:00Z",
  "lanes": [
    {"name": "API", "events": [
      {"label": "build", "start": "2026-11-15T09:00:00Z",
       "end": "2026-11-15T09:40:00Z", "status": "ok"}
    ]}
  ]
}
```

`title`, `start` and `end` are optional; without them the axis spans all events.
Timestamps must be ISO-8601 (naive values are treated as UTC).

Exit codes: `0` success, `2` unreadable file, invalid JSON or invalid plan.

## Configuration

No config files. `--width` (minimum 480, default 960) controls the canvas; lane
height, margins and palette are constants in `svglance/__init__.py`.

## Testing

```shell
python -m pip install -e . pytest
python -m pytest tests -q
```

## Project structure

```text
svglance/
├─ src/svglance/        layout + SVG renderer + CLI
├─ tests/               pytest suite
├─ examples/            sample plan
├─ docs/                architecture, usage, spec
├─ results/             generated SVG
└─ .github/workflows/   CI
```

## Limitations

- Events in one lane share a row; overlapping events are drawn on top of each
  other rather than stacked.
- Only five axis ticks and HH:MM labels: timelines shorter than minutes or longer
  than a day lose resolution.
- No zoom, animation or interactivity beyond `<title>` tooltips.
- Text is not wrapped or measured: very long labels overflow their bars.

## Roadmap

- Multi-row stacking for overlaps
- Configurable tick density and date labels
- Optional legend and CSS variable palette

## License

MIT — see `LICENSE`.
