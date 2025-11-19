import os
import time
import random
from datetime import datetime
from flask import Flask
from playwright.sync_api import sync_playwright, TimeoutError

app = Flask(__name__)

LOG_FILE = os.getenv("LOGIN_FILE", "LOGS.txt")
FAILED_LOGINS_FILE = os.getenv("FAILED_LOGINS_FILE", "failed_logins.txt")
FLAGGED_LOGINS_FILE = os.getenv("FLAGGED_LOGINS_FILE", "flagged_accounts.txt")
RETRY_LOG_DIR = os.getenv("RETRY_LOG_DIR", "retry_logs")
RESULT_LOG_FILE = "login_results.txt"

def login_account(username, password, page):
    try:
        # Clear cookies and session
        page.context.clear_cookies()
        page.goto("https://mega.nz/logout", timeout=10000)
        page.wait_for_timeout(1000)

        # Clear local/session storage
        page.evaluate("localStorage.clear(); sessionStorage.clear();")

        # Navigate to login page (balanced timeout)
        page.goto("https://mega.nz/login", timeout=15000)
        page.wait_for_selector("input#login-name2", timeout=8000)

        email_field = page.locator("input#login-name2")
        if not email_field.is_visible() or email_field.is_disabled():
            print(f"{username} login field unusable — possibly suspended.")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(FLAGGED_LOGINS_FILE, "a") as flagged_log:
                flagged_log.write(f"[{timestamp}] Possibly suspended: {username}\n")
            return False

        # Fill credentials
        page.fill("input#login-name2", username)
        page.fill("input[placeholder='Password']", password)
        page.click(".login-button")

        # Wait briefly for redirect
        page.wait_for_timeout(random.randint(4000, 7000))
        current_url = page.url

        return "cloud" in current_url or "fm" in current_url

    except TimeoutError as te:
        print(f"Timeout for {username}: {te}")
        return False
    except Exception as e:
        print(f"Exception for {username}: {e}")
        return False

def run_login_batch():
    start_time = time.time()
    failed_accounts = []
    processed = succeeded = failed = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        with open(LOG_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if not line or "," not in line:
                    continue
                username, password = line.split(",", 1)
                print(f"Attempting login for {username}")

                # Per-account timeout wrapper
                start = time.time()
                success = False
                try:
                    success = login_account(username, password, page)
                except Exception as e:
                    print(f"Error for {username}: {e}")
                finally:
                    if time.time() - start > 20:  # 20s cap per account
                        print(f"{username} exceeded time limit, skipping.")
                        success = False

                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                processed += 1

                with open(RESULT_LOG_FILE, "a") as result_log:
                    if success:
                        result_log.write(f"[{timestamp}] Login succeeded for {username}\n")
                        succeeded += 1
                    else:
                        result_log.write(f"[{timestamp}] Login failed for {username}\n")
                        with open(FAILED_LOGINS_FILE, "a") as fail_log:
                            fail_log.write(f"[{timestamp}] Login failed for {username}\n")
                        failed_accounts.append((username, password))
                        failed += 1

        browser.close()

    print(f"Processed {processed} accounts: {succeeded} succeeded, {failed} failed.")
    print(f"Runtime: {round(time.time() - start_time, 2)} seconds")

    if failed_accounts:
        retry_failed_logins(failed_accounts)

def retry_failed_logins(failed_accounts):
    print("Starting retry phase...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        for username, password in failed_accounts:
            print(f"Retrying login for {username}")
            success = login_account(username, password, page)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            retry_log_path = os.path.join(RETRY_LOG_DIR, f"{username.replace('@', '_at_')}.txt")
            with open(retry_log_path, "a") as retry_log:
                if success:
                    retry_log.write(f"[{timestamp}] Retry succeeded for {username}\n")
                else:
                    retry_log.write(f"[{timestamp}] Retry failed for {username}\n")

        browser.close()

@app.route("/run", methods=["GET"])
def trigger_run():
    run_login_batch()
    return "Batch login orchestration triggered."

if __name__ == "__main__":
    run_login_batch()
