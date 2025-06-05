import os, base64, json, openai
from flask import Flask, render_template, request, redirect
from werkzeug.utils import secure_filename
from pipeline import run_full_pipeline

UPLOAD_FOLDER = "uploads"
ALLOWED_EXT = {"png", "jpg", "jpeg", "gif"}
VISION_MODEL = "gpt-4.1"
openai.api_key = os.getenv("OPENAI_API_KEY")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def allowed(fname):
    return "." in fname and fname.rsplit(".", 1)[1].lower() in ALLOWED_EXT

@app.route("/", methods=["GET", "POST"])
def index():
    result = img_b64 = None
    issues = []
    non_compliant_colors = []

    if request.method == "POST":
        f = request.files.get("file")
        color = request.form.get("color")
        if not (f and color and allowed(f.filename)):
            return redirect("/")

        path = os.path.join(UPLOAD_FOLDER, secure_filename(f.filename))
        f.save(path)

        result, img_bytes, non_compliant_colors, non_compliant_direction = run_full_pipeline(path, color)
        if img_bytes:
            img_b64 = base64.b64encode(img_bytes).decode()
            try:
                resp = openai.chat.completions.create(
                model=VISION_MODEL,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an IBCS-certified consultant. "
                            "Analyze the given dashboard image for both **color compliance** and **direction compliance**."
                            f"Use the {non_compliant_direction} and {non_compliant_colors} as reason for non compliance."
                            "Return ONLY this JSON structure: "
                            "{\"issues\":[{\"location\":\"...\",\"issue\":\"...\",\"fix\":\"...\"}]}"
                            "If there is no issue found at all for both color and direction, return ONLY this JSON:"
                            "{\"issues\":[{\"result\":\"No IBCS rule violation is found.\"}]}"
                        ),
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "Return your answer as JSON. "
                                    "List every IBCS compliance problem in this dashboard — including color and direction issues — and how to fix them."
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
                issues = json.loads(resp.choices[0].message.content).get("issues", [])
            except Exception as e:
                issues = [{"location": "⚠️ AI feedback unavailable", "issue": str(e), "fix": ""}]
        else:
            issues = [{"location": "⚠️", "issue": "No processed image returned from pipeline.", "fix": ""}]

    return render_template(
        "index.html",
        result=result,
        image_data=img_b64,
        issues=issues,
        non_compliant_colors=non_compliant_colors
    )

@app.route("/delete_images", methods=["POST"])
def delete_images():
    import shutil
    for entry in os.listdir(UPLOAD_FOLDER):
        p = os.path.join(UPLOAD_FOLDER, entry)
        try:
            shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
        except Exception:
            pass
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)