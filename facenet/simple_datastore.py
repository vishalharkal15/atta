
import os
import sqlite3
import numpy as np
from PIL import Image
from pathlib import Path
import logging
import cv2

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from mtcnn import MTCNN
except ImportError:
    logger.error("Missing MTCNN. Install with: pip install mtcnn")
    exit(1)

class SimpleFaceStorage:
    """Simplified face storage system using basic features."""
    
    def __init__(self, db_path='data/database/faces.db'):
        self.db_path = db_path
        self.detector = MTCNN()
        self.conn = None
        self.cursor = None
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
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
        
        self.cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_name ON faces(name)
        ''')
        
        self.conn.commit()
        logger.info(f"✅ Database initialized: {self.db_path}")
    
    def extract_face(self, image_path, required_size=(160, 160)):
        """Extract face from image."""
        try:
            image = Image.open(image_path)
            image = image.convert('RGB')
            pixels = np.asarray(image)
            
            results = self.detector.detect_faces(pixels)
            
            if len(results) == 0:
                logger.warning(f"❌ No face detected: {image_path}")
                return None
            
            best_result = max(results, key=lambda x: x['confidence'])
            x1, y1, width, height = best_result['box']
            x1, y1 = abs(x1), abs(y1)
            x2, y2 = x1 + width, y1 + height
            
            face = pixels[y1:y2, x1:x2]
            face_image = Image.fromarray(face)
            face_image = face_image.resize(required_size)
            
            logger.info(f"✅ Face extracted from {image_path} (confidence: {best_result['confidence']:.2f})")
            return np.asarray(face_image)
            
        except Exception as e:
            logger.error(f"❌ Error processing {image_path}: {e}")
            return None
    
    def get_simple_features(self, face_pixels):
        """Generate simple features from face (placeholder for FaceNet)."""
        try:
            # Convert to grayscale and flatten
            gray = cv2.cvtColor(face_pixels, cv2.COLOR_RGB2GRAY)
            
            # Simple statistical features (not as good as FaceNet but works)
            features = []
            
            # Mean intensity in different regions
            h, w = gray.shape
            regions = [
                gray[:h//2, :w//2],      # Top-left
                gray[:h//2, w//2:],      # Top-right
                gray[h//2:, :w//2],      # Bottom-left
                gray[h//2:, w//2:]       # Bottom-right
            ]
            
            for region in regions:
                features.extend([
                    np.mean(region),
                    np.std(region),
                    np.min(region),
                    np.max(region)
                ])
            
            # Add histogram features
            hist = cv2.calcHist([gray], [0], None, [32], [0, 256])
            features.extend(hist.flatten())
            
            # Normalize to create a 128-dimensional vector (like FaceNet)
            features = np.array(features)
            if len(features) > 128:
                features = features[:128]
            elif len(features) < 128:
                features = np.pad(features, (0, 128 - len(features)), 'constant')
            
            # Normalize
            features = features / (np.linalg.norm(features) + 1e-8)
            
            return features.astype(np.float32)
            
        except Exception as e:
            logger.error(f"❌ Error generating features: {e}")
            return None
    
    def save_face(self, name, features):
        """Save face features to database."""
        try:
            emb_bytes = features.astype(np.float32).tobytes()
            
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
        
        features = self.get_simple_features(face)
        if features is None:
            return False
        
        return self.save_face(name, features)
    
    def process_dataset(self, images_dict):
        """Process multiple images."""
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
    
    def process_imgs_directory(self, imgs_dir='data/imgs'):
        """
        Automatically process all images in the imgs directory.
        Expected structure:
        data/imgs/
        ├── person1/
        │   ├── photo1.jpg
        │   └── photo2.png
        ├── person2/
        │   └── image.jpeg
        └── single_images/
            ├── John_Doe.jpg
            └── Jane_Smith.png
        """
        imgs_path = Path(imgs_dir)
        if not imgs_path.exists():
            logger.error(f"❌ Images directory not found: {imgs_dir}")
            return
        
        processed_count = 0
        total_files = 0
        
        # Supported image extensions
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
        
        logger.info(f"🔍 Scanning directory: {imgs_path.absolute()}")
        
        # Process folders (each folder = one person)
        for person_dir in imgs_path.iterdir():
            if person_dir.is_dir():
                person_name = person_dir.name
                logger.info(f"👤 Processing person: {person_name}")
                
                # Find all images in person's folder
                person_images = []
                for img_file in person_dir.iterdir():
                    if img_file.is_file() and img_file.suffix.lower() in image_extensions:
                        person_images.append(img_file)
                        total_files += 1
                
                # Process each image for this person
                for img_file in person_images:
                    if self.process_single_image(person_name, str(img_file)):
                        processed_count += 1
                        logger.info(f"  ✅ {img_file.name}")
                    else:
                        logger.warning(f"  ❌ Failed: {img_file.name}")
        
        # Process individual files (filename = person name)
        for img_file in imgs_path.iterdir():
            if img_file.is_file() and img_file.suffix.lower() in image_extensions:
                # Extract name from filename (remove extension)
                person_name = img_file.stem.replace('_', ' ').replace('-', ' ')
                total_files += 1
                
                if self.process_single_image(person_name, str(img_file)):
                    processed_count += 1
                    logger.info(f"✅ {person_name} from {img_file.name}")
                else:
                    logger.warning(f"❌ Failed: {img_file.name}")
        
        logger.info(f"📊 Processed {processed_count}/{total_files} images from {imgs_dir}")
        return processed_count, total_files
    
    def scan_and_add_from_downloads(self):
        """Scan Downloads folder for face images and add them."""
        downloads_path = Path.home() / "Downloads"
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
        
        found_images = []
        for img_file in downloads_path.iterdir():
            if img_file.is_file() and img_file.suffix.lower() in image_extensions:
                # Try to extract name from filename
                name = img_file.stem.replace('_', ' ').replace('-', ' ')
                found_images.append((name, str(img_file)))
        
        if found_images:
            logger.info(f"🔍 Found {len(found_images)} images in Downloads")
            success_count = 0
            
            for name, path in found_images:
                if self.process_single_image(name, path):
                    success_count += 1
            
            logger.info(f"✅ Successfully processed {success_count}/{len(found_images)} from Downloads")
        else:
            logger.info("📂 No images found in Downloads folder")
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("✅ Database connection closed")


def main():
    """Main function with multiple processing options."""
    system = SimpleFaceStorage()
    
    logger.info("🚀 Face Database Image Processor")
    logger.info("=" * 50)
    
    # Option 1: Process from data/imgs directory
    processed, total = system.process_imgs_directory('data/imgs')
    
    # Option 2: Also scan Downloads folder if imgs directory is empty
    if total == 0:
        logger.info("📂 No images in data/imgs, scanning Downloads folder...")
        system.scan_and_add_from_downloads()
    
    # Option 3: Process specific images (fallback)
    if system.get_face_count() == 0:
        logger.info("🔄 Processing specific images as fallback...")
        specific_images = {
            "Aheed Khan": "/home/vishal/Downloads/Aheed Khan.jpg",
            "Mohit": "/home/vishal/Downloads/Mohit.jpg", 
            "Vishal": "/home/vishal/Downloads/vishal.jpg"
        }
        
        valid_images = {}
        for name, path in specific_images.items():
            if os.path.exists(path):
                valid_images[name] = path
        
        if valid_images:
            system.process_dataset(valid_images)
    
    # Final summary
    count = system.get_face_count()
    names = system.get_all_names()
    logger.info("=" * 50)
    logger.info(f"📊 Database Summary:")
    logger.info(f"   Total faces: {count}")
    logger.info(f"   People: {', '.join(names) if names else 'None'}")
    
    system.close()


def create_sample_structure():
    """Create sample directory structure for testing."""
    base_path = Path('data/imgs')
    base_path.mkdir(exist_ok=True)
    
    # Create sample folders
    sample_people = ['John_Doe', 'Jane_Smith', 'Alice_Johnson']
    
    for person in sample_people:
        person_dir = base_path / person
        person_dir.mkdir(exist_ok=True)
        
        # Create a README file explaining the structure
        readme_path = person_dir / 'README.txt'
        readme_path.write_text(f"Place {person.replace('_', ' ')}'s photos here.\nSupported formats: jpg, png, jpeg, bmp, tiff, webp")
    
    # Create main README
    main_readme = base_path / 'README.txt'
    main_readme.write_text("""
Face Images Directory Structure:

Option 1 - Organized by person (folders):
data/imgs/
├── person_name/
│   ├── photo1.jpg
│   ├── photo2.png
│   └── ...

Option 2 - Single files (filename = name):
data/imgs/
├── John_Doe.jpg
├── Jane_Smith.png
└── Alice_Johnson.jpeg

Supported formats: jpg, jpeg, png, bmp, tiff, webp
The system will automatically process all images and create face embeddings.
""")
    
    logger.info(f"📁 Created sample directory structure in {base_path.absolute()}")
    logger.info("📝 Check README.txt files for usage instructions")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--create-structure':
        create_sample_structure()
    else:
        main()