#!/usr/bin/env python3
"""Evaluate a trained VisionQC model and print metrics + confusion matrix."""
import argparse
import os
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODEL_DIR = os.path.join(DATA_DIR, "models")

IMG_SIZE = 224

val_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


def evaluate(model_path, dataset_path):
    model = models.mobilenet_v3_small(weights=None)
    model.classifier[-1] = nn.Linear(model.classifier[-1].in_features, 2)
    model.load_state_dict(torch.load(model_path, map_location="cpu", weights_only=True))
    model.eval()

    dataset = datasets.ImageFolder(dataset_path, transform=val_transform)
    loader = DataLoader(dataset, batch_size=32, shuffle=False, num_workers=0)

    print(f"Classes: {dataset.classes}")
    print(f"Total images: {len(dataset)}")

    correct = 0
    total = 0
    tp = fp = fn = tn = 0

    with torch.no_grad():
        for images, labels in loader:
            outputs = model(images)
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()

            for p, l in zip(predicted, labels):
                if p == 1 and l == 1:
                    tp += 1
                elif p == 1 and l == 0:
                    fp += 1
                elif p == 0 and l == 1:
                    fn += 1
                else:
                    tn += 1

    accuracy = 100.0 * correct / total
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    print(f"\n{'='*40}")
    print(f"Model: {model_path}")
    print(f"Dataset: {dataset_path}")
    print(f"{'='*40}")
    print(f"Accuracy:  {accuracy:.1f}%")
    print(f"Precision: {precision:.3f}")
    print(f"Recall:    {recall:.3f}")
    print(f"F1 Score:  {f1:.3f}")
    print(f"\nConfusion Matrix:")
    print(f"              Predicted OK  Predicted Defect")
    print(f"  Actual OK      {tn:5d}         {fp:5d}")
    print(f"  Actual Def     {fn:5d}         {tp:5d}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate VisionQC model")
    parser.add_argument("--model", default=os.path.join(MODEL_DIR, "baseline_model.pth"))
    parser.add_argument("--dataset", default=None)
    args = parser.parse_args()

    if not args.dataset:
        for candidate in [
            os.path.join(DATA_DIR, "casting_dataset", "test"),
            os.path.join(DATA_DIR, "casting_dataset", "train"),
            os.path.join(DATA_DIR, "sample_images"),
        ]:
            if os.path.exists(candidate):
                args.dataset = candidate
                break

    if not args.dataset:
        print("No dataset found for evaluation.")
    else:
        evaluate(args.model, args.dataset)
