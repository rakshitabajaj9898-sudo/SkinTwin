import json
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


REGISTER_PATH = (
    Path(__file__).parent
    / "manifests"
    / "dataset_register.json"
)


def check_dataset_approval(dataset_id: str) -> bool:
    """Fail closed unless all dataset approval requirements pass."""

    if not REGISTER_PATH.is_file():
        raise FileNotFoundError("Dataset register not found.")

    with REGISTER_PATH.open("r", encoding="utf-8") as file:
        register = json.load(file)

    datasets = register.get("datasets", [])

    matches = [
        item for item in datasets
        if item.get("dataset_id") == dataset_id
    ]

    if len(matches) != 1:
        raise ValueError(
            f"Dataset ID must exist exactly once: {dataset_id}"
        )

    dataset = matches[0]
    policy = register.get("licensing_policy", {})

    if dataset.get("approval_status") != "approved":
        raise PermissionError("Dataset is not approved.")

    if policy.get("commercial_use_required") is True:
        if dataset.get("commercial_use") != "permitted":
            raise PermissionError("Commercial use is not permitted.")

    if policy.get("derivative_model_permission_required") is True:
        if dataset.get("derivative_model_permission") != "permitted":
            raise PermissionError("Derivative-model permission is missing.")

    if policy.get("redistribution_rights_required_for_published_weights") is True:
        if dataset.get("redistribution_permission") != "permitted":
            raise PermissionError("Model-weight redistribution permission is missing.")

    if dataset.get("consent_status") != "verified":
        raise PermissionError("Dataset consent is not verified.")

    if dataset.get("privacy_review_status") != "approved":
        raise PermissionError("Privacy review is not approved.")

    attribution = dataset.get("attribution_required")

    if attribution not in ("required", "not_required"):
        raise PermissionError("Attribution requirements are unverified.")

    if attribution == "required":
        text = dataset.get("attribution_text")
        if not isinstance(text, str) or not text.strip():
            raise PermissionError("Required attribution text is missing.")

    evidence = dataset.get("licence_evidence")

    if not isinstance(evidence, dict):
        raise PermissionError("Licence evidence is missing.")

    required_fields = [
        "source_url",
        "licence_name",
        "reviewed_by",
        "reviewed_on",
        "approval_notes",
    ]

    for field in required_fields:
        value = evidence.get(field)
        if not isinstance(value, str) or not value.strip():
            raise PermissionError(
                f"Licence evidence field '{field}' is missing."
            )

    parsed_url = urlparse(evidence["source_url"])

    if parsed_url.scheme != "https" or not parsed_url.netloc:
        raise PermissionError("Licence evidence must have a valid HTTPS URL.")

    if evidence["licence_name"] != dataset.get("licence_name"):
        raise PermissionError("Licence names do not match.")

    try:
        reviewed_date = date.fromisoformat(evidence["reviewed_on"])
    except ValueError:
        raise PermissionError("Review date must use YYYY-MM-DD.")

    if reviewed_date > date.today():
        raise PermissionError("Review date cannot be in the future.")

    return True


if __name__ == "__main__":
    print("SkinTwin Dataset Approval Gate")

    try:
        check_dataset_approval("SKINANALYSIS")
        print("Dataset approved.")
    except (ValueError, PermissionError, FileNotFoundError) as error:
        print("Training blocked:", error)
