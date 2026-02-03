import os
import io
import json
import requests
import logging
import urllib.parse
import google.generativeai as genai
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import Response
from PIL import Image, ImageDraw, ImageFont

# --- LINE 專用套件 ---
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage

# 引入核心邏輯
from ziwei_logic import get_chart 

# --- 設定 Log ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# --- 1. 環境變數 ---
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
BASE_URL = "https://ziweibot.onrender.com"

# 初始化 LINE Bot
if LINE_CHANNEL_ACCESS_TOKEN and LINE_CHANNEL_SECRET:
    line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
    handler = WebhookHandler(LINE_CHANNEL_SECRET)
else:
    logger.error("❌ LINE 變數未設定！請去 Render 檢查！")

# --- 2. 設定 Gemini ---
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(
        "gemini-1.5-flash", 
        system_instruction="你是一位專業、語氣溫和且帶有神秘感的紫微斗數大師。請用繁體中文回答。回答請控制在 150 字以內。"
    )
else:
    logger.error("❌ 尚未設定 GEMINI_API_KEY！")

# --- 3. 字體載入 ---
YANG_GAN = set(['甲', '丙', '戊', '庚', '壬'])
ZODIAC_MAP = {'子':'鼠', '丑':'牛', '寅':'虎', '卯':'兔', '辰':'龍', '巳':'蛇', '午':'馬', '未':'羊', '申':'猴', '酉':'雞', '戌':'狗', '亥':'豬'}
FONT_PATH = "NotoSansCJKtc-Regular.otf"

need_download = False
if not os.path.exists(FONT_PATH):
    need_download = True
elif os.path.getsize(FONT_PATH) < 1024:
    os.remove(FONT_PATH)
    need_download = True

if need_download:
    url = "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/TraditionalChinese/NotoSansCJKtc-Regular.otf"
    try:
        logger.info("⏳ 下載字體中...")
        r = requests.get(url)
        with open(FONT_PATH, "wb") as f: f.write(r.content)
        logger.info("✅ 字體下載成功！")
    except Exception as e:
        logger.error(f"❌ 字體下載失敗: {e}")

try:
    font_h1 = ImageFont.truetype(FONT_PATH, 56)
    font_palace_bold = ImageFont.truetype(FONT_PATH, 42) 
    font_palace_light = ImageFont.truetype(FONT_PATH, 42)
    font_ganzhi = ImageFont.truetype(FONT_PATH, 24)
    font_daxian = ImageFont.truetype(FONT_PATH, 34)    
    font_major = ImageFont.truetype(FONT_PATH, 42)      
    font_normal = ImageFont.truetype(FONT_PATH, 32) 
    font_mini = ImageFont.truetype(FONT_PATH, 24)
    font_info = ImageFont.truetype(FONT_PATH, 32)
    logger.info("✅ 字體載入記憶體完成！")
except:
    font_h1 = font_palace_bold = font_palace_light = font_ganzhi = font_daxian = font_major = font_normal = font_mini = font_info = ImageFont.load_default()

THEME = {
    "bg": "#1A1A2E", "grid": "#C6A87C", "sidebar_bg": "#232342", "box_bg": "#16213E",
    "text_main": "#EAEAEA", "text_dim": "#8E8E93", "major_star": "#FFD700",
    "lucky_star": "#FF6B6B", "bad_star": "#4D96FF", "flower_star": "#FF69B4",
    "hua_lu": "#4CAF50", "hua_quan": "#F44336", "hua_ke": "#2196F3",
    "hua_ji": "#9C27B0", "tag_dayun": "#FF4500",
}

