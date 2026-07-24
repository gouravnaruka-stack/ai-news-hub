"""
main.py
Entry point: fetch -> summarize -> build dashboard.
Run with: python src/main.py
"""

from fetch_news import get_daily_articles
from summarize import summarize_articles
from generate_dashboard import build_dashboard
from send_email import send_digest_email


def run():
    print("Fetching AI news...")
    articles = get_daily_articles()
    print(f"Found {len(articles)} articles.")

    print("Summarizing...")
    summarized = summarize_articles(articles)

    print("Building dashboard...")
    build_dashboard(summarized)

    print("Sending email digest...")
    send_digest_email(summarized)

    print("Done.")


if __name__ == "__main__":
    run()
