"""בדיקות שכבת Ollama / מורה AI — בלי לדרוש שרת חי."""
from __future__ import annotations

import unittest
from unittest import mock

from core import ai_tutor, ollama_client


class OllamaClientTests(unittest.TestCase):
    def test_defaults_point_at_localhost(self):
        self.assertIn("11434", ollama_client._base_url())
        self.assertTrue(ollama_client._model_name())

    def test_enabled_respects_storage_pref(self):
        class Fake:
            def get_pref(self, key, default=None):
                return False if key == "ollama_enabled" else default

        self.assertFalse(ollama_client.enabled(Fake()))

    def test_chat_returns_empty_when_disabled(self):
        class Fake:
            def get_pref(self, key, default=None):
                return False if key == "ollama_enabled" else default

        self.assertEqual(
            ollama_client.chat([{"role": "user", "content": "שלום"}], storage=Fake()),
            "",
        )


class AiTutorFallbackTests(unittest.TestCase):
    def test_paraphrase_fallback_without_ollama(self):
        with mock.patch.object(ai_tutor.ollama_client, "chat", return_value=""):
            with mock.patch.object(ai_tutor, "available", return_value=False):
                # available is used by other paths; paraphrase always calls chat
                got = ai_tutor.paraphrase_question(
                    {"id": "x", "question": "חשבו 2+2", "subject": "math"},
                    force=True,
                )
        self.assertIn("plain", got)
        self.assertTrue(got["plain"])
        self.assertEqual(got.get("source"), "fallback")

    def test_silent_gaps_local_path(self):
        gap = ai_tutor.analyze_silent_gaps(
            "math",
            weak_topics=["טריגונומטריה", "שברים"],
            use_llm=False,
            force=True,
        )
        self.assertEqual(gap["source"], "local")
        self.assertIn("שברים", gap["prerequisite"] + gap["root_gap"])
        self.assertGreaterEqual(gap["drill_size"], 4)

    def test_action_plan_enrichment_is_fast_local(self):
        plan = {"steps": ["תרגול"], "readiness": {"weak_topics": ["אלגברה"]}}
        out = ai_tutor.enrichment_for_action_plan("math", plan, use_llm=False)
        self.assertIn("silent_gap", out)
        self.assertEqual(out["silent_gap"]["source"], "local")
        self.assertTrue(out["steps"])

    def test_socratic_fallback(self):
        with mock.patch.object(ai_tutor, "available", return_value=False):
            turn = ai_tutor.socratic_turn(
                {"question": "מהו 2+2?", "options": ["3", "4"], "answer": 1},
            )
        self.assertEqual(turn["source"], "fallback")
        self.assertTrue(turn["say"])


if __name__ == "__main__":
    unittest.main()
