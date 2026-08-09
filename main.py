import os
from dotenv import load_dotenv
from x_scraper import fetch_latest_tweets, get_mock_tweets
from threads_poster import post_to_threads
from state_manager import load_seen_tweets, is_tweet_processed, mark_tweet_processed
from translator import translate_to_zh

# 載入 .env 檔案中的環境變數
load_dotenv()

def format_for_threads(tweet_text, username):
    """
    格式化發佈到 Threads 的文字。
    Threads 上限為 500 字元。
    """
    prefix = f"來自 X (@{username}) 的最新發文：\n\n"
    max_text_len = 500 - len(prefix) - 3 # -3 for "..."
    
    if len(tweet_text) > max_text_len:
        tweet_text = tweet_text[:max_text_len] + "..."
        
    return prefix + tweet_text

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
            
            if not tweet_id or not tweet_text:
                continue
                
            if is_tweet_processed(tweet_id, seen_tweets):
                continue
                
            new_tweets_found = True
            print(f"發現新貼文 (ID: {tweet_id})，準備翻譯並搬運至 Threads...")
            
            # 翻譯並清理特定符號
            translated_text = translate_to_zh(tweet_text)
            
            threads_content = format_for_threads(translated_text, target_username)
            
            # 呼叫 Threads API (帶入圖片)
            success = post_to_threads(threads_content, media_urls)
            
            if success:
                seen_tweets = mark_tweet_processed(tweet_id, seen_tweets)
                has_posted = True
                print("✅ 已成功發佈一篇貼文，本次任務結束。")
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
