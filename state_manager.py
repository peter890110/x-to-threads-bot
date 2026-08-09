import json
import os

STATE_FILE = "seen_tweets.json"

def load_seen_tweets():
    """載入已經處理過的推文 ID 列表"""
    if not os.path.exists(STATE_FILE):
        return []
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def save_seen_tweets(seen_tweets):
    """儲存已經處理過的推文 ID 列表"""
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(seen_tweets, f, indent=4)

def is_tweet_processed(tweet_id, seen_tweets):
    return str(tweet_id) in seen_tweets

def mark_tweet_processed(tweet_id, seen_tweets):
    seen_tweets.append(str(tweet_id))
    # 限制紀錄數量，避免檔案過大 (例如保留最近 1000 筆)
    if len(seen_tweets) > 1000:
        seen_tweets = seen_tweets[-1000:]
    save_seen_tweets(seen_tweets)
    return seen_tweets
