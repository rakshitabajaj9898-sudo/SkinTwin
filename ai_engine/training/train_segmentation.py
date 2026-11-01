import argparse
import random
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader

from ai_engine.datasets.segmentation_dataset import SkinTwinSegmentationDataset
from ai_engine.models.model_config import MODEL_CONFIG
from ai_engine.models.unet import SkinTwinUNetSmall
from ai_engine.training.training_guard import authorize_training


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def get_device():
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def train(dataset_path, dataset_id):
    authorize_training(dataset_id)

    config = MODEL_CONFIG
    set_seed(config["random_seed"])

    dataset = SkinTwinSegmentationDataset(
        manifest_path=dataset_path,
        image_size=config["input_size"],
    )

    loader = DataLoader(
        dataset,
        batch_size=config["batch_size"],
        shuffle=True,
        num_workers=0,
    )

    device = get_device()
    model = SkinTwinUNetSmall().to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=config["learning_rate"],
    )

    model.train()

    for epoch in range(config["epochs"]):
        total_loss = 0.0

        for batch in loader:
            images = batch["image"].to(device)
            masks = batch["mask"].to(device)

            optimizer.zero_grad()
            predictions = model(images)
            loss = criterion(predictions, masks)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        average_loss = total_loss / len(loader)

        print(
            f"Epoch {epoch + 1}/{config['epochs']} "
            f"| Loss: {average_loss:.4f}"
        )

    checkpoint_dir = Path("ai_engine/checkpoints")
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    checkpoint_path = checkpoint_dir / "skintwin_unet_small.pth"

    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "model_config": config,
            "dataset_id": dataset_id,
            "epochs": config["epochs"],
        },
        checkpoint_path,
    )

    print(f"Training complete. Checkpoint saved: {checkpoint_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--dataset-id", required=True)
    args = parser.parse_args()

    train(args.manifest, args.dataset_id)