import os
import io
import json
import requests
import logging
import urllib.parse  # 用來處理中文網址
import google.generativeai as genai
from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import Response
from PIL import Image, ImageDraw, ImageFont

# 引入核心邏輯
from ziwei_logic import get_chart 

# --- 設定 Log ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# --- 1. 環境變數 ---
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "ziwei_secret_123")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# 您的 Render 網址
BASE_URL = "https://ziweibot.onrender.com"

# --- 2. 設定 Gemini (1.5-flash) ---
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(
        "gemini-1.5-flash", 
        system_instruction="你是一位專業、語氣溫和且帶有神秘感的紫微斗數大師。請用繁體中文回答。回答請控制在 150 字以內。"
    )
else:
    logger.error("❌ 尚未設定 GEMINI_API_KEY！")

# --- 3. 畫圖設定 (字體與配色) ---
YANG_GAN = set(['甲', '丙', '戊', '庚', '壬'])
ZODIAC_MAP = {'子':'鼠', '丑':'牛', '寅':'虎', '卯':'兔', '辰':'龍', '巳':'蛇', '午':'馬', '未':'羊', '申':'猴', '酉':'雞', '戌':'狗', '亥':'豬'}
FONT_PATH = "NotoSansCJKtc-Regular.otf"
FONT_BOLD_PATH = "NotoSansCJKtc-Bold.otf" 

if not os.path.exists(FONT_PATH):
    logger.info("下載標準字體中...")
    url = "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/TraditionalChinese/NotoSansCJKtc-Regular.otf"
    r = requests.get(url)
    with open(FONT_PATH, "wb") as f: f.write(r.content)
font_path_regular = FONT_PATH
font_path_bold = FONT_PATH 

THEME = {
    "bg": "#1A1A2E", "grid": "#C6A87C", "sidebar_bg": "#232342", "box_bg": "#16213E",
    "text_main": "#EAEAEA", "text_dim": "#8E8E93", "major_star": "#FFD700",
    "lucky_star": "#FF6B6B", "bad_star": "#4D96FF", "flower_star": "#FF69B4",
    "hua_lu": "#4CAF50", "hua_quan": "#F44336", "hua_ke": "#2196F3",
    "hua_ji": "#9C27B0", "tag_dayun": "#FF4500",
}

# ==========================================
# 🔥🔥🔥 這裡是您完美的 v4.6 畫圖程式碼 🔥🔥🔥
# (我已確認補回了所有標籤和美編細節)
# ==========================================
def draw_chart(data):
    width, height = 1200, 1600
    img = Image.new('RGB', (width, height), color=THEME["bg"])
    draw = ImageDraw.Draw(img)
    
    try:
        font_h1 = ImageFont.truetype(font_path_bold, 56)
        font_palace_bold = ImageFont.truetype(font_path_bold, 42)
        font_palace_light = ImageFont.truetype(font_path_regular, 42)
        font_ganzhi = ImageFont.truetype(font_path_regular, 24)
        font_daxian = ImageFont.truetype(font_path_bold, 34)    
        font_major = ImageFont.truetype(font_path_bold, 42)     
        font_normal = ImageFont.truetype(font_path_regular, 32) 
        font_mini = ImageFont.truetype(font_path_regular, 24)   
        font_small = ImageFont.truetype(font_path_regular, 20)
    except:
        font_h1 = font_palace_bold = font_palace_light = font_ganzhi = font_daxian = font_major = font_normal = font_mini = font_small = ImageFont.load_default()

    center_x, center_y = width // 4, height // 4
    center_w, center_h = width // 2, height // 2
    
    draw.rectangle([center_x + 20, center_y + 20, center_x + center_w - 20, center_y + center_h - 20], outline=THEME["grid"], width=1)
    draw.text((width//2, center_y + 80), "紫微斗數", fill=THEME["text_main"], font=font_h1, anchor="mm")
    
    font_info = ImageFont.truetype(font_path_bold, 32)
    info_start_y = center_y + 180
    gap = 60
    
    draw.text((width//2, info_start_y), data['lunar_str'], fill=THEME["text_main"], font=font_info, anchor="mm")
    draw.text((width//2, info_start_y + gap), f"五行局：{data['bureau']}", fill=THEME["major_star"], font=font_info, anchor="mm")
    draw.text((width//2, info_start_y + gap*2), data['age_info'], fill=THEME["lucky_star"], font=font_info, anchor="mm")

    yinyang = "陽" if data['year_gan'] in YANG_GAN else "陰"
    zodiac = ZODIAC_MAP.get(data['year_zhi'], "")
    gender_str = f"性別：{yinyang}{data['gender']} ({zodiac})"
    draw.text((width//2, info_start_y + gap*3), gender_str, fill=THEME["text_main"], font=font_info, anchor="mm")

    col_w = width // 4
    row_h = height // 4
    
    pos_map = {
        5: (0,0), 6: (1,0), 7: (2,0), 8: (3,0),
        4: (0,1),                     9: (3,1),
        3: (0,2),                     10: (3,2),
        2: (0,3), 1: (1,3), 0: (2,3), 11: (3,3)
    }
    
    SIDEBAR_W = 70 
    
    palaces = data['palaces']
    
    for i, p in enumerate(palaces):
        if i not in pos_map: continue
        c, r = pos_map[i]
        x = c * col_w
        y = r * row_h
        
        draw.rectangle([x, y, x+col_w, y+row_h], outline=THEME["grid"], width=2)
        
        sidebar_x = x + col_w - SIDEBAR_W
        draw.rectangle([sidebar_x, y, x+col_w, y+row_h], outline=THEME["grid"], fill=THEME["sidebar_bg"], width=1)
        
        raw_name = p['name']
        base_name = raw_name.replace("宮", "") 
        gan = p['ganzhi'][0]
        zhi = p['ganzhi'][1]
        
        text_center_x = sidebar_x + SIDEBAR_W // 2
        
        ganzhi_box_h = 70 
        ganzhi_box_w = 40 
        bottom_margin = 15
        
        box_x1 = text_center_x - ganzhi_box_w // 2
        box_x2 = text_center_x + ganzhi_box_w // 2
        box_y2 = y + row_h - bottom_margin
        box_y1 = box_y2 - ganzhi_box_h
        
        draw.rectangle([box_x1, box_y1, box_x2, box_y2], outline=THEME["text_dim"], width=1)
        draw.text((text_center_x, box_y1 + 18), gan, fill=THEME["text_dim"], font=font_ganzhi, anchor="mm")
        draw.text((text_center_x, box_y1 + 52), zhi, fill=THEME["text_dim"], font=font_ganzhi, anchor="mm")
        
        available_h = row_h - (ganzhi_box_h + bottom_margin + 20)
        total_chars = len(base_name) + 1 
        if p['is_body']: total_chars += 1
        char_height = 45
        text_block_h = total_chars * char_height
        
        start_text_y = y + 20 + (available_h - text_block_h) // 2
        current_y = start_text_y
        
        for char in base_name:
            draw.text((text_center_x, current_y), char, fill=THEME["text_main"], font=font_palace_bold, anchor="mm")
            current_y += char_height
        draw.text((text_center_x, current_y), "宮", fill=THEME["text_main"], font=font_palace_light, anchor="mm")
        current_y += char_height
        if p['is_body']:
            draw.text((text_center_x, current_y), "身", fill=THEME["lucky_star"], font=font_palace_bold, anchor="mm")

        daxian_text = p['daxian']
        text_w = font_daxian.getlength(daxian_text)
        daxian_box_w = max(90, int(text_w) + 24) 
        daxian_box_h = 40
        daxian_x = x + 10 
        daxian_y = y + row_h - 50 
        
        draw.rectangle([daxian_x, daxian_y, daxian_x + daxian_box_w, daxian_y + daxian_box_h], outline=THEME["grid"], fill=THEME["box_bg"])
        draw.text((daxian_x + daxian_box_w//2, daxian_y + daxian_box_h//2), daxian_text, fill="white", font=font_daxian, anchor="mm")

        # --- 這裡就是之前漏掉的標籤部分 ---
        tag_y_pos = daxian_y - 35
        tags = p['tags']
        def draw_badge(label, bg_color):
            nonlocal tag_y_pos
            draw.rectangle([daxian_x, tag_y_pos, daxian_x + 60, tag_y_pos + 30], fill=bg_color)
            draw.text((daxian_x + 30, tag_y_pos + 15), label, fill="white", font=font_mini, anchor="mm")
            tag_y_pos -= 35

        if tags['liunian']: draw_badge("流年", THEME["hua_quan"]) 
        if tags['doujun']:  draw_badge("斗君", THEME["hua_ji"])   
        if tags['dayun']:   draw_badge("大限", THEME["tag_dayun"]) 
        # ----------------------------------

        major_stars = [s for s in p['stars'] if s['type'] == 'major']
        minor_stars = [s for s in p['stars'] if s['type'] != 'major']
        all_stars = major_stars + minor_stars
        
        hua_map_color = {'祿': THEME['hua_lu'], '權': THEME['hua_quan'], '科': THEME['hua_ke'], '忌': THEME['hua_ji']}
        
        cursor_x_start = sidebar_x - 25
        cursor_y_start = y + 20
        cursor_x = cursor_x_start
        cursor_y_base = cursor_y_start 
        
        for star in all_stars:
            s_name = star['name']
            s_type = star['type']
            s_hua = star['hua']
            
            if s_type == 'major':
                font = font_major
                color = THEME["major_star"]
                col_width = 50       
                char_spacing = 44    
            else:
                font = font_normal
                col_width = 38
                char_spacing = 34
                if s_type == 'lucky': color = THEME["lucky_star"]
                elif s_type == 'bad': color = THEME["bad_star"]
                else: color = THEME["flower_star"]
            
            if cursor_x < x + 10:
                cursor_x = cursor_x_start 
                cursor_y_base += 160 
            
            if cursor_y_base > y + row_h - 100:
                break 

            cur_draw_y = cursor_y_base 
            
            for char in s_name:
                draw.text((cursor_x, cur_draw_y), char, fill=color, font=font, anchor="mm")
                cur_draw_y += char_spacing
            
            if s_hua:
                bg_color = hua_map_color.get(s_hua, "white")
                box_size = 38 if s_type == 'major' else 30
                hua_y = cur_draw_y + 4
                
                draw.rectangle([
                    cursor_x - box_size//2, hua_y - box_size//2, 
                    cursor_x + box_size//2, hua_y + box_size//2
                ], fill=bg_color)
                draw.text((cursor_x, hua_y), s_hua, fill="white", font=font, anchor="mm")
            
            cursor_x -= col_width
    return img
# ==========================================
# 🔥🔥🔥 完美畫圖程式碼結束 🔥🔥🔥
# ==========================================

# --- 5. IG 回覆功能 ---
def reply_text(user_id, text):
    if not PAGE_ACCESS_TOKEN: return
    url = f"https://graph.facebook.com/v21.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    requests.post(url, headers={"Content-Type": "application/json"}, json={"recipient": {"id": user_id}, "message": {"text": text}})

def reply_image(user_id, image_url):
    if not PAGE_ACCESS_TOKEN: return
    url = f"https://graph.facebook.com/v21.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    data = {
        "recipient": {"id": user_id},
        "message": {
            "attachment": {
                "type": "image",
                "payload": {"url": image_url, "is_reusable": True}
            }
        }
    }
    r = requests.post(url, headers={"Content-Type": "application/json"}, json=data)
    logger.info(f"圖片發送回應: {r.status_code} {r.text}")

# --- 6. Webhook 核心邏輯 ---
@app.get("/webhook")
async def verify_webhook(mode: str = Query(alias="hub.mode"), token: str = Query(alias="hub.verify_token"), challenge: str = Query(alias="hub.challenge")):
    if mode == "subscribe" and token == VERIFY_TOKEN: return int(challenge)
    raise HTTPException(status_code=403, detail="Token error")

@app.post("/webhook")
async def receive_message(request: Request):
    try:
        data = await request.json()
        if "entry" in data:
            for entry in data["entry"]:
                if "messaging" in entry:
                    for event in entry["messaging"]:
                        sender_id = event.get("sender", {}).get("id")
                        text = event.get("message", {}).get("text")
                        
                        if sender_id and text:
                            logger.info(f"收到訊息: {text}")
                            
                            # 🔥 判斷指令：算命盤 🔥
                            if text.startswith("命盤"):
                                try:
                                    parts = text.split()
                                    if len(parts) >= 6:
                                        y, m, d, h, g = int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4]), parts[5]
                                        
                                        is_lunar_param = "false"
                                        type_str = "國曆"
                                        if len(parts) >= 7 and (parts[6] == "陰" or parts[6] == "農"):
                                            is_lunar_param = "true"
                                            type_str = "農曆"
                                        
                                        # 🔥 關鍵修正：把中文性別轉成 URL 編碼 🔥
                                        encoded_gender = urllib.parse.quote(g)
                                        chart_url = f"{BASE_URL}/test?year={y}&month={m}&day={d}&hour={h}&gender={encoded_gender}&is_lunar={is_lunar_param}"
                                        
                                        logger.info(f"產生命盤網址: {chart_url}")
                                        reply_text(sender_id, f"大師收到！正在為您繪製 {y}年{m}月{d}日 ({type_str}) 的命盤...")
                                        reply_image(sender_id, chart_url)
                                    else:
                                        reply_text(sender_id, "格式錯誤！請依照：\n命盤 1990 1 1 12 女 (陰)")
                                except Exception as e:
                                    logger.error(f"解析錯誤: {e}")
                                    reply_text(sender_id, "資料有誤，請檢查輸入格式。")
                            
                            # 🔥 一般聊天 (Gemini) 🔥
                            else:
                                if GEMINI_API_KEY:
                                    try:
                                        response = model.generate_content(text)
                                        reply_text(sender_id, response.text)
                                    except:
                                        reply_text(sender_id, "大師靈力不足，請稍後再試。")
        return {"status": "ok"}
    except:
        return {"status": "error"}

# --- 7. 畫圖 API ---
@app.get("/test")
def test_chart(year: int, month: int, day: int, hour: int, gender: str, is_lunar: bool = False):
    chart_data = get_chart(year, month, day, hour, gender, target_year=2025, is_lunar=is_lunar)
    img = draw_chart(chart_data)
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    return Response(content=img_byte_arr.getvalue(), media_type="image/png")
