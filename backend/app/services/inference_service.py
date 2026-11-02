import os
import torch
import torch.nn.functional as F
from torchvision import transforms, models
from PIL import Image
import numpy as np

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..")
MODEL_DIR = os.path.join(BASE_DIR, "data", "models")
DEFAULT_MODEL_PATH = os.path.join(MODEL_DIR, "baseline_model.pth")

_model_cache = {}

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


def _load_model(model_path: str = None):
    path = model_path or DEFAULT_MODEL_PATH
    if path in _model_cache:
        return _model_cache[path]

    model = models.mobilenet_v3_small(weights=None)
    model.classifier[-1] = torch.nn.Linear(model.classifier[-1].in_features, 2)

    if os.path.exists(path):
        state_dict = torch.load(path, map_location="cpu", weights_only=True)
        model.load_state_dict(state_dict)

    model.eval()
    _model_cache[path] = model
    return model


def _generate_gradcam(model, img_tensor, image_path):
    gradcam_dir = os.path.join(os.path.dirname(image_path), "gradcam")
    os.makedirs(gradcam_dir, exist_ok=True)

    target_layer = model.features[-1]
    activations = []
    gradients = []

    def forward_hook(module, input, output):
        activations.append(output.detach())

    def backward_hook(module, grad_input, grad_output):
        gradients.append(grad_output[0].detach())

    fh = target_layer.register_forward_hook(forward_hook)
    bh = target_layer.register_full_backward_hook(backward_hook)

    try:
        input_tensor = img_tensor.unsqueeze(0).requires_grad_(True)
        output = model(input_tensor)
        pred_class = output.argmax(dim=1).item()

        model.zero_grad()
        output[0, pred_class].backward()

        if not activations or not gradients:
            return None

        act = activations[0].squeeze()
        grad = gradients[0].squeeze()
        weights = grad.mean(dim=(1, 2))

        cam = torch.zeros(act.shape[1:], dtype=act.dtype)
        for i, w in enumerate(weights):
            cam += w * act[i]

        cam = F.relu(cam)
        cam = cam - cam.min()
        if cam.max() > 0:
            cam = cam / cam.max()

        cam_np = cam.numpy()
        cam_resized = np.array(Image.fromarray((cam_np * 255).astype(np.uint8)).resize((224, 224)))

        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        orig_img = Image.open(image_path).resize((224, 224))

        fig, ax = plt.subplots(1, 1, figsize=(3, 3), dpi=72)
        ax.imshow(orig_img)
        ax.imshow(cam_resized, cmap="jet", alpha=0.4)
        ax.axis("off")

        basename = os.path.splitext(os.path.basename(image_path))[0]
        gradcam_path = os.path.join(gradcam_dir, f"{basename}_gradcam.jpg")
        fig.savefig(gradcam_path, bbox_inches="tight", pad_inches=0)
        plt.close(fig)

        return gradcam_path
    except Exception:
        return None
    finally:
        fh.remove()
        bh.remove()


def run_inference(image_path: str, plant_id: int | None = None):
    plant_model_path = os.path.join(MODEL_DIR, f"plant_{plant_id}_model.pth") if plant_id else None

    if plant_model_path and os.path.exists(plant_model_path):
        model = _load_model(plant_model_path)
    else:
        model = _load_model(DEFAULT_MODEL_PATH)

    try:
        img = Image.open(image_path).convert("RGB")
        img_tensor = transform(img)

        with torch.no_grad():
            output = model(img_tensor.unsqueeze(0))
            probs = F.softmax(output, dim=1)
            confidence, pred = torch.max(probs, dim=1)

        result = "ok" if pred.item() == 0 else "defective"
        conf = confidence.item()

        gradcam_path = None
        if result == "defective":
            gradcam_path = _generate_gradcam(model, img_tensor, image_path)

        defect_type_id = 1 if result == "defective" else None

        return result, conf, gradcam_path, defect_type_id
    except Exception as e:
        return "defective", 0.5, None, None
