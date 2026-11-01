
from ai_engine.datasets.dataset_gate import check_dataset_approval


def authorize_training(dataset_id: str) -> None:
    """
    Authorize a dataset before model training begins.
    Raises PermissionError if approval is missing.
    """

    check_dataset_approval(dataset_id)

    print(f"Training authorized for dataset: {dataset_id}")
