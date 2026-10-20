"""Synthetic boundary regressions for issue #11; no providers or private state."""

import json
import logging
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from src.classification import classifier
from src.finance import event_extractor
from src.medical import case_tracker
from src.outputs import draft_generator
from src.summaries import weekly_summary
from src.utils.logger import JsonFormatter


def client_with_text(text):
    return SimpleNamespace(
        messages=SimpleNamespace(
            create=lambda **kwargs: SimpleNamespace(content=[SimpleNamespace(text=text)])
        )
    )


PARSERS = [
    classifier.classify_by_llm,
    case_tracker.extract_case_fields,
    draft_generator.draft_followup_email,
]


@pytest.mark.parametrize("parse", PARSERS)
@pytest.mark.parametrize("error_type", [RuntimeError, TypeError, ValueError, MemoryError])
def test_unexpected_json_decoder_failures_propagate(monkeypatch, parse, error_type):
    # A broad catch turns decoder defects/resource failures into plausible domain output.
    error = error_type("synthetic decoder failure")

    def fail(text):
        raise error

    monkeypatch.setattr(json, "loads", fail)
    with pytest.raises(error_type) as caught:
        parse({}, client_with_text("{}"))
    assert caught.value is error


@pytest.mark.parametrize(
    ("parse", "text", "expected"),
    [
        (
            classifier.classify_by_llm,
            '{"label":"synthetic"}',
            {"label": "synthetic", "method": "llm"},
        ),
        (
            classifier.classify_by_llm,
            "invalid",
            {
                "label": "BC/misc/unclassified",
                "category": "unknown",
                "action": "label",
                "confidence": 0.3,
                "method": "llm",
            },
        ),
        (case_tracker.extract_case_fields, '{"insurer":"synthetic"}', {"insurer": "synthetic"}),
        (case_tracker.extract_case_fields, "invalid", {"parse_error": "invalid"}),
        (draft_generator.draft_followup_email, '{"subject":"synthetic"}', {"subject": "synthetic"}),
        (
            draft_generator.draft_followup_email,
            "invalid",
            {"subject": "Seguimiento reembolso", "body": "invalid", "to": "", "parse_error": True},
        ),
    ],
)
def test_expected_json_results_remain_compatible(parse, text, expected):
    assert parse({}, client_with_text(text)) == expected


class UTCClock(datetime):
    """Local and legacy clocks deliberately disagree with the UTC oracle."""

    @classmethod
    def now(cls, tz=None):
        if tz is None:
            return cls(2026, 11, 1, 23, 30)
        assert tz == UTC
        return cls(2026, 11, 2, 0, 30, 45, 123456, tzinfo=UTC)

    @classmethod
    def utcnow(cls):
        pytest.fail("use an explicitly aware UTC clock before legacy serialization")


@pytest.mark.parametrize(
    ("module", "make", "fields"),
    [
        (event_extractor, lambda: event_extractor.create_event({}, {}), ["created_at"]),
        (
            case_tracker,
            lambda: case_tracker.create_case({}, {"insurer": "synthetic"}),
            ["created_at", "updated_at"],
        ),
    ],
)
def test_record_timestamps_keep_legacy_naive_utc_strings(monkeypatch, module, make, fields):
    monkeypatch.setattr(module, "datetime", UTCClock)
    record = make()
    for field in fields:
        assert record[field] == "2026-11-02T00:30:45.123456"
        # Existing naive date arithmetic must remain legal at this legacy boundary.
        assert datetime.fromisoformat(record[field]) - datetime(2026, 11, 2) == timedelta(
            minutes=30, seconds=45, microseconds=123456
        )


def test_logger_keeps_legacy_naive_utc_string(monkeypatch):
    from src.utils import logger

    monkeypatch.setattr(logger, "datetime", UTCClock)
    record = logging.LogRecord("synthetic", logging.INFO, "", 1, "hello", (), None)
    assert json.loads(JsonFormatter().format(record)) == {
        "ts": "2026-11-02T00:30:45.123456",
        "level": "INFO",
        "logger": "synthetic",
        "msg": "hello",
    }


def test_week_start_uses_utc_day_not_local_day(monkeypatch):
    monkeypatch.setattr(weekly_summary, "datetime", UTCClock)
    assert weekly_summary.collect_weekly_data([], 0, 0)["week_start"] == "2026-11-02"


def test_monthly_cli_default_uses_utc_month(monkeypatch):
    import sys

    from src import main

    months = []
    monkeypatch.setattr(sys, "argv", ["bc", "--run", "monthly"])
    monkeypatch.setattr(main, "load_config", dict)
    monkeypatch.setattr(main, "build_anthropic_client", lambda cfg: None)
    monkeypatch.setattr(main, "run_monthly", lambda cfg, client, month: months.append(month))

    class MonthClock(UTCClock):
        @classmethod
        def now(cls, tz=None):
            if tz is None:
                return cls(2026, 10, 31, 23, 30)
            assert tz == UTC
            return cls(2026, 11, 1, 0, 30, tzinfo=UTC)

    import datetime as datetime_module

    monkeypatch.setattr(datetime_module, "datetime", MonthClock)
    main.main()
    assert months == ["2026-11"]
