"""
Production-level Face Recognition Embedding System
Extracts faces, generates FaceNet embeddings, and stores in SQLite database.
"""

import os
import sqlite3
import numpy as np
from PIL import Image
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from mtcnn import MTCNN
    from keras.models import load_model
except ImportError as e:
    logger.error(f"Missing dependencies: {e}")
    logger.info("Install with: pip install mtcnn tensorflow keras pillow")
    exit(1)

class FaceEmbeddingSystem:
    """Production-ready face embedding and storage system."""
    
    def __init__(self, db_path='data/database/faces.db', model_path=None):
        """
        Initialize the face embedding system.
        
        Args:
            db_path: Path to SQLite database file
            model_path: Path to FaceNet model (optional, will try to find or download)
        """
        self.db_path = db_path
        self.detector = MTCNN()
        self.model = None
        self.conn = None
        self.cursor = None
        
        # Initialize database
        self._init_database()
        
        # Load or download FaceNet model
        self._load_model(model_path)
    
    def _init_database(self):
        """Initialize SQLite database with proper schema."""
        # Ensure database directory exists
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        # Connect and create table
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS faces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            embedding BLOB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create index for faster name lookups
        self.cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_name ON faces(name)
        ''')
        
        self.conn.commit()
        logger.info(f"✅ Database initialized: {self.db_path}")
    
    def _load_model(self, model_path):
        """Load FaceNet model with fallback options."""
        model_paths = [
            model_path,
            'facenet_keras.h5',
            '../facenet_keras.h5',
            '../../facenet_keras.h5'
        ]
        
        for path in model_paths:
            if path and os.path.exists(path):
                try:
                    self.model = load_model(path)
                    logger.info(f"✅ Loaded FaceNet model: {path}")
                    return
                except Exception as e:
                    logger.warning(f"Failed to load model {path}: {e}")
        
        # Fallback: try to use a pre-trained model or warn user
        logger.warning("⚠️ FaceNet model not found. Please provide facenet_keras.h5")
        logger.info("You can download from: https://drive.google.com/drive/folders/1pwQ3H4aJ8a6yyJHGkOwtjcTvncHrXpmP")
        self.model = None
    
    def extract_face(self, image_path, required_size=(160, 160)):
        """
        Extract and preprocess face from image.
        
        Args:
            image_path: Path to image file
            required_size: Target face size for FaceNet (160x160)
            
        Returns:
            numpy.ndarray: Preprocessed face pixels or None if no face found
        """
        try:
            # Load and convert image
            image = Image.open(image_path)
            image = image.convert('RGB')
            pixels = np.asarray(image)
            
            # Detect faces
            results = self.detector.detect_faces(pixels)
            
            if len(results) == 0:
                logger.warning(f"❌ No face detected: {image_path}")
                return None
            
            # Extract the largest face (highest confidence)
            best_result = max(results, key=lambda x: x['confidence'])
            x1, y1, width, height = best_result['box']
            
            # Ensure coordinates are positive
            x1, y1 = abs(x1), abs(y1)
            x2, y2 = x1 + width, y1 + height
            
            # Extract and resize face
            face = pixels[y1:y2, x1:x2]
            face_image = Image.fromarray(face)
            face_image = face_image.resize(required_size)
            
            logger.info(f"✅ Face extracted from {image_path} (confidence: {best_result['confidence']:.2f})")
            return np.asarray(face_image)
            
        except Exception as e:
            logger.error(f"❌ Error processing {image_path}: {e}")
            return None
    
    def get_embedding(self, face_pixels):
        """
        Generate FaceNet embedding from face pixels.
        
        Args:
            face_pixels: Preprocessed face image as numpy array
            
        Returns:
            numpy.ndarray: 128-dimensional face embedding
        """
        if self.model is None:
            logger.error("❌ FaceNet model not loaded")
            return None
        
        try:
            # Normalize pixels
            face_pixels = face_pixels.astype('float32')
            mean, std = face_pixels.mean(), face_pixels.std()
            face_pixels = (face_pixels - mean) / std
            
            # Add batch dimension and predict
            samples = np.expand_dims(face_pixels, axis=0)
            embedding = self.model.predict(samples, verbose=0)
            
            return embedding[0]
            
        except Exception as e:
            logger.error(f"❌ Error generating embedding: {e}")
            return None
    
    def save_face(self, name, embedding):
        """
        Save face embedding to database.
        
        Args:
            name: Person's name
            embedding: Face embedding vector
            
        Returns:
            bool: Success status
        """
        try:
            # Convert embedding to bytes
            emb_bytes = embedding.astype(np.float32).tobytes()
            
            # Insert into database
            self.cursor.execute(
                "INSERT INTO faces (name, embedding) VALUES (?, ?)",
                (name, emb_bytes)
            )
            self.conn.commit()
            
            logger.info(f"✅ Saved {name} in database")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving {name}: {e}")
            return False
    
    def process_single_image(self, name, image_path):
        """Process a single image and save to database."""
        face = self.extract_face(image_path)
        if face is None:
            return False
        
        embedding = self.get_embedding(face)
        if embedding is None:
            return False
        
        return self.save_face(name, embedding)
    
    def process_dataset(self, images_dict):
        """
        Process multiple images from a dictionary.
        
        Args:
            images_dict: Dict mapping names to image paths
        """
        success_count = 0
        total_count = len(images_dict)
        
        logger.info(f"🚀 Processing {total_count} images...")
        
        for name, path in images_dict.items():
            if self.process_single_image(name, path):
                success_count += 1
        
        logger.info(f"✅ Processed {success_count}/{total_count} images successfully")
    
    def get_face_count(self):
        """Get total number of faces in database."""
        self.cursor.execute("SELECT COUNT(*) FROM faces")
        return self.cursor.fetchone()[0]
    
    def get_all_names(self):
        """Get all unique names in database."""
        self.cursor.execute("SELECT DISTINCT name FROM faces")
        return [row[0] for row in self.cursor.fetchall()]
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("✅ Database connection closed")


def main():
    """Main function to process the specific images."""
    # Initialize the system
    system = FaceEmbeddingSystem(db_path='data/database/faces.db')
    
    # Define images to process
    images = {
        "Aheed Khan": "/home/vishal/Downloads/Aheed Khan.jpg",
        "Mohit": "/home/vishal/Downloads/Mohit.jpg", 
        "Vishal": "/home/vishal/Downloads/vishal.jpg"
    }
    
    # Verify files exist
    valid_images = {}
    for name, path in images.items():
        if os.path.exists(path):
            valid_images[name] = path
        else:
            logger.warning(f"⚠️ Image not found: {path}")
    
    if not valid_images:
        logger.error("❌ No valid images found")
        return
    
    # Process all images
    system.process_dataset(valid_images)
    
    # Print summary
    count = system.get_face_count()
    names = system.get_all_names()
    logger.info(f"📊 Database now contains {count} face(s) for: {', '.join(names)}")
    
    # Close database
    system.close()


if __name__ == "__main__":
    main()
