
import csv
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch.utils.data import Dataset

from ai_engine.datasets.dataset_gate import check_dataset_approval


class SkinTwinSegmentationDataset(Dataset):
    """Load paired facial images and segmentation masks."""

    def __init__(self, manifest_path, image_size=128):
        self.manifest_path = Path(manifest_path).resolve()
        self.root = self.manifest_path.parent
        self.image_size = image_size

        if not self.manifest_path.is_file():
            raise FileNotFoundError("Dataset manifest not found.")

        with self.manifest_path.open(
            "r", encoding="utf-8", newline=""
        ) as file:
            self.records = list(csv.DictReader(file))

        if not self.records:
            raise ValueError("Dataset manifest is empty.")

        required = {"image_path", "mask_path", "dataset_id"}

        if not required.issubset(self.records[0]):
            raise ValueError(
                "Manifest must contain image_path, mask_path "
                "and dataset_id columns."
            )

        # Check dataset rights before accessing image files.
        dataset_ids = {
            record["dataset_id"] for record in self.records
        }

        for dataset_id in dataset_ids:
            check_dataset_approval(dataset_id)

        # Validate all image-mask pairs.
        for record in self.records:
            for field in ("image_path", "mask_path"):
                path = (self.root / record[field]).resolve()

                if not path.is_relative_to(self.root):
                    raise ValueError("Dataset path escapes dataset folder.")

                if not path.is_file():
                    raise FileNotFoundError(
                        f"Missing {field}: {path}"
                    )

                record[field] = str(path)

    def __len__(self):
        return len(self.records)

    def __getitem__(self, index):
        record = self.records[index]

        image = Image.open(record["image_path"]).convert("RGB")
        mask = Image.open(record["mask_path"]).convert("L")

        image = image.resize(
            (self.image_size, self.image_size),
            Image.Resampling.BILINEAR
        )

        mask = mask.resize(
            (self.image_size, self.image_size),
            Image.Resampling.NEAREST
        )

        image_array = np.asarray(image, dtype=np.float32) / 255.0
        mask_array = np.asarray(mask, dtype=np.uint8)

        # Masks must contain only background (0) and skin (1).
        if not np.isin(mask_array, [0, 1]).all():
            raise ValueError(
                "Mask must contain class IDs 0 and 1 only."
            )

        image_tensor = torch.from_numpy(
            image_array.transpose(2, 0, 1).copy()
        )

        mask_tensor = torch.from_numpy(
            mask_array.copy()
        ).long()

        return {
            "image": image_tensor,
            "mask": mask_tensor,
            "dataset_id": record["dataset_id"]
        }
