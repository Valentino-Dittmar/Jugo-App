import cv2
import numpy as np
from sklearn.cluster import KMeans
import matplotlib.colors as mcolors

def run_compliance_check(image, detections, user_hex):
    print("✅ run_compliance_check was called with user color:", user_hex)

    user_rgb = tuple(int(255 * x) for x in mcolors.to_rgb(user_hex))

    allowed_colors = [
        (255, 0, 0),     # red
        (0, 255, 0),     # green
        (128, 128, 128), # gray
        (0, 0, 0),       # black
        (248, 5, 5),     # bright red
        (120, 77, 77),   # typography shade
        user_rgb
    ]

    neutral_colors = [
        (242, 242, 242),
        (243, 243, 243),
        (255, 255, 255),
        (250, 250, 250),
        (245, 245, 245)
    ]

    def color_distance(c1, c2):
        return np.linalg.norm(np.array(c1) - np.array(c2))

    def is_ibcs_compliant(detected_colors, allowed, neutral, threshold=100):
        for color in detected_colors:
            distances = [color_distance(color, ref) for ref in allowed + neutral]
            if min(distances) > threshold:
                print(f"❌ Non-compliant color detected: {color}")
                return False, color
        return True, None

    def get_dominant_colors(crop, k=3):
        img_rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
        img_rgb = img_rgb.reshape((-1, 3))
        kmeans = KMeans(n_clusters=k, n_init=10)
        kmeans.fit(img_rgb)
        return [tuple(map(int, center)) for center in kmeans.cluster_centers_]

    if image is None:
        raise ValueError("Image is empty. YOLOv5 may not have saved output correctly.")

    non_compliant = False
    non_compliant_colors = []

    annotations = []

    for det in detections:
        x_center, y_center, w, h = det
        x1 = int((x_center - w / 2) * image.shape[1])
        y1 = int((y_center - h / 2) * image.shape[0])
        x2 = int((x_center + w / 2) * image.shape[1])
        y2 = int((y_center + h / 2) * image.shape[0])
        crop = image[y1:y2, x1:x2]

        if crop.size == 0:
            print("⚠️ Empty crop for detection:", det)
            continue

        dominant_colors = get_dominant_colors(crop)
        print("🎨 Dominant colors for crop:", dominant_colors)

        compliant, bad_color = is_ibcs_compliant(dominant_colors, allowed_colors, neutral_colors)

        if not compliant:
            non_compliant_colors.append(bad_color)
            annotations.append({
                "bbox": (x1, y1, x2, y2),
                "label": "Non-compliant",
                "color": (0, 0, 255),
                "thickness": 3,
                "font_scale": 0.6,
                "font_thickness": 2
            })
            non_compliant = True

    formatted_colors = []
    for color in non_compliant_colors:
        r, g, b = color
        html = f"RGB ({r}, {g}, {b}) <span style='display:inline-block; width:16px; height:16px; margin-left:8px; background-color: rgb({r},{g},{b}); border: 1px solid #000;'></span>"
        formatted_colors.append(html)

    return non_compliant, annotations, formatted_colors

