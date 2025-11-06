from flask import Flask
from flask_cors import CORS
from mtcnn import MTCNN
from keras_facenet import FaceNet
import os

# Initialize Flask
app = Flask(__name__)
CORS(app)

# Initialize DB
from database import init_db
db, Attendance, Student = init_db(app)

# Initialize FaceNet & MTCNN
detector = MTCNN()
embedder = FaceNet()

# Register routes
from routes import register_routes
register_routes(app, db, Attendance, detector, embedder)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
