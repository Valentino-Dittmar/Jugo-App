import os
import shutil
import cv2
import numpy as np
import glob
from compliance_checker import run_compliance_check
from yolov5.detect import run as yolo_run

def run_full_pipeline(image_path, user_hex,
                      yolov5_dir="yolov5",
                      weights_path="./yolov5_weights/best.pt",
                      output_dir="/uploads"):

    print("📦 Running pipeline for:", image_path, flush=True)
    print("🎯 Passed user hex color:", user_hex, flush=True)

    # === Step 1: Clean up old YOLO label files ===
    label_folder = os.path.join(yolov5_dir, "runs/detect/webinput/labels")
    if os.path.exists(label_folder):
        for f in glob.glob(os.path.join(label_folder, "*.txt")):
            os.remove(f)

    # === Step 2: Run YOLO detection ===
    yolo_run(
        weights=weights_path,
        source=os.path.abspath(image_path),
        imgsz=(640, 640),
        conf_thres=0.25,
        iou_thres=0.45,
        save_txt=True,
        save_conf=True,
        project=os.path.join(yolov5_dir, "runs/detect"),
        name="webinput",
        exist_ok=True,
        nosave=False
    )

    # === Step 3: Paths ===
    image_filename = os.path.basename(image_path)
    label_name = os.path.splitext(image_filename)[0] + ".txt"
    label_path = os.path.join(yolov5_dir, "runs/detect/webinput/labels", label_name)

    # === Step 4: Load the original uploaded image (no boxes) ===
    result_image = cv2.imread(image_path)
    if result_image is None:
        raise ValueError(f"❌ Could not load original image from {image_path}")

    # === Step 5: Parse label file ===
    detections = []
    if os.path.exists(label_path):
        with open(label_path, "r") as file:
            for line in file:
                parts = line.strip().split()
                if len(parts) >= 5:
                    try:
                        cls, x_center, y_center, w, h = map(float, parts[:5])
                        detections.append([x_center, y_center, w, h])
                    except ValueError:
                        continue
        print("📄 Using label file:", label_path, flush=True)
    else:
        print("⚠️ No label file found — assuming compliant", flush=True)
        _, buffer = cv2.imencode('.png', result_image)
        return True, buffer.tobytes()

    print("✅ YOLO Detections:", len(detections), flush=True)
    print("✅ Detection boxes:", detections, flush=True)

    # === Step 6: Run compliance check ===
    print("🔍 Calling compliance check...", flush=True)
    is_compliant, result_image_in_memory, formatted_colors = run_compliance_check(result_image, detections, user_hex)
    print("✅ Final compliance result:", is_compliant, flush=True)

    # === Step 7: Cleanup (only label now, no blue-box image to delete)
    try:
        if os.path.exists(label_path):
            os.remove(label_path)
    except Exception as e:
        print(f"⚠️ Cleanup error: {e}", flush=True)

    return is_compliant, result_image_in_memory, formatted_colors


