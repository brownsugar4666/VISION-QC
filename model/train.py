#!/usr/bin/env python3
"""
VisionQC Model Training
Transfer learning with MobileNetV3-Small on casting inspection images.
Uses the Kaggle "Casting product image data for quality inspection" dataset
or per-plant labelled images from the review queue.
"""
import argparse
import json
import os
import sys

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split
from torchvision import datasets, transforms, models

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODEL_DIR = os.path.join(DATA_DIR, "models")
DATASET_DIR = os.path.join(DATA_DIR, "casting_dataset")
SAMPLE_DIR = os.path.join(DATA_DIR, "sample_images")

os.makedirs(MODEL_DIR, exist_ok=True)

BATCH_SIZE = 32
NUM_EPOCHS = 10
LEARNING_RATE = 0.001
NUM_CLASSES = 2  # ok_front, def_front
IMG_SIZE = 224

train_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(10),
    transforms.ColorJitter(brightness=0.2, contrast=0.2),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

val_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


def create_model():
    model = models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.DEFAULT)
    model.classifier[-1] = nn.Linear(model.classifier[-1].in_features, NUM_CLASSES)
    return model


def get_dataset_path(plant_id=None):
    if plant_id:
        plant_data = os.path.join(DATA_DIR, "uploads", str(plant_id), "labelled")
        if os.path.exists(plant_data):
            return plant_data

    if os.path.exists(os.path.join(DATASET_DIR, "train")):
        return os.path.join(DATASET_DIR, "train")

    if os.path.exists(SAMPLE_DIR) and any(
        os.path.isdir(os.path.join(SAMPLE_DIR, d)) for d in os.listdir(SAMPLE_DIR)
    ):
        return SAMPLE_DIR

    return None


def train(plant_id=None, epochs=NUM_EPOCHS):
    dataset_path = get_dataset_path(plant_id)
    if not dataset_path:
        print(f"ERROR: No dataset found. Please either:")
        print(f"  1. Download the Kaggle casting dataset to {DATASET_DIR}/")
        print(f"  2. Run: python scripts/download_dataset.py")
        print(f"  3. Use the built-in sample images at {SAMPLE_DIR}/")
        sys.exit(1)

    print(f"Training on dataset: {dataset_path}")
    full_dataset = datasets.ImageFolder(dataset_path, transform=train_transform)

    class_names = full_dataset.classes
    print(f"Classes: {class_names}")
    print(f"Total images: {len(full_dataset)}")

    val_size = max(1, int(0.2 * len(full_dataset)))
    train_size = len(full_dataset) - val_size
    train_dataset, val_dataset = random_split(full_dataset, [train_size, val_size])

    val_dataset.dataset = datasets.ImageFolder(dataset_path, transform=val_transform)

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

    device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    print(f"Device: {device}")

    model = create_model().to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.1)

    best_acc = 0.0
    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0

        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item()
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()

        train_acc = 100.0 * correct / total
        scheduler.step()

        model.eval()
        val_correct = 0
        val_total = 0
        tp = fp = fn = tn = 0

        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                _, predicted = outputs.max(1)
                val_total += labels.size(0)
                val_correct += predicted.eq(labels).sum().item()

                for p, l in zip(predicted, labels):
                    if p == 1 and l == 1:
                        tp += 1
                    elif p == 1 and l == 0:
                        fp += 1
                    elif p == 0 and l == 1:
                        fn += 1
                    else:
                        tn += 1

        val_acc = 100.0 * val_correct / val_total
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

        print(f"Epoch {epoch+1}/{epochs} — Loss: {running_loss/len(train_loader):.4f} "
              f"Train Acc: {train_acc:.1f}% Val Acc: {val_acc:.1f}% "
              f"Precision: {precision:.3f} Recall: {recall:.3f}")

        if val_acc > best_acc:
            best_acc = val_acc

    model_cpu = model.cpu()
    if plant_id:
        model_path = os.path.join(MODEL_DIR, f"plant_{plant_id}_model.pth")
        version = f"plant_{plant_id}_v1"
    else:
        model_path = os.path.join(MODEL_DIR, "baseline_model.pth")
        version = "baseline_v1"

    existing_versions = [f for f in os.listdir(MODEL_DIR) if f.startswith(f"plant_{plant_id}" if plant_id else "baseline")]
    version_num = len(existing_versions) + 1
    version = f"plant_{plant_id}_v{version_num}" if plant_id else f"baseline_v{version_num}"

    torch.save(model_cpu.state_dict(), model_path)
    print(f"\nModel saved to {model_path}")
    print(f"Version: {version}")
    print(f"Best validation accuracy: {best_acc:.1f}%")
    print(f"Precision: {precision:.3f}, Recall: {recall:.3f}")

    confusion_matrix = [[tn, fp], [fn, tp]]
    print(f"Confusion Matrix: {confusion_matrix}")

    metrics = {
        "version": version,
        "model_path": model_path,
        "accuracy": round(best_acc, 2),
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "confusion_matrix": confusion_matrix,
        "plant_id": plant_id,
    }

    metrics_path = model_path.replace(".pth", "_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    try:
        sys.path.insert(0, BASE_DIR)
        from backend.app.database import engine
        from backend.app.models import ModelVersion
        from sqlmodel import Session, select

        with Session(engine) as session:
            old_active = session.exec(
                select(ModelVersion).where(
                    ModelVersion.is_active == True,
                    ModelVersion.plant_id == plant_id,
                )
            ).all()
            for m in old_active:
                m.is_active = False
                session.add(m)

            mv = ModelVersion(
                plant_id=plant_id,
                version=version,
                model_path=model_path,
                accuracy=best_acc,
                precision=precision,
                recall=recall,
                confusion_matrix_json=json.dumps(confusion_matrix),
                is_active=True,
            )
            session.add(mv)
            session.commit()
            print("Model version recorded in database.")
    except Exception as e:
        print(f"Note: Could not record in DB (run the app first): {e}")

    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train VisionQC model")
    parser.add_argument("--plant-id", type=int, default=None, help="Plant ID for plant-specific training")
    parser.add_argument("--epochs", type=int, default=NUM_EPOCHS, help="Number of training epochs")
    args = parser.parse_args()
    train(plant_id=args.plant_id, epochs=args.epochs)
