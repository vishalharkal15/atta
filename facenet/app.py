import os
import io
import json
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS
from mtcnn import MTCNN
from keras_facenet import FaceNet
from PIL import Image
import numpy as np

# ------------------------------
# Environment & Flask Setup
# ------------------------------
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"  # Suppress TensorFlow GPU warnings

app = Flask(__name__)
CORS(app)  # Enable CORS for all origins (for development)

# ------------------------------
# FaceNet & MTCNN Initialization
# ------------------------------
detector = MTCNN()
embedder = FaceNet()

# ------------------------------
# Embeddings Data File
# ------------------------------
DATA_PATH = "data/embeddings.json"
os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)  # Auto-create folder

# Create empty JSON file if it doesn't exist
if not os.path.exists(DATA_PATH):
    with open(DATA_PATH, "w") as f:
        json.dump({}, f)

# ------------------------------
# Helper Functions
# ------------------------------
def load_embeddings():
    with open(DATA_PATH, "r") as f:
        return json.load(f)

def save_embeddings(data):
    with open(DATA_PATH, "w") as f:
        json.dump(data, f)

# ------------------------------
# /enroll Endpoint
# ------------------------------
@app.route("/enroll", methods=["POST"])
def enroll():
    try:
        data = request.json
        name = data["name"]
        image_data = data["image"].split(",")[1]  # Remove base64 prefix
        image = Image.open(io.BytesIO(base64.b64decode(image_data)))

        faces = detector.detect_faces(np.array(image))
        if not faces:
            return jsonify({"error": "No face detected"}), 400

        embeddings = []
        for face in faces:
            x, y, w, h = face["box"]
            face_crop = image.crop((x, y, x + w, y + h))
            embedding = embedder.embeddings([np.array(face_crop)])[0].tolist()
            embeddings.append(embedding)

        db = load_embeddings()
        db[name] = embeddings
        save_embeddings(db)

        return jsonify({"message": f"User {name} enrolled", "faces_detected": len(embeddings)})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ------------------------------
# /recognize Endpoint
# ------------------------------
@app.route("/recognize", methods=["POST"])
def recognize():
    try:
        data = request.json
        image_data = data["image"].split(",")[1]
        image = Image.open(io.BytesIO(base64.b64decode(image_data)))

        faces = detector.detect_faces(np.array(image))
        if not faces:
            return jsonify({"error": "No face detected"}), 400

        db = load_embeddings()
        results = []

        for face in faces:
            x, y, w, h = face["box"]
            face_crop = image.crop((x, y, x + w, y + h))
            emb = embedder.embeddings([np.array(face_crop)])[0]

            match_name = "Unknown"
            min_dist = 1.0  # Distance threshold

            for name, emb_list in db.items():
                for stored_emb in emb_list:
                    dist = np.linalg.norm(emb - np.array(stored_emb))
                    if dist < min_dist and dist < 1.0:  # Adjust threshold if needed
                        min_dist = dist
                        match_name = name

            results.append({"name": match_name, "bbox": [x, y, w, h]})

        return jsonify({"faces": results})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ------------------------------
# Run Flask Server
# ------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
