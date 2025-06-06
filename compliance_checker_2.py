from matplotlib import image as mpimg
from ultralytics import YOLO
import base64, openai, json, os
from dotenv import load_dotenv
import cv2

def run_compliance_check_2(image):
    # Load trained YOLOv8 model for chart detection
    model = YOLO("./yolov8_weights/chart_detection/best.pt")  # Use best trained model

    result = model.predict(source=image, save=False, show=False)

    inf_img = image

    # Retrieve OpenAI API key from env file
    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")

    # Define OpenAI API request
    VISION_MODEL = "gpt-4.1"

    non_compliant_count = 0

    reasons = []

    for r in result:
        label = r.boxes.xywh.numpy()  # Convert YOLO output to NumPy (x_center, y_center, width, height)

        # Process each bounding box separately
        for i, (x_center, y_center, width, height) in enumerate(label):
            # Convert YOLO format (x_center, y_center, width, height) to standard bounding box format
            x_min_chart = int(x_center - width/2)
            y_min_chart = int(y_center - height/2)
            x_max_chart = int(x_center + width/2)
            y_max_chart = int(y_center + height/2)

            chart = inf_img[y_min_chart:y_max_chart, x_min_chart:x_max_chart]

            # Load trained YOLOv8 model for axes detection
            model = YOLO("./yolov8_weights/axes_detection/best.pt")  # Use best trained model

            result = model.predict(source=chart, save=False, show=False)

            for r in result:
                label = r.boxes.xywh.numpy()  # Convert YOLO output to NumPy (x_center, y_center, width, height)

                # Process each bounding box separately
                for i, (x_center, y_center, width, height) in enumerate(label):
                    # Convert YOLO format (x_center, y_center, width, height) to standard bounding box format
                    x_min = int(x_center - width/2)
                    y_min = int(y_center - height/2)
                    x_max = int(x_center + width/2)
                    y_max = int(y_center + height/2)

                    # Draw bounding box for detected axes
                    annotated_img = chart.copy()
                    annotated_img = cv2.rectangle(annotated_img, (x_min, y_min), (x_max, y_max), (0, 0, 255), 4)  # Red box
                    annotated_img = cv2.putText(annotated_img, "Chart", (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

            # Convert processed image to Base64 format
            _, buffer = cv2.imencode(".png", annotated_img)
            img_b64 = base64.b64encode(buffer).decode("utf-8")  # Encode image

            # Send request to OpenAI
            resp = openai.chat.completions.create(
                model=VISION_MODEL,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an optical character recognizer. "
                            "Return ONLY this JSON structure: "
                            "{\"issues\":[{\"x_is_time\":\"yes or no\",\"y_is_time\":\"yes or no\",\"x_is_number\":\"yes or no\"},\"y_is_number\":\"yes or no\"]}"
                        ),
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "Return your answer as JSON. "
                                    "For the chart, determine if: x-axis is time? x-axis is number? y-axis is time? and y-axis is number? Based on the chart title. DO NOT ANALYZE the meaning of the text."
                                ),
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{img_b64}"},
                            },
                        ],
                    },
                ],
                max_tokens=500,
            )

            # Extract issues from response
            issues = json.loads(resp.choices[0].message.content).get("issues", [])

            for issue in issues:
                # Condition for time-series
                if issue['y_is_time'] == 'yes' and issue['x_is_time'] == 'no':
                    non_compliant_count += 1

                    inf_img = inf_img.copy()
                    inf_img = cv2.rectangle(inf_img, (x_min_chart, y_min_chart), (x_max_chart, y_max_chart), (128, 0, 128), 4)  # Red box
                    inf_img = cv2.putText(inf_img, "Non-compliant Direction", (x_min_chart, max(y_min_chart - 10, 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (128, 0, 128), 2)

                    reason = "Time-series should always be aligned left to right horizontally on the x-axis."
                    reasons.append(reason)

                # Condition for non-time-series
                elif issue['y_is_time'] == 'no' and issue['x_is_time'] == 'no':
                    if issue['y_is_number'] == 'yes' and issue['x_is_number'] == 'no':
                        non_compliant_count += 1

                        inf_img = inf_img.copy()
                        inf_img = cv2.rectangle(inf_img, (x_min_chart, y_min_chart), (x_max_chart, y_max_chart), (128, 0, 128), 4)  # Red box
                        inf_img = cv2.putText(inf_img, "Non-compliant Direction", (x_min_chart, max(y_min_chart - 10, 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (128, 0, 128), 2)

                        reason = "Non-time-series should always be aligned from top to bottom vertically on the y-axis."
                        reasons.append(reason)

    non_compliant = False

    if non_compliant_count != 0:
        non_compliant = True

        return non_compliant, inf_img, reasons
    else:
        return non_compliant, inf_img, reasons