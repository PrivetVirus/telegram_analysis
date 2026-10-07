import time
from selenium import webdriver
from selenium.webdriver.common.by import By

def main():
    print("Запуск браузера Chrome...")
    # Инициализируем настройки браузера
    options = webdriver.ChromeOptions()
    import os
    # Отключаем плашку "Браузером управляет автоматизированное ПО"
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    # Сохраняем сессию (логин) в папку "chrome_profile" рядом со скриптом
    current_dir = os.path.dirname(os.path.abspath(__file__))
    profile_path = os.path.join(current_dir, "chrome_profile")
    options.add_argument(f"user-data-dir={profile_path}")
    
    driver = webdriver.Chrome(options=options)
    
    # Открываем Telegram Web A
    driver.get("https://web.telegram.org/a/")
    
    print("\n" + "="*50)
    print("1. Отсканируйте QR-код для входа в аккаунт.")
    print("2. Выберите нужный чат в списке слева.")
    print("3. ДОЖДИТЕСЬ загрузки чата.")
    print("4. После этого вернитесь в терминал и нажмите ENTER.")
    print("="*50 + "\n")
    
    input("Нажмите ENTER для старта сбора сообщений...")
    print("Начинаю скроллить и собирать сообщения. Пожалуйста, не трогайте мышь и браузер...")
    
    # Словарь для хранения сообщений. Ключ - ID сообщения, значение - текст.
    # Это нужно, так как Telegram удаляет старые сообщения из DOM (Virtual Scrolling).
    messages_data = {}
    
    no_new_messages_count = 0
    max_retries = 6  # Сколько раз пытаться скроллить без появления новых сообщений
    
    try:
        while True:
            # Ищем все элементы сообщений на экране
            # В версии Web A сообщения обычно имеют атрибут id вида 'message12345'
            message_elements = driver.find_elements(By.CSS_SELECTOR, "div[id^='message']")
            
            if not message_elements:
                # Альтернативный селектор (на всякий случай, если версия K или сменили верстку)
                message_elements = driver.find_elements(By.CSS_SELECTOR, "div.message")
                
            if not message_elements:
                print("Сообщения на экране не найдены... ждем 2 сек.")
                time.sleep(2)
                continue
                
            new_messages_found = False
            
            for el in message_elements:
                try:
                    msg_id = el.get_attribute("id") or el.get_attribute("data-message-id")
                    if not msg_id:
                        continue
                        
                    if msg_id not in messages_data:
                        new_messages_found = True
                        
                        # Собираем текст сообщения
                        # Заменяем переносы строк на пробелы, чтобы удобнее читать, но можно и оставить
                        text_content = el.text.strip().replace('\n', ' | ')
                        messages_data[msg_id] = text_content
                except Exception:
                    # Игнорируем ошибки при чтении конкретного элемента (мог исчезнуть из DOM)
                    pass
            
            if new_messages_found:
                no_new_messages_count = 0
                print(f"Собрано {len(messages_data)} уникальных сообщений...", end="\r")
            else:
                no_new_messages_count += 1
                
            if no_new_messages_count >= max_retries:
                print("\nДостигнуто начало чата (или новые сообщения перестали грузиться).")
                break
                
            # Скроллим вверх для подгрузки старых сообщений.
            # Самый надежный способ - прокрутить к самому верхнему (старому) сообщению в текущем DOM
            try:
                driver.execute_script("arguments[0].scrollIntoView();", message_elements[0])
            except Exception:
                pass
                
            # Даем Telegram время подгрузить сообщения (зависит от скорости интернета)
            time.sleep(1.2) 

    except KeyboardInterrupt:
        print("\nСбор прерван вами.")
    except Exception as e:
        print(f"\nПроизошла ошибка: {e}")
        
    print(f"\nСбор завершен! Всего собрано: {len(messages_data)} сообщений.")
    
    output_file = "selenium_chat_history.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        # Пытаемся отсортировать сообщения по ID, чтобы они шли по порядку
        def get_numeric_id(m_id):
            nums = ''.join(filter(str.isdigit, m_id))
            return int(nums) if nums else 0
            
        sorted_messages = sorted(messages_data.items(), key=lambda x: get_numeric_id(x[0]))
        
        for m_id, text in sorted_messages:
            f.write(f"[{m_id}] {text}\n")
            
    print(f"Результат сохранен в файл: {output_file}")
    
    input("Нажмите ENTER, чтобы закрыть браузер...")
    driver.quit()

if __name__ == "__main__":
    main()
