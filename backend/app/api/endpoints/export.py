from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.pdf_generator import generate_analytics_pdf
from app.models.user import User
from app.api.dependencies import get_current_user
from app.core.database import get_db

# Создаем новый роутер специально для экспорта аналитики
router = APIRouter(prefix="/export", tags=["Export"])

@router.get("/analytics-pdf")
async def export_analytics_pdf(
    start_year: int = Query(2022),
    end_year: int = Query(2025),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # В РЕАЛЬНОСТИ: Здесь будет логика сбора реальных данных через db.execute
    
    # ДЛЯ ПРИМЕРА: Mock-данные, чтобы протестировать генерацию PDF
    mock_data = {
        "start_year": start_year,
        "end_year": end_year,
        "total_orgs": 145,
        "yearly_data": [
            {"year": 2022, "fact": 390509, "plan": 393401},
            {"year": 2023, "fact": 420000, "plan": 410000},
            {"year": 2024, "fact": 450000, "plan": 440000},
            {"year": 2025, "fact": 384379, "plan": 470000}
        ]
    }

    # Генерируем PDF (функция вернет поток байтов)
    pdf_buffer = generate_analytics_pdf(mock_data)

    filename = f"Analytics_Report_{start_year}_{end_year}.pdf"
    
    # Отдаем файл клиенту
    return StreamingResponse(
        pdf_buffer, 
        media_type="application/pdf", 
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )