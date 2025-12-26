from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.ml_service import ml_service

router = APIRouter()

@router.post("/predict", summary="Определить печати и подписи")
async def detect_signatures(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    content = await file.read()
    results = ml_service.predict(content, file.filename)
    
    return {"filename": file.filename, "results": results}