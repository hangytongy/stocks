import os
import requests
import matplotlib.pyplot as plt
import pandas as pd
from pytrends.request import TrendReq
from dotenv import load_dotenv

# === LOAD TELEGRAM CREDENTIALS ===
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# === TELEGRAM SEND PHOTO FUNCTION ===
def send_telegram_photo(photo_path, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    with open(photo_path, "rb") as photo_file:
        files = {"photo": photo_file}
        if "_" in TELEGRAM_CHAT_ID:
            ids = TELEGRAM_CHAT_ID.split("_")
            payload = {
                "chat_id": ids[0],
                "message_thread_id": ids[1],
                "caption": text,
            }
        else:
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "caption": text,
            }

        response = requests.post(url, data=payload, files=files)
        print(response.json())


# === GOOGLE TRENDS FETCH & PLOT ===
def fetch_and_plot_trends(keywords, spike_threshold=40):
    print(f"📊 Fetching Google Trends data for: {', '.join(keywords)}")

    pytrends = TrendReq(hl="en-US", tz=360)
    pytrends.build_payload(
        kw_list=keywords,
        timeframe="today 5-y",
        geo="",     # worldwide
        gprop="",   # web search
    )

    df = pytrends.interest_over_time()
    if df.empty:
        print("⚠️ No data found.")
        return None

    # === PLOT ===
    save_path = "google_trends_comparison_spikes.png"
    plt.figure(figsize=(12, 6))
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]

    for i, keyword in enumerate(keywords):
        color = colors[i % len(colors)]
        plt.plot(df.index, df[keyword], color=color, linewidth=2.2, label=keyword.title())

        # Find spike points
        spikes = df[df[keyword] >= spike_threshold]
        plt.scatter(spikes.index, spikes[keyword], color=color, s=60, edgecolors='black', zorder=5)

        # Annotate dates for each spike
        for x, y in zip(spikes.index, spikes[keyword]):
            plt.text(
                x, y + 2, x.strftime("%Y-%m-%d"),
                fontsize=8, color=color, ha="center", rotation=45
            )

    # === STYLING ===
    plt.title(f"Google Trends: {', '.join(keywords)} (Worldwide, Web Search, Past 5 Years)",
              fontsize=16, fontweight="bold", pad=15)
    plt.xlabel("Date", fontsize=12)
    plt.ylabel("Search Interest (0–100)", fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.legend(frameon=False)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"✅ Chart saved to {save_path}")
    return save_path


# === MAIN EXECUTION ===
if __name__ == "__main__":
    keywords = ["stock market crash", "bear market"]
    photo_path = fetch_and_plot_trends(keywords, spike_threshold=40)
    if photo_path:
        caption = (
            "📈 Google Trends (Worldwide, Web Search, Past 5 Years)\n"
            + "\n".join([f"• {kw.title()}" for kw in keywords])
            + "\n\n🔺 Spikes marked where interest ≥ 40"
        )
        send_telegram_photo(photo_path, caption)
