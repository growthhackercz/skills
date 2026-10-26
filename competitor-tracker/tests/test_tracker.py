#!/usr/bin/env python3
"""Offline regression coverage for competitor-tracker's durable workflow."""

import contextlib
import io
import json
import os
import pathlib
import sys
import tempfile
import types
import unittest
from unittest import mock

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
SKILL_ROOT = HERE.parent
SCRIPTS = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import board  # noqa: E402
import provider_ads  # noqa: E402
import provider_extras  # noqa: E402
import tracker  # noqa: E402


def _quiet_call(func, *args, **kwargs):
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        result = func(*args, **kwargs)
    return result, stdout.getvalue(), stderr.getvalue()


class TrackerWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name) / "competitors"
        self.fixture_dir = pathlib.Path(self.tmp.name) / "fixtures"
        self.fixture_dir.mkdir()
        _quiet_call(
            tracker.cmd_init,
            types.SimpleNamespace(
                root=str(self.root),
                country="CZ",
                cap=50,
                apify_monthly_usd=5,
            ),
        )

    def tearDown(self):
        self.tmp.cleanup()

    def add_brand(self, **overrides):
        values = {
            "root": str(self.root),
            "name": "Testovací konkurent",
            "query": "",
            "ico": "",
            "youtube": "",
            "facebook": "",
            "instagram": "",
            "linkedin": "",
            "maps": "",
            "web": "",
            "note": "",
            "find_page": False,
            "no_find_page": False,
        }
        values.update(overrides)
        return _quiet_call(tracker.cmd_add_brand, types.SimpleNamespace(**values))

    def patrol_args(self, **overrides):
        values = {
            "root": str(self.root),
            "brand": "",
            "cap": 0,
            "country": "",
            "fixture_dir": "",
            "force": False,
            "dry_run": False,
            "deep": 10,
            "confirm_paid": False,
        }
        values.update(overrides)
        return types.SimpleNamespace(**values)

    def latest_summary(self):
        paths = sorted((self.root / "digest").glob("*/summary.json"))
        self.assertTrue(paths)
        return json.loads(paths[-1].read_text(encoding="utf-8"))

    def test_missing_key_is_visible_and_never_quiet_or_complete(self):
        self.add_brand()
        with mock.patch.object(provider_ads, "token", return_value=""):
            _quiet_call(tracker.cmd_patrol, self.patrol_args())

        summary = self.latest_summary()
        self.assertFalse(summary["complete"])
        self.assertFalse(summary["quiet"])
        self.assertEqual(summary["paid_sources"]["skip_code"], "missing_credential")
        self.assertIn("Placené zdroje přeskočeny", summary["brands"][0]["events"][-1]["note"])
        html = pathlib.Path(summary["board"]).read_text(encoding="utf-8")
        self.assertIn("Obchůzka není úplná", html)
        self.assertNotIn("Tichý týden", html)

    def test_exhausted_budget_has_exact_reason_and_force_does_not_bypass(self):
        self.add_brand()
        with mock.patch.object(provider_ads, "token", return_value="configured"), \
                mock.patch.object(
                    provider_ads,
                    "monthly_usage_usd",
                    return_value={"used": 5.0, "apify_max": 10.0},
                ), \
                mock.patch.object(provider_ads, "pull") as pull:
            _quiet_call(tracker.cmd_patrol, self.patrol_args(force=True))

        pull.assert_not_called()
        summary = self.latest_summary()
        self.assertFalse(summary["complete"])
        self.assertEqual(summary["paid_sources"]["skip_code"], "budget_exhausted")
        self.assertIn("dosáhla bezpečnostního prahu", summary["paid_sources"]["skip_reason"])
        self.assertNotIn("chybí APIFY_API_KEY", summary["paid_sources"]["skip_reason"])

    def test_unavailable_usage_fails_closed(self):
        self.add_brand()
        with mock.patch.object(provider_ads, "token", return_value="configured"), \
                mock.patch.object(provider_ads, "monthly_usage_usd", return_value=None), \
                mock.patch.object(provider_ads, "pull") as pull:
            _quiet_call(tracker.cmd_patrol, self.patrol_args())

        pull.assert_not_called()
        summary = self.latest_summary()
        self.assertFalse(summary["complete"])
        self.assertEqual(summary["paid_sources"]["skip_code"], "usage_unavailable")

    def test_valid_budget_without_explicit_confirmation_still_fails_closed(self):
        self.add_brand()
        with mock.patch.object(provider_ads, "token", return_value="configured"), \
                mock.patch.object(
                    provider_ads,
                    "monthly_usage_usd",
                    return_value={"used": 1.0, "apify_max": 20.0},
                ), \
                mock.patch.object(provider_ads, "pull") as pull:
            _quiet_call(tracker.cmd_patrol, self.patrol_args())

        pull.assert_not_called()
        summary = self.latest_summary()
        self.assertEqual(summary["paid_sources"]["skip_code"], "approval_required")
        self.assertFalse(summary["complete"])

    def test_confirmed_paid_patrol_reaches_providers_when_budget_is_valid(self):
        self.add_brand()
        with mock.patch.object(provider_ads, "token", return_value="configured"), \
                mock.patch.object(
                    provider_ads,
                    "monthly_usage_usd",
                    return_value={"used": 1.0, "apify_max": 20.0},
                ), \
                mock.patch.object(provider_ads, "pull", return_value=[]) as pull, \
                mock.patch.object(provider_extras, "google_ads", return_value={}), \
                mock.patch.object(provider_extras, "linkedin_ads", return_value={}), \
                mock.patch.object(provider_extras, "reviews", return_value=None) as reviews:
            _quiet_call(tracker.cmd_patrol, self.patrol_args(confirm_paid=True))

        pull.assert_called_once()
        reviews.assert_not_called()
        summary = self.latest_summary()
        self.assertTrue(summary["paid_sources"]["enabled"])
        self.assertTrue(summary["complete"])

    def test_reviews_run_only_for_a_confirmed_maps_place(self):
        self.add_brand(maps="confirmed-place-id")
        with mock.patch.object(provider_ads, "token", return_value="configured"), \
                mock.patch.object(
                    provider_ads,
                    "monthly_usage_usd",
                    return_value={"used": 1.0, "apify_max": 20.0},
                ), \
                mock.patch.object(provider_ads, "pull", return_value=[]), \
                mock.patch.object(provider_extras, "google_ads", return_value={}), \
                mock.patch.object(provider_extras, "linkedin_ads", return_value={}), \
                mock.patch.object(provider_extras, "reviews", return_value=None) as reviews:
            _quiet_call(tracker.cmd_patrol, self.patrol_args(confirm_paid=True, deep=0))

        reviews.assert_called_once_with(
            "Testovací konkurent",
            location="Czechia",
            place="confirmed-place-id",
            web="",
        )

    def test_actor_request_caps_returned_and_chargeable_items(self):
        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self, _limit):
                return b"[]"

        with mock.patch.object(provider_ads, "token", return_value="configured"), \
                mock.patch.object(provider_ads.urllib.request, "urlopen", return_value=Response()) as urlopen:
            self.assertEqual(provider_ads._run_actor("owner~actor", {}, 7, 10), [])

        request = urlopen.call_args.args[0]
        query = provider_ads.urllib.parse.parse_qs(provider_ads.urllib.parse.urlsplit(request.full_url).query)
        self.assertEqual(query["limit"], ["7"])
        self.assertEqual(query["maxItems"], ["7"])
        self.assertNotIn("token", query)

    def test_unmatched_advertisers_do_not_create_false_empty_baseline(self):
        self.add_brand()
        raw = [{
            "ad_archive_id": "other",
            "start_date": 1_700_000_000,
            "snapshot": {"page_name": "Completely Different", "body": {"text": "Cizí reklama"}},
        }]
        with mock.patch.object(provider_ads, "token", return_value="configured"), \
                mock.patch.object(
                    provider_ads,
                    "monthly_usage_usd",
                    return_value={"used": 1.0, "apify_max": 20.0},
                ), \
                mock.patch.object(provider_ads, "pull", return_value=raw), \
                mock.patch.object(provider_extras, "google_ads", return_value={}), \
                mock.patch.object(provider_extras, "linkedin_ads", return_value={}), \
                mock.patch.object(provider_extras, "reviews", return_value=None):
            _quiet_call(tracker.cmd_patrol, self.patrol_args(confirm_paid=True, deep=0))

        summary = self.latest_summary()
        self.assertFalse(summary["complete"])
        self.assertIn("SOURCE_STALE", {event["type"] for event in summary["brands"][0]["events"]})
        snapshots = list((self.root / "history/testovaci-konkurent").glob("ads-*.json"))
        self.assertEqual(snapshots, [])

    def test_failed_detail_enrichment_marks_partial_result_incomplete(self):
        self.add_brand()
        raw = [{
            "ad_archive_id": "one",
            "start_date": 1_700_000_000,
            "snapshot": {"page_name": "Testovací konkurent", "body": {"text": "Nabídka"}},
        }]
        with mock.patch.object(provider_ads, "token", return_value="configured"), \
                mock.patch.object(
                    provider_ads,
                    "monthly_usage_usd",
                    return_value={"used": 1.0, "apify_max": 20.0},
                ), \
                mock.patch.object(provider_ads, "pull", return_value=raw), \
                mock.patch.object(
                    provider_ads,
                    "enrich_details",
                    side_effect=provider_ads.SourceError("detail unavailable"),
                ), \
                mock.patch.object(provider_extras, "google_ads", return_value={}), \
                mock.patch.object(provider_extras, "linkedin_ads", return_value={}), \
                mock.patch.object(provider_extras, "reviews", return_value=None):
            _quiet_call(tracker.cmd_patrol, self.patrol_args(confirm_paid=True))

        summary = self.latest_summary()
        self.assertFalse(summary["complete"])
        details = [
            event for event in summary["brands"][0]["events"]
            if event["type"] == "SOURCE_UNAVAILABLE" and event["note"].startswith("Detail reklam:")
        ]
        self.assertEqual(len(details), 1)

    def test_old_watchlist_without_budget_uses_safe_default(self):
        watchlist_path = self.root / "watchlist.json"
        watchlist = json.loads(watchlist_path.read_text(encoding="utf-8"))
        watchlist["caps"].pop("apify_monthly_usd")
        tracker._save(str(watchlist_path), watchlist)
        self.add_brand()

        with mock.patch.object(provider_ads, "token", return_value="configured"), \
                mock.patch.object(
                    provider_ads,
                    "monthly_usage_usd",
                    return_value={"used": 1.0, "apify_max": 20.0},
                ):
            _, output, _ = _quiet_call(tracker.cmd_patrol, self.patrol_args(dry_run=True))

        payload = json.loads(output)
        self.assertEqual(payload["rozpocet"]["limit_usd"], tracker.DEFAULT_APIFY_MONTHLY_USD)
        self.assertEqual(payload["rozpocet"]["stav"], "v pořádku")

    def test_non_positive_and_non_finite_budgets_are_rejected(self):
        for value in (0, -1, float("nan"), float("inf")):
            with self.subTest(value=value), self.assertRaises(SystemExit):
                _quiet_call(
                    tracker.cmd_set_budget,
                    types.SimpleNamespace(root=str(self.root), usd=value),
                )

    def test_paid_result_caps_are_bounded(self):
        self.add_brand()
        for cap in (-1, 9, 101, 1_000_000):
            with self.subTest(cap=cap), self.assertRaises(SystemExit):
                _quiet_call(tracker.cmd_patrol, self.patrol_args(cap=cap, dry_run=True))
        for deep in (-1, 1, 9, 26, 1_000_000):
            with self.subTest(deep=deep), self.assertRaises(SystemExit):
                _quiet_call(tracker.cmd_patrol, self.patrol_args(deep=deep, dry_run=True))

    def test_add_brand_never_runs_paid_lookup_without_opt_in(self):
        with mock.patch.object(provider_ads, "token", return_value="configured"), \
                mock.patch.object(provider_ads, "find_page") as find_page:
            self.add_brand()
        find_page.assert_not_called()

    def test_brand_identity_is_single_line_and_czech_ico_is_validated(self):
        self.add_brand(name="  Testovací\nkonkurent  ")
        watchlist = tracker._watchlist(str(self.root))
        self.assertEqual(watchlist["brands"][0]["name"], "Testovací konkurent")

        with tempfile.TemporaryDirectory() as tmp:
            other_root = pathlib.Path(tmp) / "competitors"
            _quiet_call(
                tracker.cmd_init,
                types.SimpleNamespace(root=str(other_root), country="CZ", cap=50, apify_monthly_usd=5),
            )
            with self.assertRaises(SystemExit):
                _quiet_call(
                    tracker.cmd_add_brand,
                    types.SimpleNamespace(
                        root=str(other_root), name="X", query="", ico="123", youtube="",
                        facebook="", instagram="", linkedin="", maps="", web="", note="",
                        find_page=False, no_find_page=False,
                    ),
                )

    def test_paid_add_brand_lookup_requires_explicit_confirmation(self):
        with mock.patch.object(provider_ads, "token", return_value="configured"), \
                mock.patch.object(provider_ads, "find_page") as find_page:
            with self.assertRaises(SystemExit):
                self.add_brand(find_page=True, confirm_paid=False)
        find_page.assert_not_called()

    def test_dry_run_counts_every_configured_primary_and_fallback(self):
        self.add_brand(
            youtube="https://youtube.com/@test",
            facebook="https://facebook.com/test",
            instagram="test",
            linkedin="https://linkedin.com/company/test",
            maps="confirmed-place-id",
        )
        watchlist = tracker._watchlist(str(self.root))
        watchlist["keywords"] = ["test brand"]
        tracker._save(str(self.root / "watchlist.json"), watchlist)
        plan = tracker._paid_call_plan(
            str(self.root),
            watchlist["brands"],
            deep=10,
            watchlist=watchlist,
            today="2026-09-03",
        )
        self.assertEqual(plan["minimum"], 9)
        self.assertEqual(plan["maximum"], 18)
        self.assertEqual({row["source"] for row in plan["sources"]}, {
            "Meta Ad Library",
            "Meta detail",
            "Google Ads Transparency",
            "LinkedIn Ad Library",
            "YouTube",
            "Facebook příspěvky",
            "Instagram příspěvky",
            "LinkedIn příspěvky",
            "Google Maps recenze",
            "Google SERP",
        })

    def test_dry_run_omits_reviews_until_maps_place_is_confirmed(self):
        self.add_brand()
        watchlist = tracker._watchlist(str(self.root))
        plan = tracker._paid_call_plan(
            str(self.root),
            watchlist["brands"],
            deep=0,
            watchlist=watchlist,
            today="2026-09-03",
        )
        self.assertEqual(plan["minimum"], 3)
        self.assertEqual(plan["maximum"], 6)
        self.assertNotIn("Google Maps recenze", {row["source"] for row in plan["sources"]})

    def test_invalid_actor_configuration_disables_paid_sources_but_keeps_free_run(self):
        self.add_brand()
        with mock.patch.dict(os.environ, {"COMP_GOOGLE_ACTORS": "https://evil.test/x"}), \
                mock.patch.object(provider_ads, "token", return_value="configured"), \
                mock.patch.object(
                    provider_ads,
                    "monthly_usage_usd",
                    return_value={"used": 1.0, "apify_max": 20.0},
                ), \
                mock.patch.object(provider_ads, "pull") as pull:
            _quiet_call(tracker.cmd_patrol, self.patrol_args(confirm_paid=True))

        pull.assert_not_called()
        summary = self.latest_summary()
        self.assertEqual(summary["paid_sources"]["skip_code"], "invalid_provider_config")
        self.assertFalse(summary["complete"])

    def test_same_day_repeat_returns_saved_result_without_credential_or_provider_call(self):
        self.add_brand()
        today = tracker._today()
        week = tracker._week()
        tracker._save(str(self.root / "history/testovaci-konkurent" / f"ads-{today}.json"), {
            "date": today,
            "brand": "Testovací konkurent",
            "count": 0,
            "ads": [],
        })
        digest = self.root / "digest" / week
        digest.mkdir(parents=True, exist_ok=True)
        board_path = digest / "index.html"
        board_path.write_text("original-board", encoding="utf-8")
        tracker._save(str(digest / "summary.json"), {
            "week": week,
            "generated": today,
            "board": str(board_path),
            "brands": [{"slug": "testovaci-konkurent", "events": [{"type": "BASELINE"}]}],
            "quiet": False,
            "complete": True,
            "sources_unavailable": [],
            "events_total": 1,
        })

        with mock.patch.object(provider_ads, "token", side_effect=AssertionError("token lookup must not run")), \
                mock.patch.object(provider_ads, "pull", side_effect=AssertionError("provider must not run")):
            _, output, _ = _quiet_call(tracker.cmd_patrol, self.patrol_args())

        payload = json.loads(output)
        self.assertTrue(payload["cached"])
        self.assertTrue(payload["complete"])
        self.assertEqual(board_path.read_text(encoding="utf-8"), "original-board")

    def test_monthly_report_never_calls_incomplete_observation_a_calm_market(self):
        self.add_brand()
        tracker._append_jsonl(str(self.root / "events.jsonl"), [{
            "date": tracker._today(),
            "brand": "testovaci-konkurent",
            "type": "SOURCE_SKIPPED",
            "note": "Placené zdroje přeskočeny: chybí potvrzení.",
        }])
        _, output, _ = _quiet_call(
            tracker.cmd_ceo_report,
            types.SimpleNamespace(root=str(self.root)),
        )
        report_path = pathlib.Path(json.loads(output)["report"])
        report = report_path.read_text(encoding="utf-8")
        self.assertIn("Neúplné kontroly", report)
        self.assertNotIn("trh je klidný", report)

    def test_full_fixture_baseline_and_next_week_diff(self):
        self.add_brand()
        fixture_path = self.fixture_dir / "testovaci-konkurent.json"
        first = [{
            "ad_archive_id": "one",
            "start_date": 1_700_000_000,
            "is_active": True,
            "snapshot": {"page_name": "Testovací konkurent", "body": {"text": "První nabídka"}},
        }]
        second = first + [{
            "ad_archive_id": "two",
            "start_date": 1_700_100_000,
            "is_active": True,
            "snapshot": {"page_name": "Testovací konkurent", "body": {"text": "Nová nabídka"}},
        }]
        tracker._save(str(fixture_path), first)

        with mock.patch.object(tracker, "_today", return_value="2026-09-01"), \
                mock.patch.object(tracker, "_week", return_value="2026-W36"):
            _quiet_call(
                tracker.cmd_patrol,
                self.patrol_args(fixture_dir=str(self.fixture_dir)),
            )

        first_summary = json.loads((self.root / "digest/2026-W36/summary.json").read_text(encoding="utf-8"))
        self.assertIn("BASELINE", {event["type"] for event in first_summary["brands"][0]["events"]})

        tracker._save(str(fixture_path), second)
        with mock.patch.object(tracker, "_today", return_value="2026-09-08"), \
                mock.patch.object(tracker, "_week", return_value="2026-W37"):
            _quiet_call(
                tracker.cmd_patrol,
                self.patrol_args(fixture_dir=str(self.fixture_dir)),
            )

        second_summary = json.loads((self.root / "digest/2026-W37/summary.json").read_text(encoding="utf-8"))
        self.assertTrue(second_summary["complete"])
        self.assertIn("NEW", {event["type"] for event in second_summary["brands"][0]["events"]})


class PersistenceAndRenderingTests(unittest.TestCase):
    def test_source_unavailable_never_renders_quiet_banner(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = pathlib.Path(tmp) / "board.html"
            board.render(
                "2026-W36",
                [{
                    "slug": "x",
                    "name": "X",
                    "active": 0,
                    "oldest": 0,
                    "events": [{"type": "SOURCE_UNAVAILABLE", "note": "Web: nedostupný"}],
                }],
                str(output),
                complete=False,
            )
            html = output.read_text(encoding="utf-8")
        self.assertIn("Obchůzka není úplná", html)
        self.assertIn("zdroj nedostupný", html)
        self.assertNotIn("Tichý týden", html)

    def test_non_advertising_change_never_renders_quiet_banner(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = pathlib.Path(tmp) / "board.html"
            board.render(
                "2026-W36",
                [{
                    "slug": "x",
                    "name": "X",
                    "active": 0,
                    "oldest": 0,
                    "events": [{"type": "REGISTRY_CHANGE", "note": "Změna ve vedení"}],
                }],
                str(output),
                complete=True,
            )
            html = output.read_text(encoding="utf-8")
        self.assertIn("změna v rejstříku", html)
        self.assertNotIn("Tichý týden", html)

    def test_external_links_require_safe_http_url_without_credentials(self):
        self.assertEqual(board._safe("javascript:alert(1)"), "")
        self.assertEqual(board._safe("https://user:pass@example.com/a"), "")
        self.assertEqual(board._safe("httpx://example.com"), "")
        self.assertEqual(board._safe("https://example.com/a"), "https://example.com/a")

    def test_remote_previews_do_not_send_document_referrer(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = pathlib.Path(tmp) / "board.html"
            board.render(
                "2026-W36",
                [{
                    "slug": "x",
                    "name": "X",
                    "active": 1,
                    "oldest": 3,
                    "events": [],
                    "top_creatives": [{
                        "creative_url": "https://cdn.example/image.jpg",
                        "ad_library_url": "https://facebook.com/ads/library/?id=1",
                        "hook": "Test",
                        "days": 3,
                    }],
                }],
                str(output),
                complete=True,
            )
            html = output.read_text(encoding="utf-8")
        self.assertIn('<meta name="referrer" content="no-referrer">', html)
        self.assertIn('referrerpolicy="no-referrer"', html)
        self.assertIn('rel="noopener noreferrer"', html)

    def test_fixture_mode_cannot_target_production_documents(self):
        for root in ("/documents", "/documents/competitors", "/documents/../documents/competitors"):
            with self.subTest(root=root), self.assertRaises(ValueError):
                tracker._validate_fixture_root(root)

    def test_facebook_page_input_is_restricted_to_facebook(self):
        self.assertEqual(
            provider_ads.normalize_facebook_page("12345"),
            ("https://www.facebook.com/12345", "12345"),
        )
        self.assertEqual(
            provider_ads.normalize_facebook_page("@example.brand"),
            ("https://www.facebook.com/example.brand", ""),
        )
        with self.assertRaises(ValueError):
            provider_ads.normalize_facebook_page("https://example.com/not-facebook")
        with self.assertRaises(ValueError):
            provider_ads.normalize_facebook_page("https://user:pass@facebook.com/page")

    def test_corrupt_json_is_not_silently_replaced_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "state.json"
            path.write_text("{broken", encoding="utf-8")
            with self.assertRaises(tracker.StateCorruptError):
                tracker._load(str(path), {})

    def test_atomic_save_preserves_previous_file_when_replace_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "state.json"
            path.write_text('{"old": true}', encoding="utf-8")
            with mock.patch.object(tracker.os, "replace", side_effect=OSError("simulated crash")):
                with self.assertRaises(OSError):
                    tracker._save(str(path), {"new": True})
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"old": True})
            self.assertEqual(list(path.parent.glob(".state.json.*.tmp")), [])

    def test_second_patrol_lock_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with tracker._patrol_lock(tmp):
                with self.assertRaises(tracker.PatrolAlreadyRunning):
                    with tracker._patrol_lock(tmp):
                        self.fail("second lock unexpectedly acquired")

    def test_invalid_actor_override_is_rejected_before_network(self):
        with mock.patch.dict(os.environ, {"COMP_GOOGLE_ACTORS": "valid~actor,https://evil.test/x"}):
            with self.assertRaises(provider_extras.SourceError):
                provider_extras.configured_chain("google_ads")

    def test_skill_contract_and_product_wording(self):
        text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        headings = [
            "## Workflow",
            "## Output Template",
            "## Decision Criteria",
            "## Anti-patterns",
            "## Integration",
            "## Quality Checklist",
        ]
        positions = [text.index(heading) for heading in headings]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn("Command Center", text)
        self.assertRegex(text, r'(?m)^version: "1\.1"$', msg="catalog release must preserve the supplied 1.1 provenance")
        self.assertRegex(text, r'(?m)^publishedAt: "2026-09-03"$', msg="publication date must be stable")


if __name__ == "__main__":
    unittest.main()
