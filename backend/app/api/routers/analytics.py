from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional
from datetime import date

from app.core.database import get_db
from app.models.organization import Organization
from app.models.investment_fact import InvestmentFact
from app.models.investment_forecast import InvestmentForecast
from app.models.directories import District
from app.models.report_submission import ReportSubmission
from app.models.uploaded_file import UploadedFile
from app.services.ipo_calculator import IPOCalculator
from app.models.organization_ipo import OrganizationIPO

router = APIRouter()

# --- Вспомогательная функция (чтобы не было ошибок импорта) ---
def get_current_quarter(target_year: int) -> int:
    today = date.today()
    if target_year == today.year:
        return (today.month - 1) // 3 + 1
    elif target_year < today.year:
        return 4
    return 1


@router.get("/dashboard")
async def get_dashboard_stats(
    start_year: int = Query(default=2022),
    end_year: int = Query(default=2026),
    db: AsyncSession = Depends(get_db)
):
    # 1. Считаем ФАКТ за период (группируем по организации и году, чтобы избежать дублей)
    fact_subq = (
        select(InvestmentFact.organization_id, InvestmentFact.year, func.max(InvestmentFact.amount).label("max_amount"))
        .where(InvestmentFact.year >= start_year)
        .where(InvestmentFact.year <= end_year)
        .group_by(InvestmentFact.organization_id, InvestmentFact.year)
        .subquery()
    )
    fact_res = await db.execute(select(func.sum(fact_subq.c.max_amount)))
    fact_total = float(fact_res.scalar() or 0)

    # 2. Считаем ПЛАН за период
    plan_subq = (
        select(InvestmentForecast.organization_id, InvestmentForecast.year, func.max(InvestmentForecast.id).label("max_id"))
        .where(InvestmentForecast.year >= start_year)
        .where(InvestmentForecast.year <= end_year)
        .group_by(InvestmentForecast.organization_id, InvestmentForecast.year)
        .subquery()
    )
    plan_stmt = select(func.sum(InvestmentForecast.forecast_amount)).join(
        plan_subq, InvestmentForecast.id == plan_subq.c.max_id
    )
    plan_res = await db.execute(plan_stmt)
    plan_total = float(plan_res.scalar() or 0)

    # 3. Выполнение
    execution = round((fact_total / plan_total) * 100, 1) if plan_total > 0 else 0

    # 4. Организации с инвестициями (считаем уникальные ID за весь период)
    orgs_with_res = await db.execute(
        select(func.count(func.distinct(fact_subq.c.organization_id)))
        .where(fact_subq.c.max_amount > 0)
    )
    orgs_with_count = orgs_with_res.scalar() or 0

    total_orgs_res = await db.execute(select(func.count(Organization.id)))
    total_orgs_count = total_orgs_res.scalar() or 0

    return {
        "factTotal": fact_total,
        "planTotal": plan_total,
        "forecastTotal": plan_total,
        "executionPercent": execution,
        "budgetExecution": execution,
        "orgsWithInvestments": orgs_with_count,
        "orgsWithoutInvestments": total_orgs_count - orgs_with_count
    }


@router.get("/stats")
async def get_dashboard_stats_legacy(db: AsyncSession = Depends(get_db)):
    return await get_dashboard_stats(start_year=date.today().year, end_year=date.today().year, db=db)


@router.get("/map")
async def get_map_data(
    start_year: int = Query(default=2022),
    end_year: int = Query(default=2026),
    db: AsyncSession = Depends(get_db)
):
    fact_subq = (
        select(InvestmentFact.organization_id, InvestmentFact.year, func.max(InvestmentFact.amount).label("max_amount"))
        .where(InvestmentFact.year >= start_year)
        .where(InvestmentFact.year <= end_year)
        .group_by(InvestmentFact.organization_id, InvestmentFact.year)
        .subquery()
    )

    stmt = select(
        func.coalesce(District.name, 'Не распределено').label('district_name'),
        func.sum(fact_subq.c.max_amount).label('total')
    ).select_from(Organization)\
     .join(fact_subq, fact_subq.c.organization_id == Organization.id)\
     .outerjoin(District, Organization.district_id == District.id)\
     .group_by(District.name)

    res = await db.execute(stmt)
    return [{"name": row.district_name, "value": float(row.total or 0)} for row in res.all()]


