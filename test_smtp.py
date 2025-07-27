import smtplib

def test_connection():
    try:
        with smtplib.SMTP_SSL('smtp.yandex.ru', 465) as server:
            server.login('projektrazgromv2@yandex.ru', '324555900a')
            print("SMTP соединение успешно!")
    except Exception as e:
        print(f"Ошибка SMTP: {e}")

test_connection()