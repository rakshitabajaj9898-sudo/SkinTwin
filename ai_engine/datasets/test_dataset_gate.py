
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ai_engine.datasets.dataset_gate import (
    check_dataset_approval,
    REGISTER_PATH,
)


class TestDatasetApprovalGate(unittest.TestCase):

    def setUp(self):
        with REGISTER_PATH.open("r", encoding="utf-8") as file:
            self.register = json.load(file)

        self.dataset = copy.deepcopy(self.register["datasets"][0])

        # Fictional test-only approval record
        self.dataset.update({
            "approval_status": "approved",
            "commercial_use": "permitted",
            "derivative_model_permission": "permitted",
            "redistribution_permission": "permitted",
            "attribution_required": "not_required",
            "attribution_text": None,
            "consent_status": "verified",
            "privacy_review_status": "approved",
            "licence_name": "Test Licence",
            "licence_evidence": {
                "source_url": "https://example.com/licence",
                "licence_name": "Test Licence",
                "reviewed_by": "Test Reviewer",
                "reviewed_on": "2026-10-01",
                "approval_notes": "Fictional test evidence only."
            }
        })

        self.register["datasets"] = [self.dataset]

        self.temp_file = tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".json",
            delete=False,
            encoding="utf-8"
        )

        self.temp_path = Path(self.temp_file.name)

        self.write_register()
        self.temp_file.close()

        self.patcher = patch(
            "ai_engine.datasets.dataset_gate.REGISTER_PATH",
            self.temp_path
        )
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        self.temp_path.unlink(missing_ok=True)

    def write_register(self):
        self.temp_path.write_text(
            json.dumps(self.register, indent=2),
            encoding="utf-8"
        )

    def assert_blocked(self):
        self.write_register()

        with self.assertRaises(PermissionError):
            check_dataset_approval("SKINANALYSIS")

    def test_fully_approved_test_record(self):
        self.assertTrue(
            check_dataset_approval("SKINANALYSIS")
        )

    def test_commercial_permission_blocked(self):
        self.dataset["commercial_use"] = "unverified"
        self.assert_blocked()

    def test_derivative_permission_blocked(self):
        self.dataset["derivative_model_permission"] = "unverified"
        self.assert_blocked()

    def test_redistribution_permission_blocked(self):
        self.dataset["redistribution_permission"] = "unverified"
        self.assert_blocked()

    def test_consent_blocked(self):
        self.dataset["consent_status"] = "unverified"
        self.assert_blocked()

    def test_privacy_review_blocked(self):
        self.dataset["privacy_review_status"] = "pending"
        self.assert_blocked()

    def test_missing_licence_evidence_blocked(self):
        self.dataset["licence_evidence"] = {}
        self.assert_blocked()

    def test_invalid_licence_url_blocked(self):
        self.dataset["licence_evidence"]["source_url"] = (
            "http://example.com"
        )
        self.assert_blocked()

    def test_rejected_dataset_blocked(self):
        self.dataset["approval_status"] = "rejected"
        self.assert_blocked()


if __name__ == "__main__":
    unittest.main(verbosity=2)
