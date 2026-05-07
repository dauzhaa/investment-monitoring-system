from datetime import date
from typing import List, Dict, Optional

class IPOCalculator:
    """
    Математическая модель расчёта Индекса Поведения Организации (ИПО).
    """
    
    # Количество проверяемых полей в одном отчете (M). 
    # У нас в ExcelRowSchema около 10 значимых колонок.
    FIELDS_PER_REPORT = 10 

    @classmethod
    def calculate(
        cls,
        is_smp: bool,
        year: int,
        current_quarter: int,
        submissions: List[Dict],  # [{'quarter': 1, 'days_overdue': 0, 'status': 'submitted'}, ...]
        errors_count: int,        # Суммарное количество ошибок валидации за год
        fact_amount: float,
        plan_amount: float
    ) -> Dict:
        # 1. Проверка на СМП: они сдают только годовой отчет
        if is_smp and current_quarter < 4:
            return {"ipo": "-", "label": "-", "details": None}

        # Определяем Qпр (количество прошедших кварталов)
        Q_pr = 1 if is_smp else current_quarter

        # ==========================================
        # ИНДЕКС ДИСЦИПЛИНЫ (Пунктуальность - ρ)
        # ==========================================
        discipline_scores = []
        for q in range(1, Q_pr + 1):
            subm = next((s for s in submissions if s['quarter'] == q), None)
            
            if subm and subm['status'] in ['submitted', 'overdue']:
                # Формула: 100 * max(0, 1 - delay/30)
                # Если просрочка 0 -> 100 баллов. Если 15 дней -> 50 баллов. Если >= 30 дней -> 0 баллов.
                delay = subm['days_overdue']
                score = 100.0 * max(0, 1.0 - (delay / 30.0))
                discipline_scores.append(score)
            elif subm and subm['status'] == 'pending':
                # Дедлайн еще не прошел, просрочки нет
                discipline_scores.append(100.0)
            else:
                # Отчет вообще не сдан, а дедлайн прошел
                discipline_scores.append(0.0)

        rho = sum(discipline_scores) / len(discipline_scores) if discipline_scores else 0.0

        # ==========================================
        # ИНДЕКС КАЧЕСТВА ДАННЫХ (Ошибки - α)
        # ==========================================
        # Формула: 100 * (1 - min(errors / (Q_pr * M), 1))
        total_fields_checked = Q_pr * cls.FIELDS_PER_REPORT
        alpha = 100.0 * (1.0 - min(errors_count / total_fields_checked, 1.0))

        # ==========================================
        # ИНДЕКС РЕЗУЛЬТАТИВНОСТИ (Исполнение - β)
        # Рассчитывается только в конце года (Q_pr == 4)
        # ==========================================
        beta = None
        if current_quarter == 4:
            if plan_amount > 0:
                beta = 100.0 * min(fact_amount / plan_amount, 1.0)
            elif fact_amount > 0:
                beta = 100.0  # Плана не было, но инвестиции есть — молодцы
            else:
                beta = 0.0    # Плана нет, факта нет

        # ==========================================
        # ИТОГОВЫЙ ИПО (Композитный)
        # ==========================================
        if current_quarter < 4:
            # Квартальный ИПО
            ipo_value = (0.7 * rho) + (0.3 * alpha)
        else:
            # Годовой ИПО
            ipo_value = (0.5 * rho) + (0.2 * alpha) + (0.3 * beta)

        ipo_value = round(ipo_value, 2)

        # Шкала интерпретации
        if ipo_value >= 90: label = "Образцовая"
        elif ipo_value >= 70: label = "Надёжная"
        elif ipo_value >= 50: label = "Требует внимания"
        elif ipo_value >= 30: label = "Проблемная"
        else: label = "Критическая"

        return {
            "ipo": ipo_value,
            "label": label,
            "details": {
                "discipline": round(rho, 2),
                "quality": round(alpha, 2),
                "execution": round(beta, 2) if beta is not None else None
            }
        }