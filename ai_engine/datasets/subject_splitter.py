
import csv
from collections import defaultdict
from pathlib import Path

import numpy as np


DEFAULT_SPLIT_RATIOS = {
    "train": 0.70,
    "validation": 0.15,
    "test": 0.15,
}


def split_by_subject(
    manifest_path: str,
    output_path: str = None,
    ratios: dict = None,
    seed: int = 42,
) -> dict:
    """
    Assign each subject to exactly one dataset split.

    All images belonging to a subject remain in the same split.
    """

    manifest = Path(manifest_path).resolve()

    if not manifest.is_file():
        raise FileNotFoundError("Dataset manifest not found.")

    if ratios is None:
        ratios = DEFAULT_SPLIT_RATIOS.copy()

    required_splits = {"train", "validation", "test"}

    if set(ratios) != required_splits:
        raise ValueError(
            "Ratios must contain train, validation and test."
        )

    if any(
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or value <= 0
        for value in ratios.values()
    ):
        raise ValueError("All split ratios must be positive numbers.")

    if not np.isclose(sum(ratios.values()), 1.0):
        raise ValueError("Split ratios must sum to 1.")

    with manifest.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames or "subject_id" not in reader.fieldnames:
            raise ValueError("Manifest must contain subject_id.")

        records = list(reader)

        if not records:
            raise ValueError("Manifest contains no records.")

        for row_number, record in enumerate(records, start=2):
            if not (record.get("subject_id") or "").strip():
                raise ValueError(
                    f"Row {row_number}: subject_id cannot be empty."
                )

    subjects = sorted({
        record["subject_id"].strip()
        for record in records
    })

    if len(subjects) < 3:
        raise ValueError(
            "At least 3 unique subjects are required "
            "to create train, validation and test splits."
        )

    rng = np.random.default_rng(seed)
    shuffled_subjects = rng.permutation(subjects).tolist()

    total_subjects = len(shuffled_subjects)

    train_count = max(
        1,
        int(total_subjects * ratios["train"])
    )

    validation_count = max(
        1,
        int(total_subjects * ratios["validation"])
    )

    # Keep at least one subject for the test split.
    if train_count + validation_count >= total_subjects:
        train_count = total_subjects - 2
        validation_count = 1

    train_subjects = set(
        shuffled_subjects[:train_count]
    )

    validation_subjects = set(
        shuffled_subjects[
            train_count:train_count + validation_count
        ]
    )

    test_subjects = set(
        shuffled_subjects[
            train_count + validation_count:
        ]
    )

    subject_splits = {}

    for subject in train_subjects:
        subject_splits[subject] = "train"

    for subject in validation_subjects:
        subject_splits[subject] = "validation"

    for subject in test_subjects:
        subject_splits[subject] = "test"

    # Verify that no subject appears in multiple splits.
    if (
        train_subjects & validation_subjects
        or train_subjects & test_subjects
        or validation_subjects & test_subjects
    ):
        raise RuntimeError("Subject leakage detected.")

    for record in records:
        subject_id = record["subject_id"].strip()
        record["split"] = subject_splits[subject_id]

    if output_path is None:
        output = manifest
    else:
        output = Path(output_path).resolve()

    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=reader.fieldnames,
        )
        writer.writeheader()
        writer.writerows(records)

    return {
        "total_subjects": total_subjects,
        "total_images": len(records),
        "train_subjects": len(train_subjects),
        "validation_subjects": len(validation_subjects),
        "test_subjects": len(test_subjects),
        "output_path": str(output),
    }


if __name__ == "__main__":
    manifest = (
        Path(__file__).parent
        / "manifests"
        / "dataset_manifest.csv"
    )

    try:
        result = split_by_subject(str(manifest))
        print("Subject split completed.")
        print(result)

    except (ValueError, FileNotFoundError) as error:
        print(f"Subject split failed: {error}")
