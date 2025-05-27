import subprocess

def run_yolo_detection(image_path):
    yolo_path = "yolov5"
    weights_path = "/Users/pavelakaradzhova/Documents/S4 Group Project/ibcs_checker/yolov5_weights/best.pt"

    subprocess.run([
        "python3", "detect.py",
        "--weights", weights_path,
        "--img", "640",
        "--conf", "0.25",
        "--source", image_path,
        "--save-txt",
        "--project", "runs/detect",
        "--name", "webinput",
        "--exist-ok"
    ], cwd=yolo_path)

# Test it on another image
run_yolo_detection("/Users/pavelakaradzhova/Documents/S4 Group Project/customcomplientrgba.png")  # <- Replace with your image path
