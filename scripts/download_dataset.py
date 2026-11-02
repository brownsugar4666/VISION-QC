#!/usr/bin/env python3
"""
Download the Kaggle Casting Product Image Dataset.

Option 1 (automatic): If you have kaggle CLI configured:
    pip install kaggle
    kaggle datasets download -d ravirajsinh45/real-life-industrial-dataset-of-casting-product
    unzip -o real-life-industrial-dataset-of-casting-product.zip -d data/casting_dataset

Option 2 (manual): Download from:
    https://www.kaggle.com/datasets/ravirajsinh45/real-life-industrial-dataset-of-casting-product
    Extract to: data/casting_dataset/
    Expected structure:
        data/casting_dataset/
            train/
                ok_front/
                def_front/
            test/
                ok_front/
                def_front/

This script tries Option 1 first, and falls back to generating sample images.
"""
import os
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATASET_DIR = os.path.join(DATA_DIR, "casting_dataset")
SAMPLE_DIR = os.path.join(DATA_DIR, "sample_images")


def try_kaggle_download():
    try:
        result = subprocess.run(
            ["kaggle", "datasets", "download", "-d",
             "ravirajsinh45/real-life-industrial-dataset-of-casting-product",
             "-p", DATA_DIR],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode == 0:
            zip_path = os.path.join(DATA_DIR, "real-life-industrial-dataset-of-casting-product.zip")
            subprocess.run(["unzip", "-o", zip_path, "-d", DATASET_DIR], check=True)
            os.remove(zip_path)

            for sub in ["casting_data", "casting_512x512"]:
                nested = os.path.join(DATASET_DIR, sub)
                if os.path.exists(nested):
                    for item in os.listdir(nested):
                        src = os.path.join(nested, item)
                        dst = os.path.join(DATASET_DIR, item)
                        if not os.path.exists(dst):
                            os.rename(src, dst)

            print(f"Dataset downloaded to {DATASET_DIR}")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return False


def generate_sample_images():
    """Generate simple synthetic casting images for demo purposes."""
    from PIL import Image, ImageDraw, ImageFilter
    import random

    for split in ["ok_front", "def_front"]:
        split_dir = os.path.join(SAMPLE_DIR, split)
        os.makedirs(split_dir, exist_ok=True)

    print("Generating sample casting images...")
    random.seed(42)

    for i in range(60):
        img = Image.new("RGB", (300, 300), color=(180, 180, 185))
        draw = ImageDraw.Draw(img)
        draw.ellipse([50, 50, 250, 250], fill=(160, 160, 165), outline=(140, 140, 145), width=2)
        draw.ellipse([100, 100, 200, 200], fill=(170, 170, 175))
        noise_val = random.randint(-10, 10)
        img = img.point(lambda p: max(0, min(255, p + noise_val)))
        img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
        img.save(os.path.join(SAMPLE_DIR, "ok_front", f"ok_{i:03d}.jpg"))

    for i in range(40):
        img = Image.new("RGB", (300, 300), color=(180, 180, 185))
        draw = ImageDraw.Draw(img)
        draw.ellipse([50, 50, 250, 250], fill=(160, 160, 165), outline=(140, 140, 145), width=2)
        draw.ellipse([100, 100, 200, 200], fill=(170, 170, 175))

        defect = random.choice(["scratch", "crack", "blob"])
        if defect == "scratch":
            x1, y1 = random.randint(60, 140), random.randint(60, 140)
            x2, y2 = random.randint(160, 240), random.randint(160, 240)
            draw.line([(x1, y1), (x2, y2)], fill=(80, 80, 85), width=random.randint(2, 4))
        elif defect == "crack":
            points = [(random.randint(80, 220), random.randint(80, 220)) for _ in range(4)]
            draw.line(points, fill=(60, 60, 65), width=2)
        else:
            cx, cy = random.randint(100, 200), random.randint(100, 200)
            r = random.randint(8, 20)
            draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(100, 100, 105))

        img.save(os.path.join(SAMPLE_DIR, "def_front", f"def_{i:03d}.jpg"))

    print(f"Generated 60 OK + 40 defective sample images in {SAMPLE_DIR}")


if __name__ == "__main__":
    if os.path.exists(os.path.join(DATASET_DIR, "train")):
        print("Dataset already exists. Skipping download.")
    elif try_kaggle_download():
        print("Kaggle download successful!")
    else:
        print("Kaggle CLI not available or download failed.")
        print("Generating sample images for demo...")
        generate_sample_images()
        print("\nFor the full dataset, download manually from:")
        print("  https://www.kaggle.com/datasets/ravirajsinh45/real-life-industrial-dataset-of-casting-product")
        print(f"  Extract to: {DATASET_DIR}/")
