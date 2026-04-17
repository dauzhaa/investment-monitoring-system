import io
import os
import urllib.request
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- Загрузка шрифтов Roboto ---
FONT_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "fonts")
os.makedirs(FONT_PATH, exist_ok=True)
font_reg_path = os.path.join(FONT_PATH, 'Roboto-Regular.ttf')
font_bold_path = os.path.join(FONT_PATH, 'Roboto-Bold.ttf')
URL_REG = "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Regular.ttf"
URL_BOLD = "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Bold.ttf"

if not os.path.exists(font_reg_path) or os.path.getsize(font_reg_path) < 10000:
    urllib.request.urlretrieve(URL_REG, font_reg_path)
if not os.path.exists(font_bold_path) or os.path.getsize(font_bold_path) < 10000:
    urllib.request.urlretrieve(URL_BOLD, font_bold_path)

pdfmetrics.registerFont(TTFont('Roboto', font_reg_path))
pdfmetrics.registerFont(TTFont('Roboto-Bold', font_bold_path))
fm.fontManager.addfont(font_reg_path)
plt.rcParams['font.family'] = 'Roboto'
# --------------------

def create_chart_image(years, facts, plans, title):
    fig, ax = plt.subplots(figsize=(8, 3.5))
    x = range(len(years))
    width = 0.35
    ax.bar([i - width/2 for i in x], facts, width, label='Факт', color='#1B3A5C')
    ax.bar([i + width/2 for i in x], plans, width, label='План', color='#F57C00')
    ax.set_ylabel('Сумма (тыс. ₽)')
    ax.set_title(title, fontsize=12, pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(years)
    ax.legend()
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=200)
    plt.close(fig)
    buf.seek(0)
    return buf

