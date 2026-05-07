"""
Аналитический центр — расширенная аналитика для системы ИнвестМонитор72.
Содержит три направления:
  1. Карта дисциплины региона (ICC + box-plot по районам)
  2. Поиск похожих организаций (k-NN бенчмарк)
  3. Кластеризация районов (k-means)
"""
import math
from typing import Any
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization
from app.models.directories import District, Okved, OrgCategory
from app.models.organization_ipo import OrganizationIPO
from app.models.investment_forecast import InvestmentForecast
from app.models.report_submission import ReportSubmission


# ============================================================
#                  1. КАРТА ДИСЦИПЛИНЫ РЕГИОНА
# ============================================================

async def calculate_districts_dispersion(
    db: AsyncSession, year: int
) -> dict[str, Any]:
    """
    Возвращает данные для box-plot по районам и значение ICC
    (intraclass correlation coefficient) — сколько разброса ИПО
    объясняется именно принадлежностью к району.
    """
    # 1. Загружаем все ИПО за год вместе с районом
    query = (
        select(
            Organization.id,
            Organization.name,
            District.name.label("district_name"),
            OrganizationIPO.ipo_score,
        )
        .join(District, Organization.district_id == District.id)
        .join(OrganizationIPO, OrganizationIPO.organization_id == Organization.id)
        .where(OrganizationIPO.year == year)
    )
    result = await db.execute(query)
    rows = result.all()

    if not rows:
        return {
            "year": year, "icc": 0.0, "icc_level": "low",
            "icc_text": "Недостаточно данных",
            "icc_explanation": f"Нет данных ИПО за {year} год",
            "total_organizations": 0, "districts": [],
        }

    df = pd.DataFrame([
        {"id": r.id, "name": r.name, "district": r.district_name, "ipo": float(r.ipo_score)}
        for r in rows
    ])

    # 2. Считаем ICC
    icc = _compute_icc(df, group_col="district", value_col="ipo")

    # 3. Box-plot по районам (исключаем районы с <2 организациями — на них статистика бессмысленна)
    districts_data = []
    for district_name, group in df.groupby("district"):
        if len(group) < 2:
            continue
        ipo_values = group["ipo"].values
        q25 = float(np.percentile(ipo_values, 25))
        q75 = float(np.percentile(ipo_values, 75))
        iqr = q75 - q25
        lower_bound = q25 - 1.5 * iqr
        upper_bound = q75 + 1.5 * iqr
        outliers = [float(v) for v in ipo_values if v < lower_bound or v > upper_bound]
        non_outliers = [v for v in ipo_values if lower_bound <= v <= upper_bound]
        districts_data.append({
            "name": district_name,
            "count": len(ipo_values),
            "median_ipo": float(np.median(ipo_values)),
            "q25": q25,
            "q75": q75,
            "min": float(min(non_outliers)) if non_outliers else float(min(ipo_values)),
            "max": float(max(non_outliers)) if non_outliers else float(max(ipo_values)),
            "outliers": outliers,
        })

    # Сортировка по медиане убыванию
    districts_data.sort(key=lambda d: d["median_ipo"], reverse=True)

    # 4. Интерпретация ICC
    if icc < 0.20:
        icc_level = "low"
        icc_text = "Дисциплина зависит от организации, не от района"
        icc_explanation = (
            "Менее 20% разброса объясняется районом. "
            "Это означает, что на ИПО сильнее влияют индивидуальные "
            "особенности организаций, чем общая среда муниципалитета. "
            "Меры воздействия эффективнее точечно — по конкретным организациям."
        )
    elif icc < 0.50:
        icc_level = "moderate"
        icc_text = "Район влияет на дисциплину умеренно"
        icc_explanation = (
            "От 20% до 50% разброса объясняется районом. "
            "Принадлежность к району влияет существенно, "
            "но индивидуальные различия организаций важнее. "
            "Эффективная стратегия — комбинация районных программ "
            "и точечной работы с проблемными организациями."
        )
    else:
        icc_level = "high"
        icc_text = "Район — главный фактор дисциплины"
        icc_explanation = (
            "Более 50% разброса объясняется районом. "
            "Это означает, что муниципальное управление "
            "сильно влияет на поведение подведомственных организаций. "
            "Меры воздействия эффективнее на уровне руководства района."
        )

    return {
        "year": year,
        "icc": round(icc, 3),
        "icc_level": icc_level,
        "icc_text": icc_text,
        "icc_explanation": icc_explanation,
        "total_organizations": len(df),
        "districts": districts_data,
    }


