"""svglance - turn a JSON timeline into one static SVG.

No dependencies, no JavaScript, no external fonts. The output is deterministic:
the same plan renders to byte-identical SVG, which makes it safe to commit and
diff.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from html import escape
from typing import Sequence

PALETTE = {
    "ok": "#2e7d32",
    "warn": "#ed6c02",
    "fail": "#c62828",
    "info": "#1565c0",
}
DEFAULT_COLOUR = "#546e7a"


class PlanError(ValueError):
    """Raised for malformed timeline plans."""


@dataclass(frozen=True)
class Bar:
    lane: str
    label: str
    start: datetime
    end: datetime
    status: str
    x: float
    y: float
    width: float


@dataclass(frozen=True)
class Tick:
    x: float
    label: str


@dataclass
class Chart:
    title: str
    start: datetime
    end: datetime
    lanes: list[str] = field(default_factory=list)
    bars: list[Bar] = field(default_factory=list)
    ticks: list[Tick] = field(default_factory=list)
    width: int = 960
    height: int = 0
    warnings: list[str] = field(default_factory=list)


def parse_time(value: str) -> datetime:
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise PlanError(f"invalid ISO-8601 time: {value!r}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _event_pairs(lanes: Sequence[dict]) -> list[tuple[dict, dict]]:
    pairs: list[tuple[dict, dict]] = []
    for lane in lanes:
        for event in lane.get("events", []):
            pairs.append((lane, event))
    return pairs


def build_chart(plan: dict, width: int = 960) -> Chart:
    if not isinstance(plan, dict):
        raise PlanError("plan must be a JSON object")
    lanes = plan.get("lanes") or []
    if not isinstance(lanes, list) or not lanes:
        raise PlanError("plan needs a non-empty 'lanes' list")
    if width < 480:
        raise PlanError("width must be at least 480")

    pairs = _event_pairs(lanes)
    if not pairs:
        raise PlanError("no events to draw")

    starts = []
    ends = []
    for _, event in pairs:
        try:
            start = parse_time(event["start"])
            end = parse_time(event["end"])
        except KeyError as exc:
            raise PlanError(f"event is missing {exc.args[0]!r}") from exc
        if end < start:
            raise PlanError(f"event '{event.get('label', '')}' ends before it starts")
        starts.append(start)
        ends.append(end)

    start = parse_time(plan["start"]) if plan.get("start") else min(starts)
    end = parse_time(plan["end"]) if plan.get("end") else max(ends)
    if end <= start:
        raise PlanError("timeline end must be after its start")

    left, right, top = 150, 24, 54
    lane_height = 36
    inner = width - left - right

    chart = Chart(
        title=str(plan.get("title") or "Timeline"),
        start=start,
        end=end,
        lanes=[str(lane.get("name") or f"lane-{index}") for index, lane in enumerate(lanes)],
        width=width,
        height=top + lane_height * len(lanes) + 24,
    )

    total = (end - start).total_seconds()

    def x_of(moment: datetime) -> float:
        ratio = (moment - start).total_seconds() / total
        return left + max(0.0, min(1.0, ratio)) * inner

    for lane_index, lane in enumerate(lanes):
        lane_name = chart.lanes[lane_index]
        row_top = top + lane_index * lane_height + 9
        for event in lane.get("events", []):
            start_at = parse_time(event["start"])
            end_at = parse_time(event["end"])
            if start_at < start or end_at > end:
                chart.warnings.append(
                    f"{lane_name}/{event.get('label', '')} is clipped to the axis"
                )
            start_at = max(start, min(end, start_at))
            end_at = max(start, min(end, end_at))
            x0, x1 = x_of(start_at), x_of(end_at)
            chart.bars.append(Bar(
                lane=lane_name,
                label=str(event.get("label") or "event"),
                start=start_at,
                end=end_at,
                status=str(event.get("status") or "info"),
                x=round(x0, 2),
                y=row_top,
                width=round(max(2.0, x1 - x0), 2),
            ))

    tick_count = 5
    for index in range(tick_count + 1):
        moment = start + timedelta(seconds=total * index / tick_count)
        chart.ticks.append(Tick(
            x=round(x_of(moment), 2),
            label=moment.strftime("%H:%M"),
        ))
    return chart


def render_svg(chart: Chart) -> str:
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{chart.width}" height="{chart.height}" '
        f'viewBox="0 0 {chart.width} {chart.height}" role="img" '
        f'aria-label="{escape(chart.title)}">',
        "<style>"
        "text{font-family:-apple-system,Segoe UI,Roboto,sans-serif}"
        ".t{font-size:16px;font-weight:600;fill:#1f2933}"
        ".l{font-size:12px;fill:#3e4c59}"
        ".a{font-size:10px;fill:#7b8794}"
        ".b{font-size:10px;fill:#fff}"
        "</style>",
        f'<rect width="{chart.width}" height="{chart.height}" fill="#ffffff"/>',
        f'<text class="t" x="16" y="28">{escape(chart.title)}</text>',
    ]

    for tick in chart.ticks:
        lines.append(
            f'<line x1="{tick.x}" y1="44" x2="{tick.x}" y2="{chart.height - 18}" '
            'stroke="#e4e7eb" stroke-width="1"/>'
        )
        lines.append(f'<text class="a" x="{tick.x}" y="{chart.height - 6}" text-anchor="middle">'
                     f"{escape(tick.label)}</text>")

    for index, lane in enumerate(chart.lanes):
        y = 54 + index * 36
        lines.append(f'<text class="l" x="16" y="{y + 22}">{escape(lane)}</text>')
        lines.append(f'<line x1="150" y1="{y + 33}" x2="{chart.width - 24}" y2="{y + 33}" '
                     'stroke="#f0f2f4" stroke-width="1"/>')

    for bar in chart.bars:
        colour = PALETTE.get(bar.status, DEFAULT_COLOUR)
        tooltip = f"{bar.label} ({bar.start.strftime('%H:%M')}–{bar.end.strftime('%H:%M')}, {bar.status})"
        lines.append(
            f'<g><title>{escape(tooltip)}</title>'
            f'<rect x="{bar.x}" y="{bar.y}" width="{bar.width}" height="18" rx="3" fill="{colour}"/>'
        )
        if bar.width >= 56:
            lines.append(f'<text class="b" x="{round(bar.x + 4, 2)}" y="{bar.y + 13}">'
                         f"{escape(bar.label)}</text>")
        else:
            lines.append(f'<text class="a" x="{round(bar.x + bar.width + 4, 2)}" y="{bar.y + 13}">'
                         f"{escape(bar.label)}</text>")
        lines.append("</g>")

    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def load_plan(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def demo_plan() -> dict:
    return {
        "title": "Release 2026-11-15",
        "start": "2026-11-15T09:00:00Z",
        "end": "2026-11-15T13:00:00Z",
        "lanes": [
            {"name": "API", "events": [
                {"label": "build", "start": "2026-11-15T09:00:00Z", "end": "2026-11-15T09:40:00Z", "status": "ok"},
                {"label": "migrate", "start": "2026-11-15T09:40:00Z", "end": "2026-11-15T10:05:00Z", "status": "warn"},
                {"label": "deploy", "start": "2026-11-15T10:05:00Z", "end": "2026-11-15T10:30:00Z", "status": "fail"},
            ]},
            {"name": "Web", "events": [
                {"label": "bundle", "start": "2026-11-15T09:10:00Z", "end": "2026-11-15T09:50:00Z", "status": "ok"},
                {"label": "upload", "start": "2026-11-15T09:50:00Z", "end": "2026-11-15T10:15:00Z", "status": "ok"},
                {"label": "smoke", "start": "2026-11-15T10:40:00Z", "end": "2026-11-15T11:10:00Z", "status": "info"},
            ]},
        ],
    }
