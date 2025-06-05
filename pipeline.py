from ultralytics import YOLO
import cv2
import os
from compliance_checker import run_compliance_check
from compliance_checker_2 import run_compliance_check_2

def run_full_pipeline(image_path, user_hex):
    # === Step 1: Load model ===
    model = YOLO("./yolov5_weights/best.pt")

    # === Step 2: Run prediction ===
    results = model.predict(source=image_path, save=False, conf=0.25)

    # === Step 3: Load image ===
    result_image = cv2.imread(image_path)
    if result_image is None:
        raise ValueError(f"Could not load original image from {image_path}")

    # === Step 4: Extract detections from results ===
    detections = []

    for r in results:
        img_h, img_w = r.orig_shape[:2]
        for box in r.boxes.xywh:  # Absolute pixel values
            x, y, w, h = box.cpu().numpy().tolist()
            # Normalize manually (0–1 range)
            norm_x = x / img_w
            norm_y = y / img_h
            norm_w = w / img_w
            norm_h = h / img_h
            detections.append([norm_x, norm_y, norm_w, norm_h])

    # === Step 5: Run color compliance check ===
    non_color_compliant, annotations, formatted_colors = run_compliance_check(result_image, detections, user_hex)

    # === Step 6: Run direction compliance check ===
    non_direction_compliant, inf_img, reasons = run_compliance_check_2(result_image)

    # === Step 7: Draw bounding box for non color compliant charts ===
    if annotations:
        for ann in annotations:
            x1, y1, x2, y2 = ann["bbox"]
            color = ann["color"]
            thickness = ann["thickness"]
            inf_img = cv2.rectangle(inf_img, (x1, y1), (x2, y2), color, thickness)
            inf_img = cv2.putText(inf_img, ann["label"], (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                ann["font_scale"], color, ann["font_thickness"])
            
    # === Step 8: Determine final compliancy status ===
    compliance = False

    if non_color_compliant == False:
        compliance = True
    elif non_direction_compliant == False:
        compliance = True

    # === Step 9: Return values for final output ===
    _, buffer = cv2.imencode('.png', inf_img)

    return compliance, buffer.tobytes(), formatted_colors, reasons