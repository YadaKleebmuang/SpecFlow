import unittest
import yaml
import os
from pathlib import Path

class TestFallbackAndSecurityWiring(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path(__file__).resolve().parent.parent
        self.config_path = self.repo_root / "app/rasa/config.yml"
        self.domain_path = self.repo_root / "app/rasa/domain.yml"
        self.rules_path = self.repo_root / "app/rasa/data/rules.yml"
        self.credentials_path = self.repo_root / "app/rasa/credentials.yml"

    def test_fallback_classifier_configuration(self):
        with open(self.config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        pipeline = config.get("pipeline", [])
        fallback_comp = next((c for c in pipeline if c.get("name") == "FallbackClassifier"), None)
        self.assertIsNotNone(fallback_comp, "FallbackClassifier must be present in config.yml")
        self.assertEqual(fallback_comp.get("threshold"), 0.3, "Fallback threshold must be 0.3")
        self.assertEqual(fallback_comp.get("ambiguity_threshold"), 0.1, "Fallback ambiguity threshold must be 0.1")

    def test_domain_fallback_response_exists(self):
        with open(self.domain_path, "r", encoding="utf-8") as f:
            domain = yaml.safe_load(f)
        
        responses = domain.get("responses", {})
        self.assertIn("utter_fallback", responses, "utter_fallback response must be defined in domain.yml")
        fallback_text = responses["utter_fallback"][0].get("text", "")
        self.assertTrue(len(fallback_text) > 0, "utter_fallback text must not be empty")

    def test_rules_fallback_wiring_exists(self):
        with open(self.rules_path, "r", encoding="utf-8") as f:
            rules_data = yaml.safe_load(f)
        
        rules = rules_data.get("rules", [])
        fallback_rule = next((r for r in rules if any(s.get("intent") == "nlu_fallback" for s in r.get("steps", []))), None)
        self.assertIsNotNone(fallback_rule, "A rule handling intent 'nlu_fallback' must be present in rules.yml")
        steps = fallback_rule.get("steps", [])
        action_step = next((s for s in steps if s.get("action") == "utter_fallback"), None)
        self.assertIsNotNone(action_step, "Fallback rule must trigger action 'utter_fallback'")

    def test_credentials_environment_interpolation(self):
        with open(self.credentials_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        self.assertIn("${LINE_CHANNEL_SECRET}", content, "credentials.yml must use ${LINE_CHANNEL_SECRET}")
        self.assertIn("${LINE_CHANNEL_ACCESS_TOKEN}", content, "credentials.yml must use ${LINE_CHANNEL_ACCESS_TOKEN}")
        
        # Verify no hardcoded long token strings for LINE credentials
        cred_yaml = yaml.safe_load(content)
        line_conf = cred_yaml.get("line_channel.LineInput", {})
        for k in ["channel_secret", "channel_access_token"]:
            val = line_conf.get(k, "")
            self.assertTrue(val.startswith("${") and val.endswith("}"), f"LINE credential '{k}' must be an environment variable reference")

if __name__ == "__main__":
    unittest.main()
