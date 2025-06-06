from compliance_checker import run_compliance_check

image_path = "yolov5/runs/detect/webinput/customcomplientrgba.png"
label_path = "yolov5/runs/detect/webinput/labels/customcomplientrgba.txt"
output_path = "yolov5/runs/detect/webinput/customcomplientrgba_compliance.png"
user_hex = "#448294"  # or any other highlight color the user chose

result = run_compliance_check(image_path, label_path, user_hex, output_path)

if result:
    print("✅ This dashboard is IBCS-compliant.")
else:
    print("❌ This dashboard is NOT compliant. See red boxes on the image.")
