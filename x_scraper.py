import requests
import os
import json

def extract_media(obj):
    urls = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "media_url_https" or k == "media_url":
                if isinstance(v, str) and (v.endswith('.jpg') or v.endswith('.png') or 'pbs.twimg.com/media/' in v):
                    urls.append(v)
            else:
                urls.extend(extract_media(v))
    elif isinstance(obj, list):
        for v in obj:
            urls.extend(extract_media(v))
    return urls

def extract_best_text(item):
    """
    從 Twitter API 的複雜 JSON 結構中，精準挖出「最完整的推文內容」。
    避免抓到被截斷的預覽，也避免誤抓到引用的其他推文。
    """
    text_candidates = []
    
    # 1. 直接層級
    if item.get("text"): text_candidates.append(item.get("text"))
    if item.get("full_text"): text_candidates.append(item.get("full_text"))
    
    # 2. Legacy 層級 (常見於 GraphQL API 的封裝)
    legacy = item.get("legacy", {})
    if legacy.get("text"): text_candidates.append(legacy.get("text"))
    if legacy.get("full_text"): text_candidates.append(legacy.get("full_text"))
    
    # 3. Note Tweet (Twitter Blue 長推文專用欄位)
    try:
        nt = item.get("note_tweet", {}).get("note_tweet_results", {}).get("result", {}).get("text")
        if nt: text_candidates.append(nt)
    except: pass
    
    try:
        nt2 = legacy.get("note_tweet", {}).get("note_tweet_results", {}).get("result", {}).get("text")
        if nt2: text_candidates.append(nt2)
    except: pass

    if not text_candidates:
        return ""
        
    # 回傳所有候選字串中最長的那一個，保證是未被截斷的完整版本
    return max(text_candidates, key=len)

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
            # 改用全新的長推文挖掘函數
            tweet_text = extract_best_text(item)
            created_at = item.get("created_at")
            
            # 使用超強的遞迴搜尋法，把整包 JSON 裡面所有圖片網址都挖出來
            media_urls = list(set(extract_media(item)))
            
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
