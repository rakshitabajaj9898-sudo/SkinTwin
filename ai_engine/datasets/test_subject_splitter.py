
import csv
import tempfile
import unittest
from pathlib import Path

from ai_engine.datasets.subject_splitter import split_by_subject


class TestSubjectSplitter(unittest.TestCase):

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

        self.records = []

        # Six fictional subjects, with two images each.
        for subject_number in range(1, 7):
            for image_number in range(1, 3):
                self.records.append({
                    "image_id": f"IMG{subject_number}_{image_number}",
                    "subject_id": f"SUB{subject_number:03d}",
                    "image_path": f"images/IMG{subject_number}_{image_number}.jpg",
                    "mask_path": f"masks/IMG{subject_number}_{image_number}.png",
                    "dataset_id": "TEST_DATASET",
                    "annotation_id": f"ANN{subject_number}_{image_number}",
                    "split": "",
                    "consent_status": "verified",
                    "training_permission": "true",
                    "approval_status": "approved",
                })

        self.write_manifest(self.records)

    def tearDown(self):
        self.temp_dir.cleanup()

    def write_manifest(self, records, columns=None):
        if columns is None:
            columns = self.columns

        with self.manifest_path.open(
            "w", newline="", encoding="utf-8"
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=columns,
                extrasaction="ignore",
            )
            writer.writeheader()
            writer.writerows(records)

    def read_manifest(self):
        with self.manifest_path.open(
            "r", newline="", encoding="utf-8"
        ) as file:
            return list(csv.DictReader(file))

    def test_split_creates_three_groups(self):
        result = split_by_subject(
            str(self.manifest_path),
            seed=42,
        )

        self.assertEqual(result["total_subjects"], 6)
        self.assertEqual(result["total_images"], 12)
        self.assertGreater(result["train_subjects"], 0)
        self.assertGreater(result["validation_subjects"], 0)
        self.assertGreater(result["test_subjects"], 0)

    def test_subjects_do_not_cross_splits(self):
        split_by_subject(str(self.manifest_path), seed=42)
        records = self.read_manifest()

        subject_splits = {}

        for record in records:
            subject = record["subject_id"]
            split = record["split"]

            if subject not in subject_splits:
                subject_splits[subject] = set()

            subject_splits[subject].add(split)

        for splits in subject_splits.values():
            self.assertEqual(len(splits), 1)

    def test_all_images_receive_a_split(self):
        split_by_subject(str(self.manifest_path), seed=42)
        records = self.read_manifest()

        allowed = {"train", "validation", "test"}

        for record in records:
            self.assertIn(record["split"], allowed)

    def test_same_seed_produces_same_split(self):
        split_by_subject(str(self.manifest_path), seed=42)
        first_result = {
            record["subject_id"]: record["split"]
            for record in self.read_manifest()
        }

        split_by_subject(str(self.manifest_path), seed=42)
        second_result = {
            record["subject_id"]: record["split"]
            for record in self.read_manifest()
        }

        self.assertEqual(first_result, second_result)

    def test_missing_subject_id(self):
        records = [record.copy() for record in self.records]
        records[0]["subject_id"] = ""

        self.write_manifest(records)

        with self.assertRaisesRegex(ValueError, "subject_id"):
            split_by_subject(str(self.manifest_path))

    def test_fewer_than_three_subjects(self):
        records = [
            record.copy()
            for record in self.records
            if record["subject_id"] in {"SUB001", "SUB002"}
        ]

        self.write_manifest(records)

        with self.assertRaisesRegex(ValueError, "At least 3"):
            split_by_subject(str(self.manifest_path))

    def test_invalid_ratios(self):
        with self.assertRaisesRegex(ValueError, "sum to 1"):
            split_by_subject(
                str(self.manifest_path),
                ratios={
                    "train": 0.8,
                    "validation": 0.1,
                    "test": 0.2,
                },
            )

    def test_missing_manifest(self):
        missing_path = Path(self.temp_dir.name) / "missing.csv"

        with self.assertRaises(FileNotFoundError):
            split_by_subject(str(missing_path))


if __name__ == "__main__":
    unittest.main(verbosity=2)
