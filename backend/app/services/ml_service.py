import io
from PIL import Image
from ultralytics import YOLO
from pdf2image import convert_from_bytes
import os

# Путь к модели (убедитесь, что файл лежит здесь)
MODEL_PATH = "app/models/yolo_model.pt"

class MLService:
    def __init__(self):
        # Загружаем модель один раз при старте, если файл существует
        if os.path.exists(MODEL_PATH):
            self.model = YOLO(MODEL_PATH)
        else:
            print(f"Warning: Model not found at {MODEL_PATH}")
            self.model = None

    def predict(self, file_bytes: bytes, filename: str):
        if not self.model:
            return {"error": "Model not loaded"}

        images = []
        # Если PDF, конвертируем в картинки
        if filename.lower().endswith(".pdf"):
            try:
                images = convert_from_bytes(file_bytes)
            except Exception as e:
                return {"error": f"PDF conversion failed: {str(e)}"}
        else:
            # Если картинка
            image = Image.open(io.BytesIO(file_bytes))
            images = [image]

        results_data = []

        for i, img in enumerate(images):
            # Прогон через YOLO
            results = self.model(img)
            
            for result in results:
                # Получаем JSON с координатами
                json_result = result.to_json()
                results_data.append({
                    "page": i + 1,
                    "detections": json_result
                })

        return results_data

# Создаем глобальный экземпляр сервиса
ml_service = MLService()