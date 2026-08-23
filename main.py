import os
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
from x_scraper import fetch_latest_tweets, get_mock_tweets
from threads_poster import post_to_threads
from state_manager import load_seen_tweets, is_tweet_processed, mark_tweet_processed
from translator import translate_to_zh

# 載入 .env 檔案中的環境變數
load_dotenv()

import email.utils

def is_within_last_6_hours(created_at_str):
    """
    判斷推文是否在過去 6 小時內發布。
    如果無法解析時間，保險起見預設回傳 True (放行)。
    """
    if not created_at_str:
        return True
        
    dt = None
    try:
        # 1. 嘗試解析標準 Twitter 格式 (例如: Sat Aug 09 10:00:00 +0000 2026)
        dt = datetime.strptime(created_at_str, '%a %b %d %H:%M:%S %z %Y')
    except ValueError:
        try:
            # 2. 嘗試解析標準 Internet 格式 (RFC 2822, 例如: Sun, 16 Aug 2026...)
            parsed = email.utils.parsedate_to_datetime(created_at_str)
            if parsed:
                dt = parsed
        except (ValueError, TypeError):
            pass
            
    if not dt:
        try:
            # 3. 嘗試解析 ISO 格式 (例如: 2026-08-09T10:00:00.000Z)
            clean_str = created_at_str.replace('Z', '+00:00')
            dt = datetime.fromisoformat(clean_str)
        except ValueError:
            pass

    if not dt:
        print(f"⚠️ 無法解析時間格式: {created_at_str}，預設放行。")
        return True
            
    now = datetime.now(timezone.utc)
    diff = now - dt
    
    is_valid = diff <= timedelta(hours=6)
    if not is_valid:
        print(f"貼文時間: {dt} (距離現在已經 {diff})，太舊了。")
        
    return is_valid

def is_finance_related(text):
    """
    透過關鍵字與長度，初步過濾掉網紅可能發的「生活廢文」或「早安文」，
    確保盡量都是財經、國際新聞或認真的分析。
    """
    text_lower = text.lower()
    
    # 財經、科技與國際新聞的關鍵字庫 (涵蓋中英文)
    keywords = [
        'stock', 'market', 'economy', 'inflation', 'fed', 'rate', 'earning', 
        'crypto', 'bitcoin', 'btc', 'eth', 'gdp', 'sec', 'bank', 'crisis', 
        'news', 'global', 'invest', 'trading', 'yield', 'bond', 'nasdaq', 
        'sp500', 'dow', 'wall street', 'bull', 'bear', 'portfolio', 'asset',
        'ai', 'nvidia', 'nvda', 'tsmc', 'apple', 'meta', 'google', 'microsoft',
        '股市', '經濟', '通膨', '降息', '升息', '聯準會', '財報', '加密貨幣', 
        '比特幣', '投資', '交易', '華爾街', '牛市', '熊市', '市場', '新聞'
    ]
    
    # 如果包含關鍵字，直接放行
    for kw in keywords:
        if kw in text_lower:
            return True
            
    # 如果沒有關鍵字，但文章長度很長 (超過 150 字)，通常是認真的長篇分析，也放行
    if len(text) > 150:
        return True
        
    # 如果又短又沒有關鍵字，大概率是生活廢文 (例如 "Good morning!", "I had a great coffee")
    return False

def chunk_text(tweet_text, username, max_len=500):
    """
    將長文章分段。Threads 每篇上限為 500 字元。
    第一段加上網紅前綴，並以換行符號為優先切分點。
    """
    name_map = {
        "aleabitoreddit": "serenity",
        "jukan05": "Jukan"
    }
    display_name = name_map.get(username.lower(), username)
    prefix = f"來自X上 {display_name} 發文：\n\n"
    
    chunks = []
    
    if len(prefix) + len(tweet_text) <= max_len:
        return [prefix + tweet_text]
        
    paragraphs = tweet_text.split('\n')
    current_chunk = prefix
    
    for p in paragraphs:
        separator = '\n' if current_chunk != prefix and current_chunk != "" else ""
        
        # 處理單一段落超過 max_len 的極端情況
        if len(p) > max_len:
            if current_chunk != prefix and current_chunk != "":
                chunks.append(current_chunk)
            
            # 將這個過長段落暴力切分
            remaining_p = p
            while len(remaining_p) > 0:
                is_first = (len(chunks) == 0)
                limit = max_len - len(prefix) if is_first else max_len
                
                chunk_part = remaining_p[:limit]
                if is_first:
                    chunks.append(prefix + chunk_part)
                else:
                    chunks.append(chunk_part)
                remaining_p = remaining_p[limit:]
                
            current_chunk = "" # 清空，因為上面已經 append 完了
            continue
            
        if len(current_chunk) + len(separator) + len(p) <= max_len:
            current_chunk += separator + p
        else:
            chunks.append(current_chunk)
            current_chunk = p
            
    if current_chunk and current_chunk != prefix:
        chunks.append(current_chunk)
        
    return chunks

