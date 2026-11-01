import json
from pathlib import Path
from datetime import date


REGISTER_PATH = (
    Path(__file__).parent
    / "manifests"
    / "dataset_register.json"
)


def check_dataset_approval(dataset_id: str) -> bool:
    """Fail closed unless all required dataset rights are documented."""

    if not REGISTER_PATH.is_file():
        raise FileNotFoundError("Dataset register not found.")

    with REGISTER_PATH.open("r", encoding="utf-8") as file:
        register = json.load(file)

    datasets = register.get("datasets", [])

    dataset = next(
        (
            item for item in datasets
            if item.get("dataset_id") == dataset_id
        ),
        None
    )

    if dataset is None:
        raise ValueError(f"Unknown dataset: {dataset_id}")

    if dataset.get("approval_status") != "approved":
        raise PermissionError(
            f"Dataset {dataset_id} is not approved for training."
        )

    required_permissions = [
        "commercial_use",
        "derivative_model_permission",
        "redistribution_permission",
    ]

    for permission in required_permissions:
        if dataset.get(permission) != "permitted":
            raise PermissionError(
                f"Dataset {dataset_id}: {permission} "
                "is not verified as permitted."
            )

    attribution = dataset.get("attribution_required")

    if attribution not in ("required", "not_required"):
        raise PermissionError(
            f"Dataset {dataset_id}: attribution requirements "
            "have not been verified."
        )

    if attribution == "required" and not dataset.get("attribution_text"):
        raise PermissionError(
            f"Dataset {dataset_id}: required attribution text is missing."
        )

    evidence = dataset.get("licence_evidence")

    if not isinstance(evidence, dict):
        raise PermissionError(
            f"Dataset {dataset_id}: licence evidence is missing."
        )

    evidence_fields = [
        "source_url",
        "licence_name",
        "reviewed_by",
        "reviewed_on",
        "approval_notes",
    ]

    for field in evidence_fields:
        if not isinstance(evidence.get(field), str) or not evidence[field].strip():
            raise PermissionError(
                f"Dataset {dataset_id}: licence evidence field "
                f"'{field}' is missing."
            )

    try:
        date.fromisoformat(evidence["reviewed_on"])
    except ValueError:
        raise PermissionError(
            f"Dataset {dataset_id}: reviewed_on must use YYYY-MM-DD."
        )

    return True


if __name__ == "__main__":
    print("SkinTwin Dataset Approval Gate")

    try:
        check_dataset_approval("SKINANALYSIS")
        print("Dataset approved.")
    except (ValueError, PermissionError, FileNotFoundError) as error:
        print("Training blocked:", error)
