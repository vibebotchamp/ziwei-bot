import io
import os
import requests
from fastapi import FastAPI
from fastapi.responses import Response
from PIL import Image, ImageDraw, ImageFont

# 引入核心邏輯
from ziwei_logic import get_chart 

app = FastAPI()

# --- 基礎資料表 ---
YANG_GAN = set(['甲', '丙', '戊', '庚', '壬'])
ZODIAC_MAP = {
    '子':'鼠', '丑':'牛', '寅':'虎', '卯':'兔', '辰':'龍', '巳':'蛇',
    '午':'馬', '未':'羊', '申':'猴', '酉':'雞', '戌':'狗', '亥':'豬'
}

# --- 1. 字體設定 ---
FONT_PATH = "NotoSansCJKtc-Regular.otf"
FONT_BOLD_PATH = "NotoSansCJKtc-Bold.otf" 

if not os.path.exists(FONT_PATH):
    print("下載標準字體中...")
    url = "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/TraditionalChinese/NotoSansCJKtc-Regular.otf"
    r = requests.get(url)
    with open(FONT_PATH, "wb") as f:
        f.write(r.content)

font_path_regular = FONT_PATH
font_path_bold = FONT_PATH 

# --- 2. 配色主題 ---
THEME = {
    "bg": "#1A1A2E",          # 深藍底
    "grid": "#C6A87C",        # 金色格線
    "sidebar_bg": "#232342",  # 右側欄位底色
    "box_bg": "#16213E",      # 小框框底色
    "text_main": "#EAEAEA",   # 主文字白
    "text_dim": "#8E8E93",    
    "major_star": "#FFD700",  # 主星金
    "lucky_star": "#FF6B6B",  # 吉星紅
    "bad_star": "#4D96FF",    # 煞星藍
    "flower_star": "#FF69B4", # 桃花粉
    "hua_lu": "#4CAF50",      
    "hua_quan": "#F44336",    
    "hua_ke": "#2196F3",      
    "hua_ji": "#9C27B0",      
    "tag_dayun": "#FF4500",   
}

def draw_chart(data):
    # 設定畫布大小
    width, height = 1200, 1600
    img = Image.new('RGB', (width, height), color=THEME["bg"])
    draw = ImageDraw.Draw(img)
    
    try:
        font_h1 = ImageFont.truetype(font_path_bold, 56)
        font_palace_bold = ImageFont.truetype(font_path_bold, 42)
        font_palace_light = ImageFont.truetype(font_path_regular, 42)
        
        # --- 字體設定 ---
        font_ganzhi = ImageFont.truetype(font_path_regular, 24) # 天干地支
        font_daxian = ImageFont.truetype(font_path_bold, 34)    
        font_major = ImageFont.truetype(font_path_bold, 42)     
        font_normal = ImageFont.truetype(font_path_regular, 32) 
        font_mini = ImageFont.truetype(font_path_regular, 24)   
        
        font_small = ImageFont.truetype(font_path_regular, 20)
    except:
        font_h1 = font_palace_bold = font_palace_light = font_ganzhi = font_daxian = font_major = font_normal = font_mini = font_small = ImageFont.load_default()

    # --- A. 繪製中宮 ---
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

    # --- B. 繪製 12 宮位 ---
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
        
        # 1. 畫格子主框線
        draw.rectangle([x, y, x+col_w, y+row_h], outline=THEME["grid"], width=2)
        
        # 2. 畫右側側邊欄
        sidebar_x = x + col_w - SIDEBAR_W
        draw.rectangle([sidebar_x, y, x+col_w, y+row_h], outline=THEME["grid"], fill=THEME["sidebar_bg"], width=1)
        
        # --- C. 側邊欄排版 ---
        raw_name = p['name']
        base_name = raw_name.replace("宮", "") 
        gan = p['ganzhi'][0]
        zhi = p['ganzhi'][1]
        
        text_center_x = sidebar_x + SIDEBAR_W // 2
        
        # 1. 繪製天干地支 (沉底)
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
        
        # 2. 繪製宮位名稱
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

        # --- D. 底部大限框 ---
        daxian_text = p['daxian']
        text_w = font_daxian.getlength(daxian_text)
        daxian_box_w = max(90, int(text_w) + 24) 
        daxian_box_h = 40
        daxian_x = x + 10 
        daxian_y = y + row_h - 50 
        
        draw.rectangle([daxian_x, daxian_y, daxian_x + daxian_box_w, daxian_y + daxian_box_h], outline=THEME["grid"], fill=THEME["box_bg"])
        draw.text((daxian_x + daxian_box_w//2, daxian_y + daxian_box_h//2), daxian_text, fill="white", font=font_daxian, anchor="mm")

        # 標籤
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

        # --- 🔥 E. 星曜直排 (自動換行/防爆版) 🔥 ---
        major_stars = [s for s in p['stars'] if s['type'] == 'major']
        minor_stars = [s for s in p['stars'] if s['type'] != 'major']
        
        all_stars = major_stars + minor_stars
        
        hua_map_color = {'祿': THEME['hua_lu'], '權': THEME['hua_quan'], '科': THEME['hua_ke'], '忌': THEME['hua_ji']}
        
        # 起始座標
        cursor_x_start = sidebar_x - 25
        cursor_y_start = y + 20
        
        cursor_x = cursor_x_start
        cursor_y_base = cursor_y_start # 這一行的基準Y
        
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
            
            # --- 🔥 換行邏輯判斷 🔥 ---
            # 如果 X 座標太左邊 (快撞到左邊界了)
            if cursor_x < x + 10:
                # 換行：重置 X 回右邊，Y 往下移動一行
                cursor_x = cursor_x_start 
                
                # 計算下一行的高度：預估一行大概佔 160px (含字+四化+間距)
                # 確保新的一行不會蓋到上一行的尾巴
                cursor_y_base += 160 
            
            # --- 🔥 底部安全檢查 🔥 ---
            # 如果 Y 座標太低 (快撞到大限框了)，就停止繪製
            # 預留 100px 給底部的大限框與標籤
            if cursor_y_base > y + row_h - 100:
                break 

            # 開始畫字
            cur_draw_y = cursor_y_base 
            
            # 1. 畫星名
            for char in s_name:
                draw.text((cursor_x, cur_draw_y), char, fill=color, font=font, anchor="mm")
                cur_draw_y += char_spacing
            
            # 2. 畫四化
            if s_hua:
                bg_color = hua_map_color.get(s_hua, "white")
                box_size = 38 if s_type == 'major' else 30
                hua_y = cur_draw_y + 4
                
                draw.rectangle([
                    cursor_x - box_size//2, hua_y - box_size//2, 
                    cursor_x + box_size//2, hua_y + box_size//2
                ], fill=bg_color)
                
                draw.text((cursor_x, hua_y), s_hua, fill="white", font=font, anchor="mm")
            
            # 畫完一顆星，X 往左移
            cursor_x -= col_width

    return img

@app.get("/test")
def test_chart(year: int = 1990, month: int = 1, day: int = 1, hour: int = 12, gender: str = "女", is_lunar: bool = False):
    chart_data = get_chart(year, month, day, hour, gender, target_year=2025, is_lunar=is_lunar)
    img = draw_chart(chart_data)
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    return Response(content=img_byte_arr.getvalue(), media_type="image/png")