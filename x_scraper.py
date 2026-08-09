import requests
import os
import json

def fetch_latest_tweets(username):
    """
    透過 RapidAPI 抓取指定帳號的最新推文。
    針對 twitter-api45.p.rapidapi.com 最佳化。
    """
    api_key = os.getenv("RAPIDAPI_KEY")
    api_host = os.getenv("RAPIDAPI_HOST", "twitter-api45.p.rapidapi.com")
    
    if not api_key:
        print("未設定 RAPIDAPI_KEY")
        return []

    # twitter-api45 的 User Timeline 端點
    url = f"https://{api_host}/timeline.php"
    
    # twitter-api45 使用 screenname 作為參數
    querystring = {"screenname": username}

    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": api_host
    }

    try:
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
        data = response.json()
        
        parsed_tweets = []
        
        # 解析 twitter-api45 的資料結構
        # 回傳通常為一個 dict 包含 'timeline' 陣列，或是直接是一個 List
        timeline_items = []
        if isinstance(data, dict) and data.get("timeline"):
            timeline_items = data["timeline"]
        elif isinstance(data, list):
            timeline_items = data
            
        if not timeline_items:
            return []
            
        for item in timeline_items[:5]: # 只取最新的 5 篇
            # 過濾掉回覆，只抓原創推文
            if item.get("in_reply_to_status_id"):
                continue
                
            tweet_id = item.get("rest_id") or item.get("id") or item.get("tweet_id")
            tweet_text = item.get("text")
            created_at = item.get("created_at")
            
            # 解析圖片 URL
            media_urls = []
            extended_entities = item.get("extended_entities", {})
            if extended_entities and "media" in extended_entities:
                for media in extended_entities["media"]:
                    if media.get("type") == "photo" and media.get("media_url_https"):
                        media_urls.append(media["media_url_https"])
            
            # 有些 API 格式會把圖片放在 entities 裡
            elif "entities" in item and "media" in item["entities"]:
                for media in item["entities"]["media"]:
                    if media.get("type") == "photo" and media.get("media_url_https"):
                        media_urls.append(media["media_url_https"])
            
            if tweet_id and tweet_text:
                parsed_tweets.append({
                    "id": str(tweet_id),
                    "text": tweet_text,
                    "created_at": created_at,
                    "media_urls": media_urls
                })
            
        return parsed_tweets

    except Exception as e:
        print(f"抓取 X 貼文時發生錯誤: {e}")
        return []

def get_mock_tweets():
    """提供測試用假資料，讓您可以在沒有 API Key 時測試發文流程"""
    return [
        {
            "id": "1234567890",
            "text": "這是一篇測試推文。AI is the future! 🚀",
            "created_at": "2026-08-09T10:00:00.000Z"
        }
    ]
