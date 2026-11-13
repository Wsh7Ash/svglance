import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest

from svglance import PlanError, build_chart, demo_plan, parse_time, render_svg
from svglance.cli import main


def plan_with(events, **extra):
    data = {
        "title": "Test <Timeline>",
        "start": "2026-11-15T09:00:00Z",
        "end": "2026-11-15T11:00:00Z",
        "lanes": [{"name": "API", "events": events}],
    }
    data.update(extra)
    return data


EVENTS = [
    {"label": "build", "start": "2026-11-15T09:00:00Z", "end": "2026-11-15T09:30:00Z", "status": "ok"},
    {"label": "deploy", "start": "2026-11-15T10:00:00Z", "end": "2026-11-15T10:30:00Z", "status": "fail"},
]


def test_parse_time_handles_z_and_naive():
    assert parse_time("2026-11-15T09:00:00Z").tzinfo is not None
    assert parse_time("2026-11-15T09:00:00").tzinfo is not None
    with pytest.raises(PlanError):
        parse_time("tomorrow")


def test_layout_positions_and_ticks():
    chart = build_chart(plan_with(EVENTS), width=960)
    assert len(chart.bars) == 2
    first, second = chart.bars
    assert first.x < second.x
    assert first.width > 0
    assert len(chart.ticks) == 6
    assert chart.ticks[0].label == "09:00"
    assert chart.ticks[-1].label == "11:00"
    assert chart.height > 100


def test_svg_is_deterministic_and_escapes_text():
    chart = build_chart(plan_with(EVENTS))
    first = render_svg(chart)
    second = render_svg(chart)
    assert first == second
    assert first.startswith("<svg") and first.rstrip().endswith("</svg>")
    assert "Test &lt;Timeline&gt;" in first
    assert "<Timeline>" not in first
    assert first.count("<rect ") >= 3  # background + two bars


def test_events_are_clipped_with_warning():
    events = [{"label": "early", "start": "2026-11-15T08:00:00Z",
               "end": "2026-11-15T12:00:00Z", "status": "info"}]
    chart = build_chart(plan_with(events))
    assert chart.warnings and "clipped" in chart.warnings[0]
    assert chart.bars[0].x >= 150
    assert chart.bars[0].x + chart.bars[0].width <= chart.width - 24


def test_invalid_plans():
    with pytest.raises(PlanError):
        build_chart({"lanes": []})
    with pytest.raises(PlanError):
        build_chart({"lanes": [{"name": "x", "events": []}]})
    with pytest.raises(PlanError):
        build_chart(plan_with([{"label": "a", "start": "2026-11-15T10:00:00Z",
                                "end": "2026-11-15T09:00:00Z"}]))
    with pytest.raises(PlanError):
        build_chart(plan_with([{"label": "a"}]))


def test_demo_plan_renders():
    chart = build_chart(demo_plan())
    assert len(chart.lanes) == 2
    assert len(chart.bars) == 6
    assert chart.warnings == []


def test_cli_render_demo_and_errors(tmp_path, capsys):
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan_with(EVENTS)), encoding="utf-8")
    assert main(["render", str(path), "--out", str(tmp_path / "out.svg")]) == 0
    svg = (tmp_path / "out.svg").read_text(encoding="utf-8")
    assert svg.count("<rect ") >= 3
    capsys.readouterr()

    assert main(["render", str(path)]) == 0
    assert capsys.readouterr().out.startswith("<svg")

    assert main(["demo", "--out", str(tmp_path / "demo.svg")]) == 0

    bad = tmp_path / "bad.json"
    bad.write_text("{oops", encoding="utf-8")
    assert main(["render", str(bad)]) == 2
    assert main(["render", str(tmp_path / "missing.json")]) == 2
