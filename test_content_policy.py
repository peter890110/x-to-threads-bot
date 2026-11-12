import unittest

from content_policy import prioritize_accounts, rumor_signal


class EditorialPolicyTests(unittest.TestCase):
    def test_uncertain_sources_are_excluded(self):
        for text in (
            "RUMOR: Nvidia may buy the company.",
            "Rumoured order cuts at a supplier.",
            "Sources say Apple is cutting production.",
            "The company reportedly won the order.",
            "Unconfirmed deal. Take this with a grain of salt.",
            "據傳公司將收購供應商。",
            "消息人士透露，公司可能砍單。",
            "網傳新產品即將上市。",
        ):
            with self.subTest(text=text):
                self.assertIsNotNone(rumor_signal(text))

    def test_ordinary_results_are_not_rumors(self):
        for text in (
            "Nvidia announced quarterly revenue of $30 billion.",
            "The annual report says revenue grew 20%.",
            "公司公布十月營收年增20%。",
            "Open source software demand is growing.",
        ):
            with self.subTest(text=text):
                self.assertIsNone(rumor_signal(text))

    def test_jukan_is_last_without_removing_other_accounts(self):
        self.assertEqual(
            prioritize_accounts(["jukan05", "aleabitoreddit", "MelvinInvests"]),
            ["aleabitoreddit", "MelvinInvests", "jukan05"],
        )
        self.assertEqual(prioritize_accounts(["Jukan05"]), ["Jukan05"])


if __name__ == "__main__":
    unittest.main()
