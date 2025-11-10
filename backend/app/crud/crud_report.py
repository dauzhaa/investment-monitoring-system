
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.investment_report import ReportCreate
from app.models import User, Organization, InvestmentReport

async def create_report(report_in: ReportCreate, user: User, organization: Organization, db: AsyncSession) -> InvestmentReport:
    db_report = InvestmentReport(report_year=report_in.report_year, data=report_in.data, organization_id=organization.id, created_by_user_id=user.id)
    
    db.add(db_report)
    
    await db.commit()

    await db.refresh(db_report)
    
    return db_report