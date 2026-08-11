import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from discovery_engine.engine import DiscoveryEngine
from discovery_engine.queues import DiscoveryQueueState
from discovery_engine.relevance import build_keyword_variants, keyword_matches, score_profile


def test_queue_state_tracks_pending_and_processed(tmp_path):
    state_file = tmp_path / "state.json"
    queue = DiscoveryQueueState(str(state_file))

    queue.enqueue_pending(["user_a", "user_b"])
    assert queue.next_pending() == "user_a"
    queue.mark_processed("user_a")
    assert queue.is_processed("user_a") is True
    assert queue.snapshot()["pending"] == ["user_b"]


def test_keyword_variants_cover_common_forms():
    variants = build_keyword_variants("food blogger")
    assert "food blogger" in variants
    assert "foodblogger" in variants


def test_keyword_matches_on_bio_and_location():
    profile = {"bio": "Loves food reviews in Milan", "name": "Marta", "username": "martafood"}
    assert keyword_matches(profile, "food blogger", "Milan") is True


def test_score_profile_rewards_keyword_hits():
    profile = {"bio": "Food blogger based in Milan", "name": "Marta", "username": "martafood"}
    assert score_profile(profile, "food blogger", "Milan") >= 3


def test_discovery_engine_skips_non_profile_keywords():
    engine = DiscoveryEngine("nike", "food blogger", "Milan")
    assert engine._looks_like_instagram_candidate("food blogger") is False
    assert engine._normalize_profile_url("food blogger") is None


def test_discovery_engine_reports_stage_counters_and_failures():
    engine = DiscoveryEngine("nike", "food blogger", "Milan")
    engine._record_counter("profiles_opened")
    engine._record_stage("profile_load", success=False, detail="navigation failed")
    report = engine.get_report()
    assert report["counters"]["profiles_opened"] == 1
    assert report["stage_failures"]["profile_load"] == "navigation failed"


class _FakeDialog:
    """Stands in for a Playwright locator over the followers dialog."""

    def __init__(self, html_by_round):
        self._html_by_round = html_by_round
        self._round = 0

    def inner_html(self):
        index = min(self._round, len(self._html_by_round) - 1)
        return self._html_by_round[index]

    def evaluate(self, _script):
        self._round += 1


class _FakePage:
    def __init__(self, dialog):
        self._dialog = dialog

    def locator(self, _selector):
        return self._dialog


def test_harvest_following_dedupes_excludes_and_stops_on_new_rows():
    round_one = '<a href="/alice/">Alice</a><a href="/bob/">Bob</a><a href="/explore/">Explore</a>'
    round_two = '<a href="/alice/">Alice</a><a href="/bob/">Bob</a><a href="/carol/">Carol</a><a href="/nike/">Nike</a>'
    engine = DiscoveryEngine("nike", "food blogger", "Milan")
    engine.page = _FakePage(_FakeDialog([round_one, round_two, round_two]))

    following = engine._harvest_following("nike", max_following=10, max_scrolls=6)

    assert following == ["alice", "bob", "carol"]


def test_harvest_following_respects_max_following_cap():
    html = '<a href="/alice/">Alice</a><a href="/bob/">Bob</a><a href="/carol/">Carol</a>'
    engine = DiscoveryEngine("nike", "food blogger", "Milan")
    engine.page = _FakePage(_FakeDialog([html]))

    following = engine._harvest_following("nike", max_following=2, max_scrolls=6)

    assert following == ["alice", "bob"]


def test_evaluate_match_requires_both_keyword_hit_and_bio():
    engine = DiscoveryEngine("nike", "food blogger", "Milan")

    profile_with_bio = {"bio": "Food blogger based in Milan", "name": "Marta", "username": "martafood"}
    match_result, keyword_ok, has_bio = engine._evaluate_match(profile_with_bio)
    assert (match_result, keyword_ok, has_bio) == (True, True, True)

    profile_without_bio = {"bio": "", "name": "food blogger", "username": "martafood"}
    match_result, keyword_ok, has_bio = engine._evaluate_match(profile_without_bio)
    assert keyword_ok is True
    assert has_bio is False
    assert match_result is False
