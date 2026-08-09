import os
import requests

def post_to_threads(text, media_urls=None):
    """
    發佈文字與多媒體到 Threads。
    支援純文字、單張圖片 (IMAGE)、多張圖片 (CAROUSEL)。
    """
    if media_urls is None:
        media_urls = []
        
    user_id = os.getenv("THREADS_USER_ID")
    access_token = os.getenv("THREADS_ACCESS_TOKEN")
    
    if not user_id or not access_token:
        print("未設定 THREADS_USER_ID 或 THREADS_ACCESS_TOKEN")
        return False

    # 自動處理填錯成英文帳號的防呆機制
    if not user_id.isdigit():
        print(f"偵測到非數字的 User ID: {user_id}，正在自動轉換為數字 ID...")
        me_url = "https://graph.threads.net/v1.0/me"
        me_res = requests.get(me_url, params={"access_token": access_token})
        if me_res.status_code == 200:
            user_id = me_res.json().get("id")
            print(f"成功取得數字 User ID: {user_id}")
        else:
            print(f"無法自動轉換 User ID，請確認您的 Access Token 是否正確。錯誤: {me_res.text}")
            return False

    base_url = "https://graph.threads.net/v1.0"
    
    try:
        # 1. 根據是否有圖片，決定 Container 的建立方式
        if not media_urls:
            # 純文字
            print("正在建立純文字 Container...")
            container_payload = {
                "media_type": "TEXT",
                "text": text,
                "access_token": access_token
            }
            res = requests.post(f"{base_url}/{user_id}/threads", data=container_payload)
            res.raise_for_status()
            container_id = res.json().get("id")
            
        elif len(media_urls) == 1:
            # 單張圖片
            print("正在建立單圖 Container...")
            container_payload = {
                "media_type": "IMAGE",
                "image_url": media_urls[0],
                "text": text,
                "access_token": access_token
            }
            res = requests.post(f"{base_url}/{user_id}/threads", data=container_payload)
            res.raise_for_status()
            container_id = res.json().get("id")
            
        else:
            # 多張圖片 (CAROUSEL)
            print("正在建立多圖輪播 (Carousel) Items...")
            # 最多支援 10 張圖片
            carousel_items = []
            for img_url in media_urls[:10]:
                item_payload = {
                    "media_type": "IMAGE",
                    "image_url": img_url,
                    "is_carousel_item": "true",
                    "access_token": access_token
                }
                item_res = requests.post(f"{base_url}/{user_id}/threads", data=item_payload)
                item_res.raise_for_status()
                carousel_items.append(item_res.json().get("id"))
                
            print("正在建立 Carousel 主 Container...")
            container_payload = {
                "media_type": "CAROUSEL",
                "children": ",".join(carousel_items),
                "text": text,
                "access_token": access_token
            }
            res = requests.post(f"{base_url}/{user_id}/threads", data=container_payload)
            res.raise_for_status()
            container_id = res.json().get("id")
            
        if not container_id:
            print("建立 Container 失敗，未取得 ID")
            return False
            
        print(f"Container 建立成功，ID: {container_id}")
        
    except Exception as e:
        print(f"建立 Container 發生錯誤: {e}")
        if 'res' in locals() and hasattr(res, 'text'):
            print(f"Threads API 錯誤詳細資訊: {res.text}")
        elif 'item_res' in locals() and hasattr(item_res, 'text'):
            print(f"Threads API 錯誤詳細資訊: {item_res.text}")
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