def generate_analytics_pdf(data: dict) -> io.BytesIO:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Title'], fontName='Roboto-Bold', fontSize=18, spaceAfter=20, textColor=colors.HexColor('#0F2439'))
    h1_style = ParagraphStyle('H1Style', parent=styles['Heading1'], fontName='Roboto-Bold', fontSize=14, spaceBefore=15, spaceAfter=10, textColor=colors.HexColor('#1B3A5C'))
    h2_style = ParagraphStyle('H2Style', parent=styles['Heading2'], fontName='Roboto-Bold', fontSize=12, spaceBefore=10, spaceAfter=5)
    normal_style = ParagraphStyle('NormalStyle', parent=styles['Normal'], fontName='Roboto', fontSize=11, spaceAfter=8, leading=14)
    insight_style = ParagraphStyle('InsightStyle', parent=styles['Normal'], fontName='Roboto', fontSize=11, spaceAfter=15, leading=16, leftIndent=15, rightIndent=15, textColor=colors.HexColor('#2E7D32'))

    # --- СТРАНИЦА 1: Обзор и Динамика ---
    elements.append(Paragraph("Департамент образования и науки Тюменской области", normal_style))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("Сводный аналитический отчёт<br/>о состоянии инвестиций в основной капитал", title_style))
    elements.append(Paragraph(f"<b>Период:</b> {data.get('start_year')} - {data.get('end_year')} гг. &nbsp;&nbsp;&nbsp; <b>Сформировано:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}", normal_style))
    elements.append(Spacer(1, 15))

    fact_total = sum(d['fact'] for d in data['yearly_data'])
    plan_total = sum(d['plan'] for d in data['yearly_data'])
    percent = round((fact_total / plan_total) * 100, 1) if plan_total else 0
    
    summary_text = (
        f"За анализируемый период фактический объём "
        f"инвестиций составил <b>{fact_total:,.0f} тыс. ₽</b>, что составляет <b>{percent}%</b> от запланированных показателей. "
        f"В инвестиционной деятельности приняли участие <b>{data.get('total_orgs')}</b> организаций Тюменской области."
    ).replace(',', ' ')
    
    elements.append(Paragraph(summary_text, normal_style))
    elements.append(Spacer(1, 10))
    
    kpi_data = [
        ["Итого Факт (тыс. ₽)", "Итого План (тыс. ₽)", "% Освоения", "Кол-во организаций"],
        [f"{fact_total:,.0f}".replace(',', ' '), f"{plan_total:,.0f}".replace(',', ' '), f"{percent}%", str(data.get('total_orgs'))]
    ]
    t_kpi = Table(kpi_data, colWidths=[130, 130, 100, 130])
    t_kpi.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1B3A5C')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,-1), 'Roboto-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 11),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#F8F9FB')),
        ('TEXTCOLOR', (0,1), (-1,1), colors.HexColor('#0F2439')),
    ]))
    elements.append(t_kpi)
    elements.append(Spacer(1, 20))

    # Текстовая аналитика (инсайты)
    if len(data['yearly_data']) >= 2:
        first_year = data['yearly_data'][0]
        last_year = data['yearly_data'][-1]
        if first_year['fact'] > 0:
            growth = ((last_year['fact'] - first_year['fact']) / first_year['fact']) * 100
            trend_word = "увеличился" if growth > 0 else "снизился"
            color_word = "положительную" if growth > 0 else "отрицательную"
            insight_text = (
                f"<b>Аналитический вывод:</b> Сравнивая {first_year['year']} и {last_year['year']} годы, "
                f"объем фактических инвестиций {trend_word} на <b>{abs(growth):.1f}%</b> "
                f"(с {first_year['fact']:,.0f} до {last_year['fact']:,.0f} тыс. ₽). "
                f"Это демонстрирует {color_word} динамику освоения бюджета в наблюдаемом периоде."
            ).replace(',', ' ')
            elements.append(Paragraph(insight_text, insight_style))

    elements.append(Paragraph("Динамика инвестиций по годам", h1_style))
    years = [str(d['year']) for d in data['yearly_data']]
    facts = [d['fact'] for d in data['yearly_data']]
    plans = [d['plan'] for d in data['yearly_data']]
    chart_buf = create_chart_image(years, facts, plans, "Сравнение фактических и плановых показателей")
    elements.append(Image(chart_buf, width=480, height=210))
    elements.append(Spacer(1, 15))
    
    elements.append(Paragraph("Детализация по годам", h2_style))
    table_data = [["Год", "Факт (тыс. ₽)", "План (тыс. ₽)", "Отклонение (тыс. ₽)", "% освоения"]]
    for d in data['yearly_data']:
        p = round((d['fact'] / d['plan']) * 100, 1) if d['plan'] else 0
        diff = d['fact'] - d['plan']
        diff_str = f"+{diff:,.0f}" if diff > 0 else f"{diff:,.0f}"
        table_data.append([
            str(d['year']), f"{d['fact']:,.0f}".replace(',', ' '), f"{d['plan']:,.0f}".replace(',', ' '), diff_str.replace(',', ' '), f"{p}%"
        ])
        
    t_years = Table(table_data, colWidths=[60, 110, 110, 120, 90])
    t_years.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#5C6BC0')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Roboto-Bold'),
        ('FONTNAME', (0,1), (-1,-1), 'Roboto'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F5F5F5')])
    ]))
    elements.append(t_years)
    
    # --- СТРАНИЦА 2: Кварталы и Районы ---
    elements.append(PageBreak())
    elements.append(Paragraph("Структурный анализ инвестиций", h1_style))
    
    elements.append(Paragraph("Рейтинг районов (Топ-5)", h2_style))
    district_text = "В таблице ниже представлены 5 районов с наибольшим объемом привлеченных инвестиций за выбранный период. Эти муниципалитеты формируют основную долю инвестиционного портфеля."
    elements.append(Paragraph(district_text, normal_style))
    elements.append(Spacer(1, 10))

    if 'top_districts' in data and data['top_districts']:
        dist_data = [["Район", "Сумма инвестиций (тыс. ₽)"]]
        for d in data['top_districts']:
            dist_data.append([d['name'], f"{d['value']:,.0f}".replace(',', ' ')])
            
        t_dist = Table(dist_data, colWidths=[250, 200])
        t_dist.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#5C6BC0')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('ALIGN', (1,0), (1,-1), 'RIGHT'),
            ('FONTNAME', (0,0), (-1,0), 'Roboto-Bold'),
            ('FONTNAME', (0,1), (-1,-1), 'Roboto'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F5F5F5')])
        ]))
        elements.append(t_dist)
    else:
         elements.append(Paragraph("Нет данных по районам для данного периода.", normal_style))

    elements.append(Spacer(1, 20))
    
    elements.append(Paragraph("Квартальное распределение (Сводные данные)", h2_style))
    elements.append(Paragraph("Анализ распределения фактических инвестиций по кварталам позволяет оценить сезонность и ритмичность освоения средств.", normal_style))
    elements.append(Spacer(1, 10))

    if 'quarters' in data and data['quarters']:
         q_data = [["Квартал", "Факт (тыс. ₽)"]]
         for q in data['quarters']:
             q_data.append([f"{q['quarter']} квартал", f"{q['fact']:,.0f}".replace(',', ' ')])
         t_q = Table(q_data, colWidths=[150, 150])
         t_q.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#5C6BC0')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Roboto-Bold'),
            ('FONTNAME', (0,1), (-1,-1), 'Roboto'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F5F5F5')])
        ]))
         elements.append(t_q)
    else:
        elements.append(Paragraph("Нет квартальных данных для данного периода.", normal_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer