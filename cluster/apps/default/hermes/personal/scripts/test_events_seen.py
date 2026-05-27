import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).with_name("events_seen.py")


def expected_key(kind, *canonical_parts):
    canonical = "\u241f".join((kind, *canonical_parts))
    return f"{kind}:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


def load_module():
    spec = importlib.util.spec_from_file_location("events_seen", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class EgyptEventsSeenTests(unittest.TestCase):
    def test_make_keys_normalizes_tracking_urls_and_title_spacing(self):
        module = load_module()
        canonical_event = {
            "title": "Andrea Bocelli Live in Cairo",
            "date": "2026-06-05",
            "url": "https://www.livenation.me/show/1652077",
        }
        messy_event = {
            "title": "  Andrea   Bocelli Live in Cairo  ",
            "date": "2026-06-05",
            "url": "https://www.livenation.me/show/1652077?utm_source=ig#tickets",
        }

        canonical_keys = module.make_keys(canonical_event)
        messy_keys = module.make_keys(messy_event)

        self.assertEqual(messy_keys, canonical_keys)
        self.assertEqual(
            messy_keys["url_title_date"],
            expected_key(
                "url_title_date",
                "https://www.livenation.me/show/1652077",
                "andrea bocelli live in cairo",
                "2026-06-05",
            ),
        )
        self.assertEqual(
            messy_keys["title_date"],
            expected_key(
                "title_date",
                "andrea bocelli live in cairo",
                "2026-06-05",
            ),
        )

    def test_check_marks_new_duplicate_and_invalid_events(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "seen-events.jsonl"
            state_file.write_text(
                json.dumps(
                    {
                        "keys": [
                            expected_key(
                                "url_title_date",
                                "https://zawyacinema.com/calendar/film-night",
                                "previously reported film night",
                                "2026-06-10",
                            ),
                            expected_key(
                                "title_date",
                                "previously reported film night",
                                "2026-06-10",
                            ),
                        ],
                        "event": {
                            "title": "Previously Reported Film Night",
                            "date": "2026-06-10",
                            "url": "https://zawyacinema.com/calendar/film-night",
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            payload = [
                {
                    "title": "Previously Reported Film Night",
                    "date": "2026-06-10",
                    "url": "https://zawyacinema.com/calendar/film-night?utm_campaign=test",
                    "venue": "Zawya",
                },
                {
                    "title": "Previously Reported Film Night",
                    "date": "2026-06-10",
                    "url": "https://example.com/duplicate-writeup",
                    "venue": "Zawya",
                },
                {
                    "title": "AUC Public Talk",
                    "date": "2026-06-12",
                    "url": "https://happening.aucegypt.edu/events/public-talk",
                    "venue": "AUC Tahrir",
                },
                {
                    "title": "No Date Event",
                    "url": "https://example.com/no-date",
                    "venue": "Unknown",
                },
            ]

            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "check", "--state-file", str(state_file)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                check=True,
            )

            output = json.loads(result.stdout)
            self.assertEqual([event["title"] for event in output["new"]], ["AUC Public Talk"])
            self.assertEqual(
                [event["url"] for event in output["seen"]],
                [
                    "https://zawyacinema.com/calendar/film-night?utm_campaign=test",
                    "https://example.com/duplicate-writeup",
                ],
            )
            self.assertEqual(len(output["invalid"]), 1)
            self.assertEqual(output["invalid"][0]["title"], "No Date Event")
            self.assertEqual(output["invalid"][0]["reason"], "missing required field: date")

    def test_check_suppresses_same_batch_duplicates(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "seen-events.jsonl"
            payload = [
                {
                    "title": "Same Title Event",
                    "date": "2026-07-01",
                    "url": "https://example.com/event-a",
                },
                {
                    "title": "Same Title Event",
                    "date": "2026-07-01",
                    "url": "https://example.com/event-b",
                },
            ]

            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "check", "--state-file", str(state_file)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                check=True,
            )

            output = json.loads(result.stdout)
            self.assertEqual([event["url"] for event in output["new"]], ["https://example.com/event-a"])
            self.assertEqual([event["url"] for event in output["seen"]], ["https://example.com/event-b"])
            self.assertEqual(output["invalid"], [])

    def test_record_appends_only_valid_events_and_check_suppresses_them(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "seen-events.jsonl"
            payload = [
                {
                    "title": "TicketsMarche Theatre Night",
                    "date": "2026-06-20",
                    "url": "https://www.ticketsmarche.com/event/theatre-night",
                    "venue": "Cairo",
                    "category": "Culture",
                },
                {
                    "title": "Missing URL",
                    "date": "2026-06-20",
                    "venue": "Cairo",
                },
            ]

            record = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "record", "--state-file", str(state_file)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                check=True,
            )
            record_output = json.loads(record.stdout)

            self.assertEqual(record_output["recorded"], 1)
            self.assertEqual(record_output["invalid"], 1)
            self.assertTrue(state_file.exists())

            check = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "check", "--state-file", str(state_file)],
                input=json.dumps(payload[:1]),
                text=True,
                capture_output=True,
                check=True,
            )
            check_output = json.loads(check.stdout)

            self.assertEqual(check_output["new"], [])
            self.assertEqual(len(check_output["seen"]), 1)
            self.assertEqual(check_output["seen"][0]["title"], "TicketsMarche Theatre Night")
            self.assertEqual(
                check_output["seen"][0]["url"],
                "https://www.ticketsmarche.com/event/theatre-night",
            )

    def test_record_is_idempotent_for_repeated_events(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "seen-events.jsonl"
            payload = [
                {
                    "title": "Idempotent Event",
                    "date": "2026-08-15",
                    "url": "https://example.com/idempotent-event",
                }
            ]

            first = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "record", "--state-file", str(state_file)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                check=True,
            )
            second = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "record", "--state-file", str(state_file)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                check=True,
            )

            first_output = json.loads(first.stdout)
            second_output = json.loads(second.stdout)

            self.assertEqual(first_output["recorded"], 1)
            self.assertEqual(second_output["recorded"], 0)
            self.assertEqual(first_output["invalid"], 0)
            self.assertEqual(second_output["invalid"], 0)
            self.assertTrue(state_file.exists())
            self.assertEqual(len(state_file.read_text(encoding="utf-8").splitlines()), 1)


if __name__ == "__main__":
    unittest.main()
