import re
import os
import time
import requests
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

URL = "https://www.josalukkasonline.com/gold-rate-today/Chennai"
WAIT_SECONDS = 4  # time to let JS update the price after page load

# Secrets are injected as environment variables by GitHub Actions
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]


def fetch_gold_rate():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )

    driver = webdriver.Chrome(options=options)

    try:
        driver.get(URL)

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".carat-card"))
        )
        time.sleep(WAIT_SECONDS)

        cards = driver.find_elements(By.CSS_SELECTOR, ".carat-card")

        price_22k = None
        for card in cards:
            label_el = card.find_element(By.CSS_SELECTOR, ".karat")
            amount_el = card.find_element(By.CSS_SELECTOR, ".amount")
            if "22K" in label_el.text:
                digits = re.sub(r"[^\d]", "", amount_el.text)
                price_22k = int(digits)
                break

        if price_22k is None:
            raise ValueError("Could not find 22K gold rate on page")

        try:
            updated_el = driver.find_element(By.CSS_SELECTOR, ".update-text strong")
            site_updated = updated_el.text.strip()
        except Exception:
            site_updated = "N/A"

        return price_22k, site_updated

    finally:
        driver.quit()


def send_telegram_message(price, site_updated):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text = (
        f"22K Gold Rate (Chennai): Rs.{price} per gram\n"
        f"Site updated on: {site_updated}\n"
        f"Checked at: {now}"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}

    response = requests.post(url, data=payload, timeout=10)
    if response.status_code != 200:
        print("Telegram send failed:", response.text)
        response.raise_for_status()


if __name__ == "__main__":
    price, site_updated = fetch_gold_rate()
    send_telegram_message(price, site_updated)
    print(f"Sent to Telegram: Rs.{price} (site updated: {site_updated})")