@router.get("/trends")
async def get_analytics_trends(
    start_year: int = Query(default=2022),
    end_year: int = Query(default=2026),
    db: AsyncSession = Depends(get_db)
):
    years_res = await db.execute(select(func.distinct(InvestmentFact.year)))
    all_years = sorted([y[0] for y in years_res.all() if y[0] is not None])
    
    history = []
    forecast_data = []
    
    for y in all_years:
        f_subq = select(func.max(InvestmentFact.amount).label("max_amount")).where(InvestmentFact.year == y).group_by(InvestmentFact.organization_id).subquery()
        f_res = await db.execute(select(func.sum(f_subq.c.max_amount)))
        fact_sum = float(f_res.scalar() or 0)
        
        p_subq = select(func.max(InvestmentForecast.id).label("mid")).where(InvestmentForecast.year == y).group_by(InvestmentForecast.organization_id).subquery()
        p_res = await db.execute(select(func.sum(InvestmentForecast.forecast_amount)).join(p_subq, InvestmentForecast.id == p_subq.c.mid))
        plan_sum = float(p_res.scalar() or 0)
        
        history.append({"year": y, "amount": fact_sum, "forecast": plan_sum})
        if y >= start_year:
            forecast_data.append({"year": y, "amount": plan_sum})

    map_data = await get_map_data(start_year, end_year, db)
    rating = sorted(map_data, key=lambda x: x['value'], reverse=True)[:5]

    return {
        "history": history,
        "rating": rating,
        "forecast": forecast_data
    }


@router.get("/quarters")
async def get_quarterly_data(
    start_year: int = Query(default=2022),
    end_year: int = Query(default=2026),
    db: AsyncSession = Depends(get_db)
):
    quarters_data = []
    
    # План за период
    plan_subq = select(InvestmentForecast.organization_id, InvestmentForecast.year, func.max(InvestmentForecast.id).label("mid")).where(
        InvestmentForecast.year >= start_year, InvestmentForecast.year <= end_year
    ).group_by(InvestmentForecast.organization_id, InvestmentForecast.year).subquery()
    
    plan_res = await db.execute(select(func.sum(InvestmentForecast.forecast_amount)).join(plan_subq, InvestmentForecast.id == plan_subq.c.mid))
    plan_total = float(plan_res.scalar() or 0)
    plan_per_quarter = plan_total / 4 if plan_total > 0 else 0

    for q in [1, 2, 3, 4]:
        stmt = select(func.sum(InvestmentFact.amount)).where(
            InvestmentFact.year >= start_year,
            InvestmentFact.year <= end_year,
            InvestmentFact.quarter == q
        )
        res = await db.execute(stmt)
        fact_sum = float(res.scalar() or 0)
        
        quarters_data.append({"quarter": q, "fact": fact_sum, "plan": plan_per_quarter})
        
    return quarters_data


