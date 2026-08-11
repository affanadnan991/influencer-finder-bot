import unittest

from utils import create_profile_record


class ProfileCleaningTests(unittest.TestCase):
    def test_creates_clean_profile_record(self):
        record = create_profile_record(
            username="",
            name="Foodie City",
            url="https://www.instagram.com/foodie_city/",
            profile_url="https://www.instagram.com/foodie_city/",
            followers="10.2K",
            following="450",
            bio="Food lover and creator",
            verified=True,
            niche=["food", "lifestyle"],
        )

        self.assertIsNotNone(record)
        self.assertEqual(record["username"], "foodie_city")
        self.assertEqual(record["profile_url"], "https://www.instagram.com/foodie_city/")
        self.assertEqual(record["followers"], 10200)
        self.assertEqual(record["following"], 450)
        self.assertEqual(record["bio"], "Food lover and creator")
        self.assertTrue(record["verified"])
        self.assertEqual(record["niche"], "food")

    def test_rejects_invalid_profile_url(self):
        record = create_profile_record(
            username="bad",
            name="Bad",
            url="https://example.com/not-instagram",
            profile_url="https://example.com/not-instagram",
        )

        self.assertIsNone(record)


if __name__ == "__main__":
    unittest.main()