def _compute_icc(df: pd.DataFrame, group_col: str, value_col: str) -> float:
    """
    Intraclass Correlation Coefficient ICC(1).
    Стандартная формула: ICC = MS_between / (MS_between + (k-1) * MS_within)
    где k — среднее число наблюдений в группе.
    
    Для практической интерпретации возвращаем долю variance_between / total_variance.
    """
    grand_mean = df[value_col].mean()
    grand_var = df[value_col].var()
    if grand_var == 0 or len(df) == 0:
        return 0.0

    # Дисперсия групповых средних, взвешенная по размеру групп
    group_stats = df.groupby(group_col)[value_col].agg(["mean", "count"])
    if len(group_stats) < 2:
        return 0.0

    weighted_between_var = sum(
        row["count"] * (row["mean"] - grand_mean) ** 2 for _, row in group_stats.iterrows()
    ) / len(df)

    icc = weighted_between_var / grand_var
    return max(0.0, min(1.0, icc))


# ============================================================
#                  2. ПОХОЖИЕ ОРГАНИЗАЦИИ (k-NN)
# ============================================================

async def find_peers(
    db: AsyncSession, organization_id: int, year: int, n: int = 7
) -> dict[str, Any] | None:
    """
    Находит N организаций, наиболее похожих на целевую,
    и возвращает агрегированную информацию о них.
    Имена самих похожих организаций НЕ возвращаются (анонимизация).
    """
    # 1. Загружаем все организации с ИПО за год + признаки сходства
    query = (
        select(
            Organization.id,
            Organization.name,
            Organization.is_smp,
            District.name.label("district_name"),
            Okved.code.label("okved_code"),
            OrgCategory.name.label("category_name"),
            OrganizationIPO.ipo_score,
            OrganizationIPO.d_score,
            OrganizationIPO.a_score,
            OrganizationIPO.e_score,
            InvestmentForecast.forecast_amount.label("plan"),
        )
        .join(District, Organization.district_id == District.id, isouter=True)
        .join(Okved, Organization.okved_id == Okved.id, isouter=True)
        .join(OrgCategory, Organization.category_id == OrgCategory.id, isouter=True)
        .join(OrganizationIPO, OrganizationIPO.organization_id == Organization.id)
        .join(
            InvestmentForecast,
            (InvestmentForecast.organization_id == Organization.id)
            & (InvestmentForecast.year == year)
            & (InvestmentForecast.forecast_type == "первоначальный"),
            isouter=True,
        )
        .where(OrganizationIPO.year == year)
    )
    result = await db.execute(query)
    rows = result.all()

    df = pd.DataFrame([
        {
            "id": r.id, "name": r.name, "is_smp": r.is_smp,
            "district": r.district_name or "Не определён",
            "okved": r.okved_code or "00.00",
            "category": r.category_name or "Иные",
            "ipo": float(r.ipo_score),
            "discipline": float(r.d_score),
            "quality": float(r.a_score),
            "execution": float(r.e_score) if r.e_score is not None else 0.0,
            "plan": float(r.plan) if r.plan else 0.0,
        }
        for r in rows
    ])

    if len(df) < 2:
        return None

    target_rows = df[df["id"] == organization_id]
    if target_rows.empty:
        return None
    target = target_rows.iloc[0]

    # 2. Считаем расстояние до каждой другой организации
    others = df[df["id"] != organization_id].copy()

    def distance(row):
        # Категория — самый важный признак
        cat_match = 1.0 if row["category"] == target["category"] else 0.0
        # ОКВЭД — сравниваем по первым 2 символам (вид деятельности)
        okved_match = 1.0 if row["okved"][:2] == target["okved"][:2] else 0.0
        # Район — слабый фактор сходства
        district_match = 1.0 if row["district"] == target["district"] else 0.0
        # СМП — двоичный признак
        smp_match = 1.0 if row["is_smp"] == target["is_smp"] else 0.0
        # Размер плана — нормализованная разница логарифмов
        log_target = math.log(max(target["plan"], 1))
        log_other = math.log(max(row["plan"], 1))
        plan_diff = abs(log_target - log_other) / max(log_target, log_other, 1)
        # Итоговое расстояние (меньше = похожее)
        return (
            -2.0 * cat_match
            - 1.5 * okved_match
            - 0.3 * district_match
            - 0.5 * smp_match
            + 2.0 * plan_diff
        )

    others["distance"] = others.apply(distance, axis=1)
    others = others.sort_values("distance").head(n)

    if others.empty:
        return None

    # 3. Агрегаты по похожим
    peers_ipo = others["ipo"].values
    median_ipo = float(np.median(peers_ipo))
    median_discipline = float(np.median(others["discipline"].values))
    median_quality = float(np.median(others["quality"].values))
    median_execution = float(np.median(others["execution"].values))

    # Ранг целевой среди похожих (включая её)
    all_in_group = list(peers_ipo) + [target["ipo"]]
    rank = sum(1 for v in all_in_group if v > target["ipo"]) + 1
    total = len(all_in_group)
    if rank == 1:
        rank_text = f"вы лучше всех {len(others)} похожих организаций"
    elif rank == total:
        rank_text = f"вы хуже всех {len(others)} похожих организаций"
    else:
        worse_count = total - rank
        rank_text = f"вы хуже {total - rank} из {len(others)} похожих организаций"

    # 4. Сравнение компонентов
    components = []
    gaps = {
        "Дисциплина": (target["discipline"], median_discipline),
        "Качество": (target["quality"], median_quality),
        "Исполнение": (target["execution"], median_execution),
    }
    main_gap_name = min(gaps, key=lambda k: gaps[k][0] - gaps[k][1])
    for name, (your, median) in gaps.items():
        components.append({
            "name": name,
            "your": round(your, 1),
            "median": round(median, 1),
            "gap": round(your - median, 1),
            "is_main_gap": name == main_gap_name,
        })

    return {
        "target": {
            "id": int(target["id"]),
            "name": target["name"],
            "ipo": round(float(target["ipo"]), 1),
            "discipline": round(float(target["discipline"]), 1),
            "quality": round(float(target["quality"]), 1),
            "execution": round(float(target["execution"]), 1),
            "category": target["category"],
            "okved": target["okved"],
            "district": target["district"],
            "plan": float(target["plan"]),
        },
        "peers_summary": {
            "count": len(others),
            "median_ipo": round(median_ipo, 1),
            "median_discipline": round(median_discipline, 1),
            "median_quality": round(median_quality, 1),
            "median_execution": round(median_execution, 1),
            "rank_in_peers": rank,
            "rank_text": rank_text,
        },
        "components_comparison": components,
        "peers_distribution": [round(float(v), 1) for v in peers_ipo],
        "found_count": len(others),
    }


