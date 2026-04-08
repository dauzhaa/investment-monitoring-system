import io
import os
import urllib.request
import matplotlib
matplotlib.use('Agg') # Рисуем в фоне, чтобы сервер не падал
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ================= АВТОЗАГРУЗКА ШРИФТОВ =================
FONT_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "fonts")
os.makedirs(FONT_PATH, exist_ok=True)

font_reg_path = os.path.join(FONT_PATH, 'Roboto-Regular.ttf')
font_bold_path = os.path.join(FONT_PATH, 'Roboto-Bold.ttf')

# Надежные прямые ссылки на Google Fonts
URL_REG = "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Regular.ttf"
URL_BOLD = "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Bold.ttf"

# Если шрифта нет или он "битый" (весит меньше 10Кб), качаем заново
if not os.path.exists(font_reg_path) or os.path.getsize(font_reg_path) < 10000:
    urllib.request.urlretrieve(URL_REG, font_reg_path)

if not os.path.exists(font_bold_path) or os.path.getsize(font_bold_path) < 10000:
    urllib.request.urlretrieve(URL_BOLD, font_bold_path)

# Регистрируем шрифт для PDF (ReportLab)
pdfmetrics.registerFont(TTFont('Roboto', font_reg_path))
pdfmetrics.registerFont(TTFont('Roboto-Bold', font_bold_path))

# Регистрируем шрифт для графиков (Matplotlib)
fm.fontManager.addfont(font_reg_path)
plt.rcParams['font.family'] = 'Roboto'
# =========================================================

def create_chart_image(years, facts, plans, title):
    """Генерация графика matplotlib в поток байтов"""
    fig, ax = plt.subplots(figsize=(7, 4))
    
    x = range(len(years))
    width = 0.35
    
    ax.bar([i - width/2 for i in x], facts, width, label='Факт', color='#1B3A5C')
    ax.bar([i + width/2 for i in x], plans, width, label='План', color='#F57C00')
    
    ax.set_ylabel('Сумма (тыс. ₽)')
    ax.set_title(title, fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels(years)
    ax.legend()
    
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150)
    plt.close(fig) # Закрываем фигуру для очистки памяти
    
    buf.seek(0)
    return buf

def generate_analytics_pdf(data: dict) -> io.BytesIO:
    """Главная функция сборки PDF-документа"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4,
        rightMargin=40, leftMargin=40,
        topMargin=40, bottomMargin=40
    )
    
    elements = []
    
    # --- Стили текста ---
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle', parent=styles['Title'], fontName='Roboto-Bold', fontSize=22, spaceAfter=30, textColor=colors.HexColor('#0F2439')
    )
    h1_style = ParagraphStyle(
        'H1Style', parent=styles['Heading1'], fontName='Roboto-Bold', fontSize=16, spaceAfter=15, textColor=colors.HexColor('#1B3A5C')
    )
    normal_style = ParagraphStyle(
        'NormalStyle', parent=styles['Normal'], fontName='Roboto', fontSize=12, spaceAfter=10, leading=16
    )

    # --- СТРАНИЦА 1: ТИТУЛЬНЫЙ ЛИСТ ---
    elements.append(Spacer(1, 150))
    elements.append(Paragraph("Департамент образования и науки Тюменской области", normal_style))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Аналитический отчёт<br/>о состоянии инвестиций в основной капитал", title_style))
    elements.append(Spacer(1, 40))
    elements.append(Paragraph(f"<b>Период:</b> {data.get('start_year')} - {data.get('end_year')} гг.", normal_style))
    elements.append(Paragraph(f"<b>Дата формирования:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}", normal_style))
    elements.append(Spacer(1, 200))
    elements.append(Paragraph("<font size='10' color='grey'><i>Сформировано автоматически системой ИнвестМонитор72</i></font>", normal_style))
    elements.append(PageBreak())

    # --- СТРАНИЦА 2: EXECUTIVE SUMMARY ---
    elements.append(Paragraph("Ключевые показатели (Executive Summary)", h1_style))
    
    fact_total = sum(d['fact'] for d in data['yearly_data'])
    plan_total = sum(d['plan'] for d in data['yearly_data'])
    percent = round((fact_total / plan_total) * 100, 1) if plan_total else 0
    
    summary_text = (
        f"За период с {data.get('start_year')} по {data.get('end_year')} год фактический объём "
        f"инвестиций составил <b>{fact_total:,.0f} тыс. ₽</b>, что составляет <b>{percent}%</b> от плана. "
        f"Инвестиции осуществляли <b>{data.get('total_orgs')}</b> организаций."
    ).replace(',', ' ')
    
    elements.append(Paragraph(summary_text, normal_style))
    elements.append(Spacer(1, 20))
    
    kpi_data = [
        ["ФАКТ (тыс. ₽)", "ПЛАН (тыс. ₽)", "% ОСВОЕНИЯ", "ОРГАНИЗАЦИЙ"],
        [f"{fact_total:,.0f}".replace(',', ' '), f"{plan_total:,.0f}".replace(',', ' '), f"{percent}%", str(data.get('total_orgs'))]
    ]
    t = Table(kpi_data, colWidths=[120, 120, 100, 120])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1B3A5C')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,-1), 'Roboto-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('TOPPADDING', (0,0), (-1,-1), 12),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
    ]))
    elements.append(t)
    elements.append(PageBreak())

    # --- СТРАНИЦА 3: ДИНАМИКА ПО ГОДАМ ---
    elements.append(Paragraph("Динамика инвестиций по годам", h1_style))
    
    years = [str(d['year']) for d in data['yearly_data']]
    facts = [d['fact'] for d in data['yearly_data']]
    plans = [d['plan'] for d in data['yearly_data']]
    
    chart_buf = create_chart_image(years, facts, plans, "Инвестиции: Факт vs План")
    elements.append(Image(chart_buf, width=450, height=250))
    elements.append(Spacer(1, 20))
    
    table_data = [["Год", "Факт", "План", "% освоения"]]
    for d in data['yearly_data']:
        p = round((d['fact'] / d['plan']) * 100, 1) if d['plan'] else 0
        table_data.append([str(d['year']), f"{d['fact']:,.0f}".replace(',', ' '), f"{d['plan']:,.0f}".replace(',', ' '), f"{p}%"])
        
    t_years = Table(table_data, colWidths=[100, 120, 120, 120])
    t_years.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#5C6BC0')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Roboto-Bold'),
        ('FONTNAME', (0,1), (-1,-1), 'Roboto'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ]))
    elements.append(t_years)

    # Сборка документа
    doc.build(elements)
    buffer.seek(0)
    return buffer