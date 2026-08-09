import os
import google.generativeai as genai

def translate_to_zh(text):
    """
    使用 Google Gemini API 將文字翻譯為繁體中文，並濾除特殊符號。
    如果尚未設定 API 金鑰，則直接回傳原文。
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        print("未設定 GEMINI_API_KEY，略過翻譯。")
        return text
        
    try:
        genai.configure(api_key=api_key)
        
        prompt = f"""
        你是一個專業的社群媒體編輯。請將以下這段來自國外財經網紅的推文，翻譯成流暢、自然的台灣繁體中文。
        
        【嚴格規定】
        1. 絕對不要在翻譯結果中使用這些符號：*, 「, 」, $
        2. 請直接給出翻譯結果，不要加上任何解釋、問候語或註解。
        3. 如果遇到原本是美金的數字，請改用中文寫法 (例如：100萬美金)，不要保留 $ 符號。
        
        【待翻譯原文】
        {text}
        """
        
        # 嘗試使用正確的模型名稱
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            translated_text = response.text.strip()
        except Exception as e:
            print(f"Gemini API 呼叫失敗，請確認您的 API 金鑰是否有足夠權限: {e}")
            return text
        
        # 雙重防線：程式碼層面強制移除不想要的符號
        for char in ['*', '「', '」', '$']:
            translated_text = translated_text.replace(char, '')
            
        return translated_text
        
    except Exception as e:
        print(f"翻譯發生錯誤: {e}")
        return text
