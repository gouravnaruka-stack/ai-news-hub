"""
summarize.py
Takes raw articles and produces short-but-detailed summaries using Claude,
if an API key is available. If not, falls back to the article's own
description so the pipeline still works for free.
"""

import os
import time

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = (
    "You are a concise tech news editor. Given an article title and description, "
    "write a summary that is SHORT but DETAILED: 2-3 sentences, covering what "
    "happened, who is involved, and why it matters. No fluff, no filler words, "
    "no 'in conclusion'. Do not use markdown formatting. Just plain sentences."
)

client = None
if ANTHROPIC_API_KEY:
    from anthropic import Anthropic
    client = Anthropic(api_key=ANTHROPIC_API_KEY)


def summarize_article(title, description, source):
    content = description.strip() if description else "(No description available.)"

    if not client:
        return content

    user_prompt = (
        f"Title: {title}\n"
        f"Source: {source}\n"
        f"Description: {content}\n\n"
        "Write the 2-3 sentence summary now."
    )

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=200,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text_blocks = [b.text for b in response.content if b.type == "text"]
        return " ".join(text_blocks).strip()
    except Exception as e:
        print(f"Summarization failed for '{title}': {e}")
        return content


def summarize_articles(articles):
    summarized = []
    for a in articles:
        summary = summarize_article(a["title"], a.get("description", ""), a["source"])
        summarized.append({**a, "summary": summary})
        if client:
            time.sleep(0.5)
    return summarized


if __name__ == "__main__":
    test_articles = [{
        "title": "OpenAI releases new reasoning model",
        "description": "OpenAI announced a new model focused on step-by-step reasoning tasks.",
        "source": "TechCrunch",
        "url": "https://example.com",
        "published": "",
    }]
    print(summarize_articles(test_articles))