def main():
    target_usernames_str = os.getenv("TARGET_TWITTER_USERNAME")
    if not target_usernames_str:
        print("未設定 TARGET_TWITTER_USERNAME，請檢查 .env 檔案")
        return

    # 支援使用逗號分隔多個帳號，例如 elonmusk,billgates,tim_cook
    target_usernames = [u.strip() for u in target_usernames_str.split(",") if u.strip()]
    
    seen_tweets = load_seen_tweets()
    is_mock = os.getenv("RAPIDAPI_KEY") == "your_rapidapi_key_here" or not os.getenv("RAPIDAPI_KEY")
    
    has_posted = False # 確保每次排程只發一篇
    
    for target_username in target_usernames:
        print(f"\n=========================================")
        print(f"開始檢查 @{target_username} 的最新貼文...")
        
        if is_mock:
            print("尚未設定正式 RAPIDAPI_KEY，使用測試資料...")
            tweets = get_mock_tweets()
            # 為了測試，如果是假資料，只跑一次就結束，避免每個帳號都發同一篇測試文
            if len(target_usernames) > 1 and target_username != target_usernames[0]:
                continue
        else:
            tweets = fetch_latest_tweets(target_username)
            
        if not tweets:
            print(f"沒有抓取到 @{target_username} 的推文或發生錯誤。")
            continue
            
        new_tweets_found = False
        
        # 這裡我們假設 tweets 是最新的排在最前面，所以反向迴圈 (從舊到新發佈)
        for tweet in reversed(tweets):
            tweet_id = tweet.get("id")
            tweet_text = tweet.get("text")
            media_urls = tweet.get("media_urls", [])
            created_at = tweet.get("created_at")
            
            if not tweet_id or not tweet_text:
                continue
                
            if is_tweet_processed(tweet_id, seen_tweets):
                continue
                
            if not is_within_last_6_hours(created_at):
                print(f"貼文 (ID: {tweet_id}) 太舊 (超過 6 小時)，跳過不搬運。")
                # 雖然不搬運，但還是標記為已處理，避免下次又重複檢查
                seen_tweets = mark_tweet_processed(tweet_id, seen_tweets)
                continue
                
            if not is_finance_related(tweet_text):
                print(f"貼文 (ID: {tweet_id}) 判定為非財經/國際新聞的廢文，跳過不搬運。")
                # 標記為已處理，避免下次又重複檢查
                seen_tweets = mark_tweet_processed(tweet_id, seen_tweets)
                continue
                
            new_tweets_found = True
            print(f"發現新貼文 (ID: {tweet_id})，準備翻譯並搬運至 Threads...")
            
            # 清除原推文中的 t.co 短網址 (多媒體或外部連結)
            import re
            clean_tweet_text = re.sub(r'https?://t\.co/\w+', '', tweet_text).strip()
            
            # 翻譯並清理特定符號
            translated_text = translate_to_zh(clean_tweet_text)
            
            if not translated_text:
                print(f"翻譯完全失敗 (ID: {tweet_id})，保留狀態下次重試。")
                continue
            
            # 將長文章分段
            chunks = chunk_text(translated_text, target_username)
            if not chunks:
                continue
                
            # 發佈第一段 (包含多媒體)
            import time
            first_post_id = post_to_threads(chunks[0], media_urls)
            
            if first_post_id:
                parent_id = first_post_id
                # 發佈後續留言串
                for i, chunk in enumerate(chunks[1:]):
                    print(f"正在發佈第 {i+2} 段留言 (接續貼文 ID: {parent_id})...")
                    time.sleep(3) # 稍微等待避免觸發 API 頻率限制
                    reply_id = post_to_threads(chunk, media_urls=[], reply_to_id=parent_id)
                    if reply_id:
                        parent_id = reply_id # 將下一則接在剛發佈的留言下，形成串流
                    else:
                        print("後續留言發佈失敗！")
                        break
                
                seen_tweets = mark_tweet_processed(tweet_id, seen_tweets)
                has_posted = True
                print("✅ 已成功發佈一篇完整串文，本次任務結束。")
                break # 成功發布一篇後就跳出迴圈
            else:
                print(f"發佈失敗 (ID: {tweet_id})，保留狀態下次重試。")
                
        if not new_tweets_found:
            print(f"目前沒有 @{target_username} 的新貼文需要搬運。")
            
        # 如果已經發布過一篇，就不再檢查其他網紅
        if has_posted:
            break

if __name__ == "__main__":
    main()
