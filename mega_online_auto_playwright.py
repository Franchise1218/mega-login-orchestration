import os, time, random
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError

LOG_FILE = os.getenv("LOGIN_FILE", "LOGS.txt")
FAILED_LOGINS_FILE = "failed_logins.txt"
FINAL_FAILED_FILE = "final_failed_accounts.txt"
RESULT_LOG_FILE = "login_results.txt"

def jitter_delay():
    delay = random.uniform(2, 5)  # jitter between 2–5 seconds
    print(f"Waiting {round(delay,2)}s before next login...")
    time.sleep(delay)

def login_account(username, password, page):
    try:
        page.context.clear_cookies()
        page.goto("https://mega.nz/logout", timeout=10000)
        page.evaluate("localStorage.clear(); sessionStorage.clear();")

        page.goto("https://mega.nz/login", timeout=20000, wait_until="load")
        page.wait_for_selector("input#login-name2", timeout=8000)

        email_field = page.locator("input#login-name2")
        if not email_field.is_visible() or email_field.is_disabled():
            print(f"{username} flagged/suspended.")
            return "blocked"

        page.fill("input#login-name2", username)
        page.fill("input[placeholder='Password']", password)
        page.click(".login-button")

        page.wait_for_load_state("networkidle", timeout=15000)

        try:
            page.wait_for_url("**/fm", timeout=10000)
            return "success"
        except TimeoutError:
            return "failed"

    except Exception as e:
        print(f"Error for {username}: {e}")
        return "failed"

def run_login_batch():
    failed_accounts = []
    processed = succeeded = failed = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width":1920,"height":1080})
        page = context.new_page()

        with open(LOG_FILE, "r") as f:
            for line in f:
                if not line.strip() or "," not in line: continue
                username, password = line.strip().split(",",1)

                print(f"Attempting login for {username}")
                outcome = login_account(username, password, page)
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                with open(RESULT_LOG_FILE,"a") as result_log:
                    if outcome == "success":
                        result_log.write(f"[{timestamp}] Login succeeded for {username}\n")
                        succeeded += 1
                    elif outcome == "blocked":
                        result_log.write(f"[{timestamp}] Account blocked/suspended: {username}\n")
                        failed += 1
                    else:
                        result_log.write(f"[{timestamp}] Login failed for {username}\n")
                        with open(FAILED_LOGINS_FILE,"a") as fail_log:
                            fail_log.write(f"[{timestamp}] Login failed for {username}\n")
                        failed_accounts.append((username,password))
                        failed += 1

                processed += 1
                if processed % 25 == 0:
                    print(f"Checkpoint: {processed} processed ({succeeded} succeeded, {failed} failed)")
                jitter_delay()

        browser.close()

    print(f"Run complete: {processed} accounts, {succeeded} succeeded, {failed} failed.")
    if failed_accounts:
        retry_failed_logins(failed_accounts)

def retry_failed_logins(failed_accounts):
    print("Starting single retry pass...")
    still_failed = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width":1920,"height":1080})
        page = context.new_page()

        for username,password in failed_accounts:
            print(f"Retrying {username}")
            outcome = login_account(username,password,page)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if outcome != "success":
                still_failed.append((username,password))
            jitter_delay()

        browser.close()

    if still_failed:
        with open(FINAL_FAILED_FILE,"w") as final_log:
            for username,_ in still_failed:
                final_log.write(f"[{timestamp}] Final failure: {username}\n")
        print("\n=== FINAL FAILURE REPORT ===")
        print(f"Total accounts failed after retry: {len(still_failed)}")
        for username,_ in still_failed:
            print(f" - {username}")
        print("============================\n")
    else:
        print("\nAll accounts eventually succeeded!\n")
