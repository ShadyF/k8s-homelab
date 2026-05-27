#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


DEFAULT_STATE_FILE = "/opt/data/events/seen-events.jsonl"
REQUIRED_FIELDS = ("title", "date", "url")
TRACKING_QUERY_KEYS = {"fbclid", "gclid", "mc_cid", "mc_eid", "igshid"}


def _normalize_text(value: Any) -> str:
    return " ".join(str(value).split()).casefold()


def _normalize_url(value: Any) -> str:
    raw = str(value).strip()
    parts = urlsplit(raw)
    scheme = parts.scheme.lower()
    netloc = parts.netloc.lower()

    path = parts.path or ""
    if path == "/":
        normalized_path = "/"
    else:
        normalized_path = path.rstrip("/")

    filtered_query = [
        (key, val)
        for key, val in parse_qsl(parts.query, keep_blank_values=True)
        if key.casefold() not in TRACKING_QUERY_KEYS and not key.casefold().startswith("utm_")
    ]
    query = urlencode(filtered_query, doseq=True)
    return urlunsplit((scheme, netloc, normalized_path, query, ""))


def make_keys(event: dict[str, Any]) -> dict[str, str]:
    normalized_url = _normalize_url(event["url"])
    normalized_title = _normalize_text(event["title"])
    normalized_date = _normalize_text(event["date"])

    url_title_date_canonical = "\u241f".join(
        ("url_title_date", normalized_url, normalized_title, normalized_date)
    )
    title_date_canonical = "\u241f".join(("title_date", normalized_title, normalized_date))

    return {
        "url_title_date": "url_title_date:" + hashlib.sha256(
            url_title_date_canonical.encode("utf-8")
        ).hexdigest(),
        "title_date": "title_date:" + hashlib.sha256(title_date_canonical.encode("utf-8")).hexdigest(),
    }


def _load_state_keys(state_file: Path) -> set[str]:
    seen: set[str] = set()
    if not state_file.exists():
        return seen

    with state_file.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError:
                continue
            if not isinstance(record, dict):
                continue
            keys = record.get("keys")
            if not isinstance(keys, list):
                continue
            for key in keys:
                if isinstance(key, str):
                    seen.add(key)
    return seen


def _missing_field_reason(event: Any) -> str | None:
    if not isinstance(event, dict):
        return f"missing required field: {REQUIRED_FIELDS[0]}"

    for field in REQUIRED_FIELDS:
        value = event.get(field)
        if value is None:
            return f"missing required field: {field}"
        if isinstance(value, str):
            if not value.strip():
                return f"missing required field: {field}"
        else:
            if not str(value).strip():
                return f"missing required field: {field}"
    return None


def _invalid_item(event: Any, reason: str) -> dict[str, Any]:
    if isinstance(event, dict):
        invalid = dict(event)
    else:
        invalid = {"event": event}
    invalid["reason"] = reason
    return invalid


def _read_payload() -> list[Any]:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(json.dumps({"error": f"invalid JSON: {exc.msg}"}, separators=(",", ":")), file=sys.stderr)
        raise SystemExit(1)

    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("events"), list):
        return payload["events"]

    print(
        json.dumps(
            {"error": "top-level JSON must be a list or an object with an 'events' list"},
            separators=(",", ":"),
        ),
        file=sys.stderr,
    )
    raise SystemExit(1)


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def cmd_check(state_file: Path) -> int:
    seen_keys = _load_state_keys(state_file)
    new_events: list[dict[str, Any]] = []
    seen_events: list[dict[str, Any]] = []
    invalid_events: list[dict[str, Any]] = []

    for event in _read_payload():
        reason = _missing_field_reason(event)
        if reason is not None:
            invalid_events.append(_invalid_item(event, reason))
            continue

        keys = make_keys(event)
        if keys["url_title_date"] in seen_keys or keys["title_date"] in seen_keys:
            seen_events.append(event)
        else:
            seen_keys.add(keys["url_title_date"])
            seen_keys.add(keys["title_date"])
            new_events.append(event)

    print(json.dumps({"new": new_events, "seen": seen_events, "invalid": invalid_events}, separators=(",", ":")))
    return 0


def cmd_record(state_file: Path) -> int:
    events = _read_payload()
    valid_records: list[dict[str, Any]] = []
    invalid_count = 0
    seen_keys = _load_state_keys(state_file)

    for event in events:
        reason = _missing_field_reason(event)
        if reason is not None:
            invalid_count += 1
            continue
        if not isinstance(event, dict):
            continue
        keys = make_keys(event)
        if keys["url_title_date"] in seen_keys or keys["title_date"] in seen_keys:
            continue
        seen_keys.add(keys["url_title_date"])
        seen_keys.add(keys["title_date"])
        valid_records.append(
            {"recorded_at": _utc_timestamp(), "keys": [keys["url_title_date"], keys["title_date"]], "event": event}
        )

    state_file.parent.mkdir(parents=True, exist_ok=True)
    with state_file.open("a", encoding="utf-8") as handle:
        for record in valid_records:
            handle.write(json.dumps(record, separators=(",", ":")) + "\n")

    print(json.dumps({"recorded": len(valid_records), "invalid": invalid_count}, separators=(",", ":")))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="events_seen")
    parser.add_argument("command", choices=("check", "record"))
    parser.add_argument("--state-file", default=DEFAULT_STATE_FILE)
    args = parser.parse_args(argv)

    state_file = Path(args.state_file)
    if args.command == "check":
        return cmd_check(state_file)
    if args.command == "record":
        return cmd_record(state_file)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
