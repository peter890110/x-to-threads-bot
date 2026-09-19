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
        response = requests.get(url, headers=headers, params=querystring, timeout=30)
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
            
        # 第一步：過濾與整理所有貼文
        tweet_dict = {}
        for item in timeline_items:
            tid = str(item.get("rest_id") or item.get("id") or item.get("tweet_id"))
            if not tid: continue
            
            # 檢查是否為回覆
            reply_to_user = item.get("in_reply_to_screen_name")
            is_reply = item.get("in_reply_to_status_id") is not None
            
            # 如果是回覆，而且回覆的對象不是自己 (username)，代表這是他在別人版面上的留言，忽略
            if is_reply and reply_to_user and reply_to_user.lower() != username.lower():
                continue
                
            reply_to_id = str(item.get("in_reply_to_status_id")) if is_reply else None
            
            tweet_dict[tid] = {
                "id": tid,
                "text": extract_best_text(item),
                "created_at": item.get("created_at"),
                "media_urls": list(set(extract_media(item))),
                "reply_to_id": reply_to_id
            }

        parsed_tweets = []
        
        # 第二步：自動縫合 Thread (串文)
        # 依照 timeline 順序掃描，找出「串文的源頭」
        for item in timeline_items:
            tid = str(item.get("rest_id") or item.get("id") or item.get("tweet_id"))
            if tid not in tweet_dict:
                continue
                
            t = tweet_dict[tid]
            
            # 什麼是源頭？這篇不是回覆，或者它回覆的那篇已經古老到不在這次抓取的列表裡了
            if not t["reply_to_id"] or t["reply_to_id"] not in tweet_dict:
                combined_text = t["text"]
                combined_media = list(t["media_urls"])
                
                # 往下尋找有沒有回覆它的子推文，把整串故事接起來
                current_id = tid
                while True:
                    child = None
                    for child_id, child_t in tweet_dict.items():
                        if child_t["reply_to_id"] == current_id:
                            child = child_t
                            break
                            
                    if child:
                        combined_text += "\n\n" + child["text"]
                        combined_media.extend(child["media_urls"])
                        current_id = child["id"]
                    else:
                        break
                        
                # 圖片去重
                final_media = []
                for m in combined_media:
                    if m not in final_media:
                        final_media.append(m)
                        
                parsed_tweets.append({
                    "id": tid, # 用源頭的 ID 代表整串
                    "text": combined_text,
                    "created_at": t["created_at"],
                    "media_urls": final_media
                })
                
                if len(parsed_tweets) >= 5:
                    break
                    
        # 第三步：為了防範 timeline 端點惡意閹割 Twitter Blue 長推文，
        # 我們針對選出來的推文，額外呼叫一次 tweet.php (單篇詳情端點) 來獲取 100% 完整的內文
        for pt in parsed_tweets:
            details_url = f"https://{api_host}/tweet.php"
            try:
                # 嘗試呼叫詳情端點
                res = requests.get(details_url, headers=headers, params={"id": pt["id"]}, timeout=30)
                if res.status_code == 200:
                    detail_data = res.json()
                    detail_text = extract_best_text(detail_data)
                    
                    # 如果詳情端點給出的文字比 timeline 給的還要長，代表 timeline 真的隱藏了內容！
                    if len(detail_text) > len(pt["text"]):
                        print(f"成功透過 tweet.php 挖出被隱藏的超長文！字數從 {len(pt['text'])} 暴增至 {len(detail_text)} 字。")
                        pt["text"] = detail_text
                        
                    # 順便把詳情裡可能隱藏的圖片也補上
                    detail_media = extract_media(detail_data)
                    for dm in detail_media:
                        if dm not in pt["media_urls"]:
                            pt["media_urls"].append(dm)
            except Exception as e:
                print(f"嘗試抓取單篇詳情 (ID: {pt['id']}) 失敗，使用原有內容: {e}")
                pass
            
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
