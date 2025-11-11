async def send_report_notification(email_to: str, status: str, details: str):
    print(f'Отправка email {email_to}: Статус {status}, Детали {details}')