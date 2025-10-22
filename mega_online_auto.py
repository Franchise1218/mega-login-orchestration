import os
from flask import Flask
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from datetime import datetime

app = Flask(__name__)

CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
LOG_FILE = os.getenv("LOGIN_FILE", "LOGS.txt")
FAILED_LOGINS_FILE = os.getenv("FAILED_LOGINS_FILE", "failed_logins.txt")
RETRY_LOG_DIR = os.getenv("RETRY_LOG_DIR", "retry_logs")

def login_account(username, password, driver):
    try:
        driver.get("https://example.com/login")
        # Replace with actual login logic:
        # driver.find_element(...).send_keys(username)
        # driver.find_element(...).send_keys(password)
        # driver.find_element(...).click()
        return True  # Simulate success
    except Exception as e:
        print(f"Exception for {username}: {e}")
        return False

def run_login_batch():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)

    failed_accounts = []

    try:
        with open(LOG_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if not line or "," not in line:
                    continue
                username, password = line.split(",", 1)
                print(f"Attempting login for {username}")
                success = login_account(username, password, driver)
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if success:
                    with open(LOG_FILE, "a") as log:
                        log.write(f"[{timestamp}] Login succeeded for {username}\n")
                else:
                    with open(FAILED_LOGINS_FILE, "a") as fail_log:
                        fail_log.write(f"[{timestamp}] Login failed for {username}\n")
                    failed_accounts.append((username, password))
    finally:
        driver.quit()

    if failed_accounts:
        retry_failed_logins(failed_accounts)

def retry_failed_logins(failed_accounts):
    print("Starting retry phase...")
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)

    try:
        for username, password in failed_accounts:
            print(f"Retrying login for {username}")
            success = login_account(username, password, driver)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            retry_log_path = os.path.join(RETRY_LOG_DIR, f"{username.replace('@', '_at_')}.txt")
            with open(retry_log_path, "a") as retry_log:
                if success:
                    retry_log.write(f"[{timestamp}] Retry succeeded for {username}\n")
                else:
                    retry_log.write(f"[{timestamp}] Retry failed for {username}\n")
    finally:
        driver.quit()

@app.route("/run", methods=["GET"])
def trigger_run():
    run_login_batch()
    return "Batch login orchestration triggered."

if __name__ == "__main__":
    run_login_batch()
