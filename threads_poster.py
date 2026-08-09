import os
import requests

def post_to_threads(text):
    """
    發佈文字到 Threads。
    Threads API 要求兩步發佈：先建立 Media Container，再 Publish。
    """
    user_id = os.getenv("THREADS_USER_ID")
    access_token = os.getenv("THREADS_ACCESS_TOKEN")
    
    if not user_id or not access_token:
        print("未設定 THREADS_USER_ID 或 THREADS_ACCESS_TOKEN")
        return False

    base_url = "https://graph.threads.net/v1.0"
    
    # 1. 建立 Media Container
    container_url = f"{base_url}/{user_id}/threads"
    container_payload = {
        "media_type": "TEXT",
        "text": text,
        "access_token": access_token
    }
    
    print("正在建立 Threads Media Container...")
    try:
        res = requests.post(container_url, data=container_payload)
        res.raise_for_status()
        container_id = res.json().get("id")
        
        if not container_id:
            print("建立 Container 失敗，未取得 ID")
            return False
            
        print(f"Container 建立成功，ID: {container_id}")
        
    except Exception as e:
        print(f"建立 Container 發生錯誤: {e}")
        if 'res' in locals():
            print(res.text)
        return False

    # 2. 發佈 Media Container
    publish_url = f"{base_url}/{user_id}/threads_publish"
    publish_payload = {
        "creation_id": container_id,
        "access_token": access_token
    }
    
    print("正在發佈至 Threads...")
    try:
        pub_res = requests.post(publish_url, data=publish_payload)
        pub_res.raise_for_status()
        post_id = pub_res.json().get("id")
        print(f"✅ 發佈成功！Threads Post ID: {post_id}")
        return True
    except Exception as e:
        print(f"發佈至 Threads 發生錯誤: {e}")
        if 'pub_res' in locals():
            print(pub_res.text)
        return False
