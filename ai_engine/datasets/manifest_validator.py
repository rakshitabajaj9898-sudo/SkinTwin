
import csv
from pathlib import Path

REQUIRED_COLUMNS = {
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
}

ALLOWED_SPLITS = {"train", "validation", "test"}


def validate_manifest(manifest_path: str) -> int:
    path = Path(manifest_path).resolve()

    if not path.is_file():
        raise FileNotFoundError(f"Manifest not found: {path}")

    with path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ValueError("Manifest is empty.")

        missing = REQUIRED_COLUMNS - set(reader.fieldnames)

        if missing:
            raise ValueError(
                f"Missing required columns: {sorted(missing)}"
            )

        records = list(reader)

    if not records:
        raise ValueError("Manifest contains no records.")

    seen_image_ids = set()

    for row_number, record in enumerate(records, start=2):
        for field in REQUIRED_COLUMNS:
            if not (record.get(field) or "").strip():
                raise ValueError(
                    f"Row {row_number}: '{field}' cannot be empty."
                )

        image_id = record["image_id"].strip()

        if image_id in seen_image_ids:
            raise ValueError(
                f"Row {row_number}: duplicate image_id '{image_id}'."
            )

        seen_image_ids.add(image_id)

        if record["split"].strip() not in ALLOWED_SPLITS:
            raise ValueError(f"Row {row_number}: invalid split.")

        if record["consent_status"].strip() != "verified":
            raise PermissionError(
                f"Row {row_number}: consent is not verified."
            )

        if record["training_permission"].strip().lower() != "true":
            raise PermissionError(
                f"Row {row_number}: training permission is not granted."
            )

        if record["approval_status"].strip() != "approved":
            raise PermissionError(
                f"Row {row_number}: dataset is not approved."
            )

    return len(records)


if __name__ == "__main__":
    manifest = (
        Path(__file__).parent
        / "manifests"
        / "dataset_manifest.csv"
    )

    try:
        count = validate_manifest(str(manifest))
        print(f"Manifest valid. Records checked: {count}")
    except (ValueError, PermissionError, FileNotFoundError) as error:
        print(f"Manifest validation failed: {error}")
