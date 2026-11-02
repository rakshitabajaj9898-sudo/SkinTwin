import csv
import tempfile
import unittest
from pathlib import Path

from ai_engine.datasets.manifest_validator import validate_manifest


class TestManifestValidator(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.manifest_path = Path(self.temp_dir.name) / "manifest.csv"

        self.columns = [
            "image_id",
            "subject_id",
            "image_path",
            "mask_path",
            "dataset_id",
            "annotation_id",
            "split",
            "consent_status",
            "training_permission",
            "approval_status",
        ]

        self.valid_record = {
            "image_id": "IMG001",
            "subject_id": "SUB001",
            "image_path": "images/IMG001.jpg",
            "mask_path": "masks/IMG001.png",
            "dataset_id": "SKINTWIN_INTERNAL",
            "annotation_id": "ANN001",
            "split": "train",
            "consent_status": "verified",
            "training_permission": "true",
            "approval_status": "approved",
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def write_manifest(self, columns=None, records=None):
        if columns is None:
            columns = self.columns

        if records is None:
            records = [self.valid_record]

        with self.manifest_path.open(
            "w", newline="", encoding="utf-8"
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=columns,
                extrasaction="ignore"
            )
            writer.writeheader()
            writer.writerows(records)

    def test_valid_manifest(self):
        self.write_manifest()
        self.assertEqual(
            validate_manifest(str(self.manifest_path)), 1
        )

    def test_empty_manifest(self):
        self.write_manifest(records=[])
        with self.assertRaisesRegex(ValueError, "no records"):
            validate_manifest(str(self.manifest_path))

    def test_missing_columns(self):
        self.write_manifest(columns=self.columns[:-1])
        with self.assertRaisesRegex(
            ValueError, "Missing required columns"
        ):
            validate_manifest(str(self.manifest_path))

    def test_duplicate_image_ids(self):
        second_record = self.valid_record.copy()
        second_record["subject_id"] = "SUB002"

        self.write_manifest(
            records=[self.valid_record, second_record]
        )

        with self.assertRaisesRegex(ValueError, "duplicate image_id"):
            validate_manifest(str(self.manifest_path))

    def test_invalid_split(self):
        record = self.valid_record.copy()
        record["split"] = "testing"
        self.write_manifest(records=[record])

        with self.assertRaisesRegex(ValueError, "invalid split"):
            validate_manifest(str(self.manifest_path))

    def test_unverified_consent(self):
        record = self.valid_record.copy()
        record["consent_status"] = "pending"
        self.write_manifest(records=[record])

        with self.assertRaisesRegex(PermissionError, "consent"):
            validate_manifest(str(self.manifest_path))

    def test_training_permission_denied(self):
        record = self.valid_record.copy()
        record["training_permission"] = "false"
        self.write_manifest(records=[record])

        with self.assertRaisesRegex(
            PermissionError, "training permission"
        ):
            validate_manifest(str(self.manifest_path))

    def test_unapproved_dataset(self):
        record = self.valid_record.copy()
        record["approval_status"] = "pending"
        self.write_manifest(records=[record])

        with self.assertRaisesRegex(PermissionError, "not approved"):
            validate_manifest(str(self.manifest_path))


if __name__ == "__main__":
    unittest.main(verbosity=2)
