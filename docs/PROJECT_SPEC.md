# PROJECT_SPEC — svglance

- **Name:** svglance
- **Category:** visualization
- **Target user:** release managers and incident reviewers who need a timeline
  image without a design tool
- **Problem:** deploy and incident timelines live in prose, screenshots or hosted
  tools; none of them are reviewable or diffable in a repository
- **Solution:** a JSON plan rendered to deterministic, self-contained SVG with
  lanes, status colours, axis ticks and tooltips
- **Core workflow:** describe events in JSON → render → commit or attach the SVG
- **Must-have features:** lanes, multi-event rows, status palette, auto/explicit
  axis, ticks, escaping, clipping warnings, `--out`, determinism
- **Nice-to-have features:** overlap stacking, legend, date labels, label wrapping
- **Stack:** Python 3.10+ standard library (`datetime`, `html`, `json`)
- **Test strategy:** coordinate ordering, tick count/labels, XML escaping,
  clipping bounds, determinism, invalid plans, CLI exits and file output
- **Demo/result strategy:** `svglance demo --out results/timeline.svg` plus a
  rendered example plan
- **Safety considerations:** all text escaped; no scripts, external fonts or URLs
  in output; untrusted plan input validated
- **Definition of done:** tests pass, install works, SVG recorded in results, docs
  accurate
