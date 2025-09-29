import schedule
import subprocess
import time
from datetime import datetime

def run_insider_buy_sell():
    print(f"[{datetime.now()}] Running insider_buy_sell.py")
    subprocess.run(["python3", "insider_buy_sell.py"])

def run_insider_ticker():
    print(f"[{datetime.now()}] Running insider_ticker.py")
    subprocess.run(["python3", "insider_ticker.py"])

# Schedule tasks
schedule.every(7).days.at("12:00").do(run_insider_buy_sell)
schedule.every(7).days.at("12:30").do(run_insider_ticker)

print("Scheduler started... waiting for jobs.")

while True:
    schedule.run_pending()
    time.sleep(30)