# --- 4. 畫圖函數 ---
def draw_chart(data):
    width, height = 1200, 1600
    img = Image.new('RGB', (width, height), color=THEME["bg"])
    draw = ImageDraw.Draw(img)
    
    center_x, center_y = width // 4, height // 4
    center_w, center_h = width // 2, height // 2
    draw.rectangle([center_x + 20, center_y + 20, center_x + center_w - 20, center_y + center_h - 20], outline=THEME["grid"], width=1)
    draw.text((width//2, center_y + 80), "紫微斗數", fill=THEME["text_main"], font=font_h1, anchor="mm")
    
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
    pos_map = {5: (0,0), 6: (1,0), 7: (2,0), 8: (3,0), 4: (0,1), 9: (3,1), 3: (0,2), 10: (3,2), 2: (0,3), 1: (1,3), 0: (2,3), 11: (3,3)}
    palaces = data['palaces']
    SIDEBAR_W = 70 
    
    for i, p in enumerate(palaces):
        if i not in pos_map: continue
        c, r = pos_map[i]
        x, y = c * col_w, r * row_h
        draw.rectangle([x, y, x+col_w, y+row_h], outline=THEME["grid"], width=2)
        sidebar_x = x + col_w - SIDEBAR_W
        draw.rectangle([sidebar_x, y, x+col_w, y+row_h], outline=THEME["grid"], fill=THEME["sidebar_bg"], width=1)
        gan, zhi = p['ganzhi'][0], p['ganzhi'][1]
        text_center_x = sidebar_x + SIDEBAR_W // 2
        ganzhi_box_h, ganzhi_box_w = 70, 40 
        box_y2 = y + row_h - 15
        box_y1 = box_y2 - ganzhi_box_h
        draw.rectangle([text_center_x - ganzhi_box_w//2, box_y1, text_center_x + ganzhi_box_w//2, box_y2], outline=THEME["text_dim"], width=1)
        draw.text((text_center_x, box_y1 + 18), gan, fill=THEME["text_dim"], font=font_ganzhi, anchor="mm")
        draw.text((text_center_x, box_y1 + 52), zhi, fill=THEME["text_dim"], font=font_ganzhi, anchor="mm")
        base_name = p['name'].replace("宮", "") 
        total_chars = len(base_name) + 1 + (1 if p['is_body'] else 0)
        char_height = 45
        current_y = y + 20 + (row_h - ganzhi_box_h - 35 - total_chars * char_height) // 2
        for char in base_name:
            draw.text((text_center_x, current_y), char, fill=THEME["text_main"], font=font_palace_bold, anchor="mm")
            current_y += char_height
        draw.text((text_center_x, current_y), "宮", fill=THEME["text_main"], font=font_palace_light, anchor="mm")
        if p['is_body']:
            current_y += char_height
            draw.text((text_center_x, current_y), "身", fill=THEME["lucky_star"], font=font_palace_bold, anchor="mm")
        daxian_text = p['daxian']
        text_len = font_daxian.getlength(daxian_text)
        box_w = text_len + 24 
        if box_w < 90: box_w = 90
        daxian_x = x + 10 
        daxian_y = y + row_h - 50 
        draw.rectangle([daxian_x, daxian_y, daxian_x + box_w, daxian_y + 40], outline=THEME["grid"], fill=THEME["box_bg"])
        draw.text((daxian_x + box_w//2, daxian_y + 20), daxian_text, fill="white", font=font_daxian, anchor="mm")
        tag_y_pos = daxian_y - 35
        tags = p.get('tags', {}) 
        def draw_badge(label, bg_color):
            nonlocal tag_y_pos
            draw.rectangle([daxian_x, tag_y_pos, daxian_x + 60, tag_y_pos + 30], fill=bg_color)
            draw.text((daxian_x + 30, tag_y_pos + 15), label, fill="white", font=font_mini, anchor="mm")
            tag_y_pos -= 35
        if tags.get('liunian'): draw_badge("流年", THEME["hua_quan"]) 
        if tags.get('doujun'):  draw_badge("斗君", THEME["hua_ji"])    
        if tags.get('dayun'):   draw_badge("大限", THEME["tag_dayun"]) 
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
                font = font_major; color = THEME["major_star"]; col_width = 50; char_spacing = 44   
            else:
                font = font_normal; col_width = 38; char_spacing = 34
                if s_type == 'lucky': color = THEME["lucky_star"]
                elif s_type == 'bad': color = THEME["bad_star"]
                else: color = THEME["flower_star"]
            if cursor_x < x + 10: cursor_x = cursor_x_start; cursor_y_base += 160 
            if cursor_y_base > y + row_h - 100: break 
            cur_draw_y = cursor_y_base 
            for char in s_name:
                draw.text((cursor_x, cur_draw_y), char, fill=color, font=font, anchor="mm")
                cur_draw_y += char_spacing
            if s_hua:
                bg_color = hua_map_color.get(s_hua, "white")
                box_size = 44 if s_type == 'major' else 34
                hua_y = cur_draw_y + 4
                draw.rectangle([cursor_x - box_size//2, hua_y - box_size//2, cursor_x + box_size//2, hua_y + box_size//2], fill=bg_color)
                draw.text((cursor_x, hua_y), s_hua, fill="white", font=font, anchor="mm")
            cursor_x -= col_width
    return img

# --- 5. LINE Webhook 處理 ---
@app.post("/callback")
async def callback(request: Request):
    signature = request.headers.get('X-Line-Signature', '')
    body = await request.body()
    body_decoded = body.decode('utf-8')
    try:
        handler.handle(body_decoded, signature)
    except InvalidSignatureError:
        logger.error("❌ LINE 簽章驗證失敗")
        raise HTTPException(status_code=400, detail="Invalid signature")
    return "OK"

# --- 6. LINE 訊息邏輯 (🔥更新重點🔥) ---
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.strip()
    logger.info(f"📩 收到 LINE 訊息: {text}")

    # 🔥 自動判斷：是「排盤指令」還是「聊天」？ 🔥
    is_chart_request = False
    
    parts = text.split()
    start_index = 0
    
    # 1. 容錯處理：如果有使用者還是習慣打 "命盤" 開頭，我們也接受
    if len(parts) > 0 and parts[0] == "命盤":
        start_index = 1

    # 2. 判斷邏輯：如果前四個參數是數字 (年/月/日/時)，就認定是排盤
    # 參數至少要有 5 個 (年 月 日 時 性別)
    y, m, d, h, g = 0, 0, 0, 0, ""
    is_lunar_param = "false" # 預設陽曆
    
    if len(parts) - start_index >= 5:
        try:
            # 嘗試解析數字，如果這裡報錯 (ValueError)，代表不是日期，就會跳去 else 聊天
            y = int(parts[start_index])
            m = int(parts[start_index+1])
            d = int(parts[start_index+2])
            h = int(parts[start_index+3])
            g = parts[start_index+4]
            
            # 解析成功，確認是排盤請求
            is_chart_request = True
            
            # 3. 處理「陰曆/陽曆」關鍵字 (🔥新增 農/農曆/國曆/陽曆🔥)
            # 檢查第 6 個參數以後的文字
            if len(parts) > start_index + 5:
                calendar_tag = parts[start_index + 5]
                
                # 定義陰曆關鍵字
                lunar_keywords = ["陰", "陰曆", "農", "農曆"]
                
                if calendar_tag in lunar_keywords:
                    is_lunar_param = "true"
                # 預設就是陽曆 (包含 "陽", "陽曆", "國曆", 或沒填)，所以不用特別寫 else
                
        except ValueError:
            # 轉換失敗，代表不是排盤指令
            pass

    # --- 分流處理 ---
    if is_chart_request:
        # 進入排盤模式
        try:
            encoded_gender = urllib.parse.quote(g)
            chart_url = f"{BASE_URL}/test?year={y}&month={m}&day={d}&hour={h}&gender={encoded_gender}&is_lunar={is_lunar_param}"
            logger.info(f"產生命盤 URL: {chart_url}")

            line_bot_api.reply_message(
                event.reply_token,
                [
                    TextSendMessage(text=f"大師正在為您繪製 {y}年{m}月{d}日 的命盤..."),
                    ImageSendMessage(original_content_url=chart_url, preview_image_url=chart_url)
                ]
            )
        except Exception as e:
            logger.error(f"排盤失敗: {e}")
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="大師手滑了，請檢查輸入格式是否正確。"))
    
    else:
        # 進入 Gemini 聊天模式
        if GEMINI_API_KEY:
            try:
                response = model.generate_content(text)
                reply_text = response.text
            except:
                reply_text = "大師靈力不足，請稍後再試。"
        else:
            reply_text = "大師腦袋還沒裝好 (API Key Missing)"
        
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )

# --- 7. 畫圖 API ---
@app.get("/test")
def test_chart(year: int, month: int, day: int, hour: int, gender: str, is_lunar: bool = False):
    chart_data = get_chart(year, month, day, hour, gender, target_year=2025, is_lunar=is_lunar)
    img = draw_chart(chart_data)
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    return Response(content=img_byte_arr.getvalue(), media_type="image/png")
