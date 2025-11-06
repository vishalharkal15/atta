# Automated Attendance System

Face recognition-based automated attendance system using FaceNet and MTCNN.

## Deployment

### Option 1: Docker

```bash
cd facenet
docker build -t atta-backend .
docker run -p 5000:5000 atta-backend
```

### Option 2: Render

1. Push your code to GitHub
2. Connect your repository to Render
3. Render will automatically detect `render.yaml`
4. Deploy!

### Option 3: Railway/Heroku

1. Push your code to GitHub
2. Connect to Railway/Heroku
3. The `Procfile` will be automatically detected
4. Set environment variable: `PYTHON_VERSION=3.12.3`
5. Deploy!

## Local Development

### Backend (Flask)

```bash
cd facenet
python3 -m venv ../.venv
source ../.venv/bin/activate  # On Windows: ..\.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Backend runs on: http://localhost:5000

### Frontend (React/Vite)

```bash
npm install
npm run dev
```

Frontend runs on: http://localhost:5173/Automated-Attendance/

## Environment Variables

- `PORT`: Server port (default: 5000)
- `FLASK_APP`: Flask application entry point (default: app.py)

## Technologies

- **Backend**: Flask, TensorFlow, FaceNet, MTCNN
- **Frontend**: React, Vite
- **Database**: SQLAlchemy

## API Endpoints

Document your API endpoints here...
