{\rtf1\ansi\ansicpg1252\cocoartf2865
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import os\
from flask import Flask\
from selenium import webdriver\
from selenium.webdriver.chrome.options import Options\
from datetime import datetime\
\
# Setup Flask app (optional if you want to expose a /run endpoint)\
app = Flask(__name__)\
\
# Environment variables (obfuscated)\
USERNAME = os.getenv("LOGIN_USER")\
PASSWORD = os.getenv("LOGIN_PASS")\
CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")\
LOG_FILE = os.getenv("LOGIN_FILE", "LOGS.txt")\
FAILED_LOGINS_FILE = os.getenv("FAILED_LOGINS_FILE", "failed_logins.txt")\
RETRY_LOG_DIR = os.getenv("RETRY_LOG_DIR", "retry_logs")\
\
def run_login():\
    options = Options()\
    options.add_argument("--headless")\
    options.add_argument("--no-sandbox")\
    options.add_argument("--disable-dev-shm-usage")\
\
    driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH, options=options)\
\
    try:\
        driver.get("https://example.com/login")\
        # Replace with actual login logic\
        # driver.find_element(...).send_keys(USERNAME)\
        # driver.find_element(...).send_keys(PASSWORD)\
        # driver.find_element(...).click()\
\
        # Simulate success\
        success = True\
\
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")\
        if success:\
            with open(LOG_FILE, "a") as log:\
                log.write(f"[\{timestamp\}] Login succeeded for account #HASHED\\n")\
        else:\
            with open(FAILED_LOGINS_FILE, "a") as fail_log:\
                fail_log.write(f"[\{timestamp\}] Login failed for account #HASHED\\n")\
\
    except Exception as e:\
        with open(FAILED_LOGINS_FILE, "a") as fail_log:\
            fail_log.write(f"[\{datetime.now()\}] Exception: \{str(e)\}\\n")\
\
    finally:\
        driver.quit()\
\
@app.route("/run", methods=["GET"])\
def trigger_run():\
    run_login()\
    return "Login orchestration triggered."\
\
if __name__ == "__main__":\
    run_login()}