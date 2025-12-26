import io
from PIL import Image
from ultralytics import YOLO
from pdf2image import convert_from_bytes
import os
import json

# Путь к модели
MODEL_PATH = "app/models/yolo_model.pt"

class MLService:
    def __init__(self):
        if os.path.exists(MODEL_PATH):
            self.model = YOLO(MODEL_PATH)
        else:
            print(f"Warning: Model not found at {MODEL_PATH}")
            self.model = None

    def predict(self, file_bytes: bytes, filename: str):
        if not self.model:
            return {"error": "Model not loaded"}

        images = []
        if filename.lower().endswith(".pdf"):
            try:
                images = convert_from_bytes(file_bytes)
            except Exception as e:
                return {"error": f"PDF conversion failed: {str(e)}"}
        else:
            image = Image.open(io.BytesIO(file_bytes))
            images = [image]

        results_data = []

        for i, img in enumerate(images):
            results = self.model(img)
            
            for result in results:
                # ИСПРАВЛЕНИЕ: используем to_json()
                json_str = result.to_json()
                
                # Парсим строку в объект, чтобы фронтенд получил нормальный JSON
                try:
                    detections = json.loads(json_str)
                except:
                    detections = []

                results_data.append({
                    "page": i + 1,
                    "detections": detections
                })

        return results_data

ml_service = MLService()