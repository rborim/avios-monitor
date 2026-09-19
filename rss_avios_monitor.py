import feedparser
import requests
import json
import os
import re
from pathlib import Path

STATE_FILE = "state.json"
BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

FEEDS = [
    "https://www.melhoresdestinos.com.br/feed",
    "https://passageirodeprimeira.com/feed/",
]

RE_PROGRAMA = re.compile(r"esfera|livelo", re.IGNORECASE)
RE_DESTINO = re.compile(r"avios|iberia|british airways|qatar airways", re.IGNORECASE)
RE_BONUS = re.compile(r"b[ôo]nus|\d{2,3}\s*%", re.IGNORECASE)


def load_state():
    if Path(STATE_FILE).exists():
        return json.loads(Path(STATE_FILE).read_text())
    return {"seen": []}


def save_state(state):
    Path(STATE_FILE).write_text(json.dumps(state, indent=2, ensure_ascii=False))


def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    resp = requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        },
        timeout=15,
    )
    resp.raise_for_status()


def check_feeds():
    state = load_state()
    seen = set(state["seen"])
    new_seen = list(seen)

    for feed_url in FEEDS:
        parsed = feedparser.parse(feed_url)
        for entry in parsed.entries:
            link = entry.get("link", "")
            if not link or link in seen:
                continue

            title = entry.get("title", "")
            summary = entry.get("summary", "")
            combined = f"{title} {summary}"

            if RE_PROGRAMA.search(combined) and RE_DESTINO.search(combined) and RE_BONUS.search(combined):
                msg = f"🚨 Promoção Esfera/Livelo → Avios detectada!\n\n<b>{title}</b>\n{link}"
                send_telegram(msg)

            new_seen.append(link)

    # evita que o state.json cresça indefinidamente
    state["seen"] = new_seen[-500:]
    save_state(state)


if __name__ == "__main__":
    check_feeds()
