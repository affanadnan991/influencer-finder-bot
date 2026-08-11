import json
import os
import tempfile
import unittest

from production_runtime import BrowserManager, StructuredLogger, URLWorkQueue, VisitedCache, retry_with_backoff


class ProductionRuntimeTests(unittest.TestCase):
    def test_retry_with_backoff_retries_until_success(self):
        attempts = {"count": 0}

        def flaky():
            attempts["count"] += 1
            if attempts["count"] < 3:
                raise RuntimeError("transient")
            return "ok"

        result = retry_with_backoff(flaky, max_attempts=3, base_delay=0)
        self.assertEqual(result, "ok")
        self.assertEqual(attempts["count"], 3)

    def test_structured_logger_writes_run_records(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = StructuredLogger(run_id="test-run", log_dir=tmpdir)
            logger.info("hello", stage="test")

            log_path = os.path.join(tmpdir, "test-run.jsonl")
            self.assertTrue(os.path.exists(log_path))
            with open(log_path, "r", encoding="utf-8") as handle:
                records = [json.loads(line) for line in handle if line.strip()]
            self.assertEqual(records[0]["message"], "hello")
            self.assertEqual(records[0]["stage"], "test")

    def test_browser_manager_builds_page_without_playwright(self):
        manager = BrowserManager(allow_browser_start=False)
        self.assertFalse(manager.ensure_browser())

    def test_url_work_queue_enqueues_and_dequeues(self):
        queue = URLWorkQueue()
        queue.enqueue("one")
        queue.enqueue("two")
        self.assertEqual(queue.size(), 2)
        self.assertEqual(queue.dequeue(), "one")
        self.assertEqual(queue.dequeue(), "two")

    def test_visited_cache_persists_urls(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = VisitedCache(db_path=os.path.join(tmpdir, "visited.db"))
            self.assertFalse(cache.is_visited("https://example.com/test"))
            cache.mark_visited("https://example.com/test")
            self.assertTrue(cache.is_visited("https://example.com/test"))


if __name__ == "__main__":
    unittest.main()