# ============================================================
#                  3. КЛАСТЕРИЗАЦИЯ РАЙОНОВ (k-means)
# ============================================================

CLUSTER_COLORS = ["#388e3c", "#1976d2", "#f57c00", "#d32f2f"]


async def cluster_districts(
    db: AsyncSession, year: int, n_clusters: int = 4
) -> dict[str, Any]:
    """
    Выделяет в районах Тюменской области однородные группы
    на основании 4 признаков:
      1. Средний ИПО организаций района
      2. Средняя просрочка (дней) при сдаче отчётов
      3. Доля СМП в районе
      4. Медианный размер годового плана
    """
    # 1. Загрузить все нужные данные
    query_ipo = (
        select(
            District.name.label("district"),
            Organization.id.label("org_id"),
            Organization.is_smp,
            OrganizationIPO.ipo_score,
        )
        .join(Organization, Organization.district_id == District.id)
        .join(OrganizationIPO, OrganizationIPO.organization_id == Organization.id)
        .where(OrganizationIPO.year == year)
    )
    ipo_rows = (await db.execute(query_ipo)).all()

    query_late = (
        select(
            District.name.label("district"),
            ReportSubmission.days_overdue,
        )
        .join(Organization, Organization.id == ReportSubmission.organization_id)
        .join(District, District.id == Organization.district_id)
        .where(ReportSubmission.year == year)
    )
    late_rows = (await db.execute(query_late)).all()

    query_plan = (
        select(
            District.name.label("district"),
            InvestmentForecast.forecast_amount,
        )
        .join(Organization, Organization.id == InvestmentForecast.organization_id)
        .join(District, District.id == Organization.district_id)
        .where(
            (InvestmentForecast.year == year)
            & (InvestmentForecast.forecast_type == "первоначальный")
        )
    )
    plan_rows = (await db.execute(query_plan)).all()

    # 2. Собираем агрегаты по районам
    df_ipo = pd.DataFrame([
        {"district": r.district, "ipo": float(r.ipo_score), "is_smp": bool(r.is_smp)}
        for r in ipo_rows
    ])
    df_late = pd.DataFrame([
        {"district": r.district, "days_overdue": int(r.days_overdue or 0)}
        for r in late_rows
    ])
    df_plan = pd.DataFrame([
        {"district": r.district, "plan": float(r.forecast_amount or 0)}
        for r in plan_rows
    ])

    if df_ipo.empty:
        return {"year": year, "n_clusters": 0, "districts": [], "clusters": []}

    grouped = df_ipo.groupby("district").agg(
        avg_ipo=("ipo", "mean"),
        organizations_count=("ipo", "count"),
        smp_share=("is_smp", "mean"),
    ).reset_index()

    if not df_late.empty:
        late_agg = df_late.groupby("district")["days_overdue"].mean().reset_index()
        late_agg.columns = ["district", "avg_late_days"]
        grouped = grouped.merge(late_agg, on="district", how="left")
    else:
        grouped["avg_late_days"] = 0.0

    if not df_plan.empty:
        plan_agg = df_plan.groupby("district")["plan"].median().reset_index()
        plan_agg.columns = ["district", "median_plan"]
        grouped = grouped.merge(plan_agg, on="district", how="left")
    else:
        grouped["median_plan"] = 0.0

    grouped = grouped.fillna(0)

    # 3. Подготовка признаков для k-means
    features = grouped[["avg_ipo", "avg_late_days", "smp_share", "median_plan"]].copy()
    # Логарифмируем план — иначе он съест все остальные признаки
    features["median_plan"] = np.log1p(features["median_plan"])

    n_clusters_actual = min(n_clusters, len(grouped))
    if n_clusters_actual < 2:
        # Нет смысла кластеризовать
        grouped["cluster_id"] = 0
        return _format_clusters_response(grouped, year, 1)

    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)

    kmeans = KMeans(n_clusters=n_clusters_actual, random_state=42, n_init=10)
    grouped["cluster_id"] = kmeans.fit_predict(features_scaled)

    # 4. Постпроцессинг: переименовываем кластеры по их характеристикам
    return _format_clusters_response(grouped, year, n_clusters_actual)


