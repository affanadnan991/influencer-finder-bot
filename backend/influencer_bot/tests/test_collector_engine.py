import os
import tempfile
import unittest

from collector import build_collection_record
from storage import ProfileStore


class CollectorEngineTests(unittest.TestCase):
    def test_build_collection_record_uses_only_collection_fields(self):
        record = build_collection_record(
            username="sample_user",
            profile_url="https://www.instagram.com/sample_user/",
            followers=1200,
            following=300,
            bio="Local food creator",
            verified=True,
            source_url="https://example.com/page",
        )

        self.assertEqual(record["username"], "sample_user")
        self.assertEqual(record["profile_url"], "https://www.instagram.com/sample_user/")
        self.assertIn("followers", record)
        self.assertIn("following", record)
        self.assertIn("bio", record)
        self.assertIn("verified", record)
        self.assertIn("source_url", record)
        self.assertIn("collection_time", record)
        self.assertNotIn("niche", record)
        self.assertNotIn("city", record)
        self.assertNotIn("source_query", record)

    def test_append_profiles_appends_without_overwriting(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "profiles.db")
            csv_path = os.path.join(tmpdir, "collection.csv")
            store = ProfileStore(database_file=db_path, csv_file=csv_path)

            first = build_collection_record(username="first", profile_url="https://www.instagram.com/first/", source_url="https://example.com/one")
            second = build_collection_record(username="second", profile_url="https://www.instagram.com/second/", source_url="https://example.com/two")

            count_one = store.append_profiles([first])
            count_two = store.append_profiles([second])

            self.assertEqual(count_one, 1)
            self.assertEqual(count_two, 1)

            stored = store.raw_records()
            self.assertEqual(len(stored), 2)
            self.assertEqual({row["username"] for row in stored}, {"first", "second"})
            self.assertTrue(os.path.exists(csv_path))
            with open(csv_path, "r", encoding="utf-8") as handle:
                rows = [line.strip() for line in handle if line.strip()]
            self.assertGreaterEqual(len(rows), 2)


if __name__ == "__main__":
    unittest.main()
