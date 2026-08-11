import unittest

from utils import generate_search_queries


class GenerateSearchQueriesTests(unittest.TestCase):
    def test_generates_many_distinct_query_variants(self):
        queries = generate_search_queries("Karachi", ["food", "fashion"])

        self.assertGreaterEqual(len(queries), 24)
        self.assertEqual(len(set(queries)), len(queries))
        self.assertTrue(any("site:instagram.com" in query for query in queries))
        self.assertTrue(any("Karachi food blogger" in query for query in queries))
        self.assertTrue(any("Karachi fashion creator" in query for query in queries))
        self.assertTrue(any("near me" in query.lower() for query in queries))
        self.assertTrue(any("local" in query.lower() for query in queries))


if __name__ == "__main__":
    unittest.main()
