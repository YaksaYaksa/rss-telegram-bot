import feedparser
import requests
import time
from datetime import datetime
import re
from requests.exceptions import RequestException
import os

# Настройки Telegram
BOT_TOKEN = os.getenv('BOT_TOKEN', '8171472371:AAE6A9p-IS0ueuyfJc8b_JVkvjrEEekZmM8')  # Используем переменную окружения
CHAT_ID = os.getenv('CHAT_ID', '@generyai')

RSS_FEED_URLS = [
    'https://realt.onliner.by/feed',
    'https://realt.by/rss/',
    'https://domovita.by/rss/',
]

POSTED_FILE = 'posted_ids.txt'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def load_posted_ids():
    try:
        with open(POSTED_FILE, 'r') as f:
            return set(f.read().splitlines())
    except FileNotFoundError:
        return set()

def save_posted_id(post_id):
    with open(POSTED_FILE, 'a') as f:
        f.write(f"{post_id}\n")

def clean_html(text):
    clean_text = re.sub(r'<[^>]+>', '', text)
    clean_text = ' '.join(clean_text.split())
    return clean_text

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    try:
        response = requests.post(url, data=payload, timeout=10)
        return response.json()
    except RequestException as e:
        print(f"Ошибка при отправке в Telegram: {e}")
        return {'ok': False, 'description': str(e)}

def process_feed(feed_url, posted_ids):
    try:
        feed = feedparser.parse(feed_url, request_headers=HEADERS)
        if not feed.entries:
            print(f"Нет новых записей в {feed_url}")
            return
        for entry in feed.entries:
            post_id = entry.get('id', entry.link)
            if post_id not in posted_ids:
                title = entry.get('title', 'Без заголовка')
                link = entry.get('link', '')
                raw_description = entry.get('description', '')
                description = clean_html(raw_description)[:2000] + '...' if raw_description else ''
                message = f"<b>{title}</b>\n{description}\n<a href='{link}'>Читать далее</a>"
                if len(message) > 4096:
                    description = description[:4096 - len(title) - len(link) - 50] + '...'
                    message = f"<b>{title}</b>\n{description}\n<a href='{link}'>Читать далее</a>"
                result = send_telegram_message(message)
                if result.get('ok'):
                    print(f"Опубликовано из {feed_url}: {title}")
                    save_posted_id(post_id)
                else:
                    print(f"Ошибка при публикации из {feed_url}: {result}")
                time.sleep(2)
    except Exception as e:
        print(f"Ошибка при обработке {feed_url}: {e}")

def main():
    posted_ids = load_posted_ids()
    for feed_url in RSS_FEED_URLS:
        print(f"Обрабатываю ленту: {feed_url}")
        process_feed(feed_url, posted_ids)
        time.sleep(5)

if __name__ == "__main__":
    while True:
        try:
            print(f"Проверка всех лент: {datetime.now()}")
            main()
            time.sleep(900)  # Каждые 15 минут
        except Exception as e:
            print(f"Ошибка в основном цикле: {e}")
            time.sleep(300)