def _format_clusters_response(
    grouped: pd.DataFrame, year: int, n_clusters: int
) -> dict[str, Any]:
    # Сортируем кластеры по средним показателям ИПО (по убыванию)
    cluster_stats = grouped.groupby("cluster_id").agg(
        avg_ipo=("avg_ipo", "mean"),
        avg_plan=("median_plan", "mean"),
        avg_late=("avg_late_days", "mean"),
        avg_smp=("smp_share", "mean"),
        count=("district", "count"),
    ).reset_index()

    cluster_stats_sorted = cluster_stats.sort_values("avg_ipo", ascending=False).reset_index(drop=True)

    # Жестко задаем уникальные названия от лучших к худшим
    cluster_profiles = [
        ("Лидеры инвестиций", "Районы с самым высоким ИПО, крупными планами и отличной дисциплиной."),
        ("Стабильная зона", "Районы с показателями ИПО выше среднего и умеренной просрочкой."),
        ("Зона риска", "Районы с ИПО ниже среднего, наблюдаются проблемы с освоением и сдачей отчётов."),
        ("Проблемные", "Районы с критически низким ИПО и систематическими нарушениями.")
    ]

    cluster_renames = {}
    for new_id, row in cluster_stats_sorted.iterrows():
        old_id = int(row["cluster_id"])
        
        # Берем название из профилей (или генерим запасное, если кластеров больше 4)
        name, desc = cluster_profiles[new_id] if new_id < len(cluster_profiles) else (f"Группа {new_id+1}", "")
        
        cluster_renames[old_id] = {
            "id": new_id + 1,
            "name": name,
            "color": CLUSTER_COLORS[new_id % len(CLUSTER_COLORS)],
            "description": desc,
            "avg_ipo": round(float(row["avg_ipo"]), 1),
            "districts_count": int(row["count"]),
        }

    grouped["cluster_id_new"] = grouped["cluster_id"].map(lambda x: cluster_renames[x]["id"])

    districts_list = []
    for _, row in grouped.iterrows():
        districts_list.append({
            "name": row["district"],
            "cluster_id": int(row["cluster_id_new"]),
            "avg_ipo": round(float(row["avg_ipo"]), 1),
            "avg_late_days": round(float(row["avg_late_days"]), 1),
            "smp_share": round(float(row["smp_share"]), 2),
            "median_plan": round(float(row["median_plan"]), 0),
            "organizations_count": int(row["organizations_count"]),
        })

    clusters_list = sorted(cluster_renames.values(), key=lambda c: c["id"])

    return {
        "year": year,
        "n_clusters": n_clusters,
        "districts": districts_list,
        "clusters": clusters_list,
    }