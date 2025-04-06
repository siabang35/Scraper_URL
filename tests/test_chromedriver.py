import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

# ⛓️ Tambahkan root folder ke PYTHONPATH supaya bisa import app.config
sys.path.append(str(Path(__file__).resolve().parent.parent))

# 📦 Load .env dari root project folder
env_path = Path(__file__).resolve().parents[1] / ".env"
if not env_path.exists():
    raise FileNotFoundError(f"❌ .env file not found at: {env_path}")
load_dotenv(dotenv_path=env_path)

# ✅ Import config (setelah .env diload)
from app.config import SCRAPING_CONFIG

# 📁 Ambil dan validasi path ChromeDriver
driver_path = SCRAPING_CONFIG.get("chrome_driver_path")
print(f"📁 ChromeDriver path from config: {driver_path}")

driver_file = Path(driver_path)
if not driver_path or not driver_file.exists():
    raise FileNotFoundError(f"❌ ChromeDriver not found at: {driver_path}")

# ⚙️ Konfigurasi Chrome options
options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")

# 🚀 Jalankan ChromeDriver
driver = None
try:
    print("🚀 Starting ChromeDriver...")
    service = Service(executable_path=str(driver_file))
    driver = webdriver.Chrome(service=service, options=options)
    driver.get("https://www.google.com")
    print("🌐 Page Title:", driver.title)
    print("✅ ChromeDriver berhasil dijalankan.")
except WebDriverException as e:
    print("❌ WebDriverException:", e)
except Exception as e:
    print("❌ General Error:", e)
finally:
    if driver:
        driver.quit()
        print("🧹 Browser closed.")
