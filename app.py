import os
import uuid
import base64
import json
from flask import Flask, render_template, request, jsonify, url_for
import openai

# Initialize Flask app
app = Flask(__name__)
# Set your OpenAI API key


UPLOAD_DIR = os.path.join(app.static_folder, 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/check', methods=['POST'])
def check_ibcs():
    data = request.get_json()
    img_b64 = data.get('image')
    if not img_b64:
        return jsonify({'error': 'No image provided'}), 400

    try:
        img_data = base64.b64decode(img_b64)
        filename = f"{uuid.uuid4().hex}.jpg"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, 'wb') as f:
            f.write(img_data)
        image_url = request.url_root.rstrip('/') + url_for('static', filename=f'uploads/{filename}')
    except Exception as e:
        return jsonify({'error': f'Failed to save image: {e}'}), 500

    try:
        resp = openai.chat.completions.create(
            model='gpt-4o',
            messages=[
                {"role": "system", "content": (
                    "You are a vision-capable AI expert. Analyze provided chart images for IBCS compliance. "
                    "Respond ONLY with a JSON: {\"likelihood\": <0-100>, \"explanation\": <string>}."
                )},
                {"role": "user", "content": [
                    {"type": "text", "text": "Please assess this chart for IBCS compliance:"},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]}
            ],
            max_tokens=500
        )
        raw = resp.choices[0].message.content.strip()

        # Extract JSON part
        start = raw.find('{')
        end = raw.rfind('}') + 1
        if start == -1 or end == -1:
            return jsonify({'error': 'Invalid JSON from AI', 'raw': raw}), 500
        json_str = raw[start:end]
        result = json.loads(json_str)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True)
