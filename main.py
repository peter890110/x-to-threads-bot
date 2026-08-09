import os
from dotenv import load_dotenv
from x_scraper import fetch_latest_tweets, get_mock_tweets
from threads_poster import post_to_threads
from state_manager import load_seen_tweets, is_tweet_processed, mark_tweet_processed

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
    target_username = os.getenv("TARGET_TWITTER_USERNAME")
    if not target_username:
        print("未設定 TARGET_TWITTER_USERNAME，請檢查 .env 檔案")
        return

    print(f"開始檢查 @{target_username} 的最新貼文...")
    
    seen_tweets = load_seen_tweets()
    
    # 若 API 金鑰尚未設定，可以使用 get_mock_tweets() 測試發佈流程
    if os.getenv("RAPIDAPI_KEY") == "your_rapidapi_key_here" or not os.getenv("RAPIDAPI_KEY"):
        print("尚未設定正式 RAPIDAPI_KEY，使用測試資料...")
        tweets = get_mock_tweets()
    else:
        tweets = fetch_latest_tweets(target_username)
        
    if not tweets:
        print("沒有抓取到推文或發生錯誤。")
        return
        
    new_tweets_found = False
    
    # 這裡我們假設 tweets 是最新的排在最前面，所以反向迴圈 (從舊到新發佈)
    for tweet in reversed(tweets):
        tweet_id = tweet.get("id")
        tweet_text = tweet.get("text")
        
        if not tweet_id or not tweet_text:
            continue
            
        if is_tweet_processed(tweet_id, seen_tweets):
            continue
            
        new_tweets_found = True
        print(f"發現新貼文 (ID: {tweet_id})，準備搬運至 Threads...")
        
        threads_content = format_for_threads(tweet_text, target_username)
        
        # 呼叫 Threads API
        success = post_to_threads(threads_content)
        
        if success:
            seen_tweets = mark_tweet_processed(tweet_id, seen_tweets)
        else:
            print(f"發佈失敗 (ID: {tweet_id})，保留狀態下次重試。")
            
    if not new_tweets_found:
        print("目前沒有新的貼文需要搬運。")

if __name__ == "__main__":
    main()
