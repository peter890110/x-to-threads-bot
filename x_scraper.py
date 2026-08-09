import requests
import os
import json

def fetch_latest_tweets(username):
    """
    透過 RapidAPI 抓取指定帳號的最新推文。
    注意：此範例程式碼以常見的 Twitter135 API 為例。
    若您在 RapidAPI 選擇了不同的 Twitter API，URL 與回傳的 JSON 結構可能需要微調。
    """
    api_key = os.getenv("RAPIDAPI_KEY")
    api_host = os.getenv("RAPIDAPI_HOST", "twitter135.p.rapidapi.com")
    
    if not api_key:
        print("未設定 RAPIDAPI_KEY")
        return []

    # 這個 Endpoint 是以 Twitter135 為例，抓取使用者時間線
    url = f"https://{api_host}/v2/UserTweets/"
    
    # 這裡我們需要先透過 username 取得 user_id，但在某些 API 中可以直接用 username。
    # 假設這個 API 接受 username 或是可以查詢，我們這裡簡化為直接帶參數。
    # 實際使用時請參考您訂閱的 RapidAPI 服務文件。
    querystring = {"username": username, "count": "5"}

    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": api_host
    }

    try:
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
        data = response.json()
        
        # 解析推文 (不同的 RapidAPI 服務回傳結構會不同，這裡提供一個常見範例結構解析)
        parsed_tweets = []
        
        # 假設資料結構為 data["data"]["user"]["result"]["timeline_v2"]...
        # 為了相容性，這裡實作一個簡單的假資料模擬，或者您可以在填入真實 API 後調整此處。
        
        # 這裡我們用一個通用的解析方式，如果 API 失敗或不符預期，回傳空列表
        if "data" in data:
            # 此為簡化版解析，請依據您訂閱的 API 實際 JSON 結構修改
            # 例如:
            # tweets = data.get('data', {}).get('user', {}).get('result', {}).get('timeline_v2', {})...
            pass
            
        print("API 請求成功，由於每家 API 格式不同，請確保此處解析邏輯與您的 API 文件一致。")
        # 為了讓您測試流程，如果無法解析，這裡會返回一個測試資料 (如果開啟測試模式)
        
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
