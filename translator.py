import os
import requests
from deep_translator import GoogleTranslator

def translate_to_zh(text):
    """
    使用 Google Gemini REST API 將文字翻譯為繁體中文，並濾除特殊符號。
    如果失敗，則使用免金鑰的 deep-translator 作為備用。
    """
    api_key = os.getenv("GEMINI_API_KEY")
    translated_text = text
    used_gemini = False
    
    if api_key and api_key != "your_gemini_api_key_here":
        prompt = f"""
        你是一個專業的社群媒體編輯。請將以下這段來自國外財經網紅的推文，翻譯成流暢、自然的台灣繁體中文。
        
        【嚴格規定】
        1. 絕對不要在翻譯結果中使用這些符號：*, 「, 」, $
        2. 請直接給出翻譯結果，不要加上任何解釋、問候語或註解。
        3. 如果遇到原本是美金的數字，請改用中文寫法 (例如：100萬美金)，不要保留 $ 符號。
        4. 這是財經/股市相關推文，請使用正確的金融術語 (例如 Bear = 看空/熊市，Bull = 看多/牛市)。
        
        【待翻譯原文】
        {text}
        """
        
        models_to_try = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-1.0-pro']
        
        for model_name in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}]
            }
            try:
                res = requests.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    translated_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    used_gemini = True
                    print(f"✅ 成功使用 {model_name} 進行 AI 翻譯！")
                    break
                else:
                    print(f"嘗試模型 {model_name} 失敗，狀態碼: {res.status_code}, 回應: {res.text}")
            except Exception as e:
                print(f"嘗試模型 {model_name} 發生例外錯誤: {e}")
                continue

    # 如果 Gemini 完全失敗，啟動終極備用方案：Google Translate (免金鑰)
    if not used_gemini or translated_text == text:
        print("⚠️ Gemini 翻譯失敗，啟動 Google Translate 終極備用方案...")
        try:
            translated_text = GoogleTranslator(source='auto', target='zh-TW').translate(text)
        except Exception as e:
            print(f"終極備用方案也失敗: {e}")
            return text
            
    # 雙重防線：程式碼層面強制移除不想要的符號
    for char in ['*', '「', '」', '$']:
        translated_text = translated_text.replace(char, '')
        
    return translated_text