@router.get("/ipo")
async def get_ipo_analytics(
    year: int = Query(2024),
    category: str = Query("Все"),
    db: AsyncSession = Depends(get_db)
):
    # 1. Получаем организации и их районы
    stmt = select(Organization, District.name.label("district_name"))\
        .outerjoin(District, Organization.district_id == District.id)
    
    orgs_rows = (await db.execute(stmt)).all()
    org_ids = [row[0].id for row in orgs_rows]

    if not org_ids:
        return {"kpi": [], "funnel": [], "scatter": [], "top_orgs": [], "bottom_orgs": []}

    # 2. Собираем Факты и Планы
    fact_res = await db.execute(
        select(InvestmentFact.organization_id, func.sum(InvestmentFact.amount))
        .where(InvestmentFact.organization_id.in_(org_ids), InvestmentFact.year == year)
        .group_by(InvestmentFact.organization_id)
    )
    facts = dict(fact_res.all())

    plan_res = await db.execute(
        select(InvestmentForecast.organization_id, func.max(InvestmentForecast.forecast_amount))
        .where(InvestmentForecast.organization_id.in_(org_ids), InvestmentForecast.year == year)
        .group_by(InvestmentForecast.organization_id)
    )
    plans = dict(plan_res.all())

    # 3. Загружаем закэшированные ИПО из organization_ipo
    ipo_cache_res = await db.execute(
        select(
            OrganizationIPO.organization_id,
            OrganizationIPO.ipo_score,
            OrganizationIPO.d_score,
            OrganizationIPO.a_score,
            OrganizationIPO.e_score,
        )
        .where(OrganizationIPO.organization_id.in_(org_ids), OrganizationIPO.year == year)
    )
    ipo_cache = {row.organization_id: row for row in ipo_cache_res.all()}
    
    # 4. Собираем Сдачи отчетов
    subm_res = await db.execute(
        select(ReportSubmission.organization_id, ReportSubmission.quarter, ReportSubmission.status, ReportSubmission.days_overdue)
        .where(ReportSubmission.organization_id.in_(org_ids), ReportSubmission.year == year)
    )
    submissions = {org_id: [] for org_id in org_ids}
    for row in subm_res.all():
        submissions[row.organization_id].append({
            "quarter": row.quarter,
            "status": row.status,
            "days_overdue": row.days_overdue
        })

    # 5. Календарь сдачи отчетов (Группировка по датам)
    cal_stmt = select(
        ReportSubmission.submitted_date.label("date"),
        func.count(ReportSubmission.id).label("count")
    ).where(
        ReportSubmission.submitted_date.isnot(None)
    ).group_by("date")
        
    cal_res = await db.execute(cal_stmt)
    calendar_data = [[str(r.date), r.count] for r in cal_res.all()]

    # --- РАСЧЕТ ИПО ДЛЯ ДАШБОРДА ---
    total_plan, total_fact, total_fact_ontime = 0, 0, 0
    scatter_data, orgs_ipo = [], []
    sum_rho, sum_alpha, sum_beta, sum_ipo, valid_count = 0, 0, 0, 0, 0

    # Словари для группировок (Stack & Heatmap)
    dist_stats = {}

    for org, dist_name in orgs_rows:
        if not dist_name or dist_name == "Не распределено":
            dist_name = "⚠ Без района"
            
        if dist_name not in dist_stats:
            dist_stats[dist_name] = {
                'count': 0, 'rho': 0, 'alpha': 0, 'beta': 0, 
                'fact': 0, 'plan': 0, 'ontime_reports': 0, 'total_reports': 0,
                'statuses': {'Образцовые': 0, 'Безалаберные': 0, 'Слабые': 0, 'Проблемные': 0}
            }

        fact_val = float(facts.get(org.id, 0))
        plan_val = float(plans.get(org.id, 0))
        org_subs = submissions.get(org.id, [])
        
        cached = ipo_cache.get(org.id)
        if not cached:
            continue  # нет в кэше — пропускаем

        rho = float(cached.d_score)
        alpha = float(cached.a_score)
        beta = float(cached.e_score) if cached.e_score is not None else 0
        ipo_val = float(cached.ipo_score)

        # для воронки "Сдано вовремя"
        is_ontime = len(org_subs) > 0 and all(s['days_overdue'] == 0 for s in org_subs)

        total_plan += plan_val
        total_fact += fact_val
        if is_ontime:
            total_fact_ontime += fact_val

        # Глобальная статистика
        sum_rho += rho
        sum_alpha += alpha
        sum_beta += beta
        sum_ipo += ipo_val
        valid_count += 1

        cat_name = "ВУЗ" if "ВУЗ" in org.name else "МО" if "МАОУ" in org.name or "МБДОУ" in org.name else "Подвед"
        scatter_data.append([rho, beta, fact_val / 1000, org.name, cat_name])
        orgs_ipo.append({"name": org.name, "ipo": ipo_val})

        # Статистика по районам
        dist_stats[dist_name]['count'] += 1
        dist_stats[dist_name]['rho'] += rho
        dist_stats[dist_name]['alpha'] += alpha
        dist_stats[dist_name]['beta'] += beta
        dist_stats[dist_name]['fact'] += fact_val
        dist_stats[dist_name]['plan'] += plan_val
        dist_stats[dist_name]['total_reports'] += len(org_subs)
        dist_stats[dist_name]['ontime_reports'] += sum(1 for s in org_subs if s['days_overdue'] == 0)

        # Определение статуса (матрица 2x2)
        if rho >= 50 and beta >= 50: dist_stats[dist_name]['statuses']['Образцовые'] += 1
        elif rho < 50 and beta >= 50: dist_stats[dist_name]['statuses']['Безалаберные'] += 1
        elif rho >= 50 and beta < 50: dist_stats[dist_name]['statuses']['Слабые'] += 1
        else: dist_stats[dist_name]['statuses']['Проблемные'] += 1

    orgs_ipo.sort(key=lambda x: x["ipo"], reverse=True)
    avg_rho = round(sum_rho / valid_count, 1) if valid_count else 0
    avg_alpha = round(sum_alpha / valid_count, 1) if valid_count else 0
    avg_beta = round(sum_beta / valid_count, 1) if valid_count else 0
    avg_ipo = round(sum_ipo / valid_count, 1) if valid_count else 0

    # --- ФОРМИРОВАНИЕ ДАННЫХ ДЛЯ НОВЫХ ГРАФИКОВ ---
    
    # 1. Stacked Bar (Распределение профилей по районам)
    districts_list = [d for d in dist_stats.keys() if dist_stats[d]['count'] > 0]
    stack_series = [
        {"name": "Образцовые", "type": "bar", "stack": "total", "itemStyle": {"color": "#4CAF50"}, "data": []},
        {"name": "Безалаберные", "type": "bar", "stack": "total", "itemStyle": {"color": "#FF9800"}, "data": []},
        {"name": "Слабые в освоении", "type": "bar", "stack": "total", "itemStyle": {"color": "#FFC107"}, "data": []},
        {"name": "Проблемные", "type": "bar", "stack": "total", "itemStyle": {"color": "#F44336"}, "data": []}
    ]
    for d in districts_list:
        stack_series[0]["data"].append(dist_stats[d]['statuses']['Образцовые'])
        stack_series[1]["data"].append(dist_stats[d]['statuses']['Безалаберные'])
        stack_series[2]["data"].append(dist_stats[d]['statuses']['Слабые'])
        stack_series[3]["data"].append(dist_stats[d]['statuses']['Проблемные'])

    # 2. Heatmap (Детальная матрица)
    heatmap_data = []
    for x_idx, d in enumerate(districts_list):
        s = dist_stats[d]
        c = s['count']
        d_rho = round(s['rho'] / c, 1)
        d_alpha = round(s['alpha'] / c, 1)
        d_beta = round(s['beta'] / c, 1)
        d_ontime = round((s['ontime_reports'] / s['total_reports'] * 100), 1) if s['total_reports'] else 0
        d_plan_perc = round((s['fact'] / s['plan'] * 100), 1) if s['plan'] else 0
        
        # 'Дисциплина', 'Качество', 'Исполнение', '% вовремя', '% плана', 'Кол-во орг.'
        heatmap_data.extend([
            [x_idx, 0, d_rho], [x_idx, 1, d_alpha], [x_idx, 2, d_beta],
            [x_idx, 3, d_ontime], [x_idx, 4, d_plan_perc > 100 and 100 or d_plan_perc], [x_idx, 5, c]
        ])

    return {
        "kpi": [
            {"title": "Дисциплина (ρ)", "val": avg_rho, "avg": 71, "delta": round(avg_rho - 71, 1), "desc": "к среднему"},
            {"title": "Качество (α)", "val": avg_alpha, "avg": 84, "delta": round(avg_alpha - 84, 1), "desc": "к среднему"},
            {"title": "Исполнение (β)", "val": avg_beta, "avg": 62, "delta": round(avg_beta - 62, 1), "desc": "к среднему"}
        ],
        "funnel": [
            {"value": round(total_plan / 1000), "name": "План инвестиций"},
            {"value": round(total_fact / 1000), "name": "Освоено (Факт)"},
            {"value": round(total_fact_ontime / 1000), "name": "Сдано вовремя"}
        ],
        "scatter": scatter_data,
        "top_orgs": orgs_ipo[:5],
        "bottom_orgs": orgs_ipo[-5:][::-1],
        "radar": [avg_rho, avg_alpha, avg_beta, avg_ipo],
        "stack": {
            "categories": districts_list,
            "series": stack_series
        },
        "heatmap": {
            "xAxis": districts_list,
            "data": heatmap_data
        },
        "calendar": calendar_data,
        "line": {
            "xAxis": ['Q1 2024', 'Q2 2024', 'Q3 2024', 'Q4 2024'],
            "seriesData": [max(0, avg_ipo - 5), avg_ipo, min(100, avg_ipo + 3), avg_ipo],
            "avgData": [70, 72, 74, 75]
        }
    }