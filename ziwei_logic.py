import math
from lunar_python import Lunar, Solar

# --- 基礎資料 ---
GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 五行局納音表 (用於精確五行局)
NAYIN_BUREAU = {
    '甲子': 4, '乙丑': 4, '丙寅': 6, '丁卯': 6, '戊辰': 3, '己巳': 3, '庚午': 5, '辛未': 5, '壬申': 4, '癸酉': 4, '甲戌': 6, '乙亥': 6,
    '丙子': 2, '丁丑': 2, '戊寅': 5, '己卯': 5, '庚辰': 4, '辛巳': 4, '壬午': 3, '癸未': 3, '甲申': 2, '乙酉': 2, '丙戌': 5, '丁亥': 5,
    '戊子': 6, '己丑': 6, '庚寅': 3, '辛卯': 3, '壬辰': 2, '癸巳': 2, '甲午': 4, '乙未': 4, '丙申': 6, '丁酉': 6, '戊戌': 3, '己亥': 3,
    '庚子': 5, '辛丑': 5, '壬寅': 4, '癸卯': 4, '甲辰': 6, '乙巳': 6, '丙午': 2, '丁未': 2, '戊申': 5, '己酉': 5, '庚戌': 4, '辛亥': 4,
    '壬子': 3, '癸丑': 3, '甲寅': 2, '乙卯': 2, '丙辰': 5, '丁巳': 5, '戊午': 6, '己未': 6, '庚申': 3, '辛酉': 3, '壬戌': 2, '癸亥': 2
}
BUREAU_NAMES = {2: "水二局", 3: "木三局", 4: "金四局", 5: "土五局", 6: "火六局"}

def get_chart(year, month, day, hour, gender, target_year=2025, is_lunar=False):
    """
    紫微斗數核心排盤 (修正版)
    """
    
    # --- 1. 時間標準化 (最重要的一步) ---
    if is_lunar:
        # 使用者輸入農曆 (ex: 1989, 11, 5) -> 轉成陽曆 (1989, 12, 2)
        try:
            lunar_obj = Lunar.fromYmd(year, month, day)
            solar_obj = lunar_obj.getSolar()
        except:
            # 防呆：如果日期不存在，回傳錯誤結構
            return error_chart("日期格式錯誤")
    else:
        # 使用者輸入陽曆
        solar_obj = Solar.fromYmd(year, month, day)

    # 用「陽曆」建立標準 Lunar 物件，確保閏月等資訊正確
    # 這裡很關鍵：紫微斗數排盤要用這個 lunar 變數的月、日
    lunar = solar_obj.getLunar()
    
    l_year = lunar.getYear()
    l_month = lunar.getMonth()
    if l_month < 0: l_month = abs(l_month) # 處理閏月 (lunar-python 閏月是負數)
    l_day = lunar.getDay()
    
    # 時辰轉換 (子=0, 丑=1...)
    time_idx = (hour + 1) // 2 % 12
    
    # 生年干支
    year_gan = GAN[(l_year - 4) % 10]
    year_zhi = ZHI[(l_year - 4) % 12]

    # --- 2. 定命宮、身宮 ---
    # 命宮：寅宮起正月，順數至生月，逆數至生時
    # 公式：(月 - 時) + 寅宮修正(2)
    ming_idx = (l_month - 1 - time_idx + 2) % 12
    
    # 身宮：寅宮起正月，順數至生月，順數至生時
    shen_idx = (l_month - 1 + time_idx + 2) % 12

    # --- 3. 定十二宮干 (五虎遁) ---
    # 寅宮天干：甲己之年丙作首...
    start_gan_idx = (l_year - 4) % 10 % 5 * 2 + 2
    start_gan_idx %= 10
    
    palaces = [None] * 12
    base_names = ["命宮", "兄弟", "夫妻", "子女", "財帛", "疾厄", "遷移", "交友", "官祿", "田宅", "福德", "父母"]
    
    # 建立宮位結構
    for i in range(12):
        # 逆布十二宮：命宮在 ming_idx，下一個是 ming_idx-1
        current_idx = (ming_idx - i) % 12
        
        # 計算該宮位的干支
        # 該宮位的地支是固定的 (0=子, 1=丑...)
        # 但我們列表 palace[0] 代表「子宮」，palace[1] 代表「丑宮」
        # 所以我們要填入對應的名稱
        
        # 修正：palaces 陣列索引 0=子宮, 1=丑宮...
        # 命宮名稱應該填在 ming_idx 的位置
        palace_zhi_idx = current_idx
        
        # 計算該宮天干 (從寅宮 ZHI[2] 開始順排)
        # 寅宮(2) 的天干是 GAN[start_gan_idx]
        # 公式：(宮位 - 2) + 起始干
        p_gan_idx = (palace_zhi_idx - 2 + start_gan_idx) % 10
        p_ganzhi = GAN[p_gan_idx] + ZHI[palace_zhi_idx]
        
        palaces[current_idx] = {
            "name": base_names[i],
            "is_body": (current_idx == shen_idx),
            "ganzhi": p_ganzhi,
            "stars": [],
            "daxian": ""
        }

    # --- 4. 定五行局 (精確版) ---
    # 依命宮干支的納音
    ming_ganzhi = palaces[ming_idx]['ganzhi']
    bureau_num = NAYIN_BUREAU.get(ming_ganzhi, 2) # 預設水二
    bureau_name = BUREAU_NAMES[bureau_num]

    # --- 5. 安紫微星 (🔥 修正演算法 🔥) ---
    # 公式：(生日 + X) / 局數
    # 邏輯：生日除以局數，若整除，則商數即為位置。若不整除，需補數。
    
    remainder = l_day % bureau_num
    quotient = l_day // bureau_num
    
    ziwei_pos = 0 # 0=子, 1=丑...
    
    if remainder == 0:
        # 整除：寅宮起 1，順行至商數
        # ZHI[2] = 寅
        ziwei_pos = (2 + (quotient - 1)) % 12
    else:
        # 不整除：需補數 (局數 - 餘數)
        add_num = bureau_num - remainder
        new_quotient = quotient + 1
        # 補數為奇數時? 紫微斗數全書公式：
        # (生日 + 補數) / 局數 = 商數
        # 位置 = (寅宮起商數) - 補數 (若補數為奇數? 偶數? 這裡有不同流派，採用標準盤邏輯)
        
        # 標準口訣：
        # 1. 商數位置 (從寅開始)
        base_pos = (2 + (new_quotient - 1)) % 12
        # 2. 扣掉補數 (若補數是奇數則逆退? 其實是直接逆退補數之數)
        # 公式：商數所落之宮 - 補數
        ziwei_pos = (base_pos - add_num) % 12

    # --- 6. 安十四主星 ---
    # 紫微系 (逆時針)
    # 紫微, 天機, -, 太陽, 武曲, 天同, -, -, 廉貞
    ziwei_offsets = {0: "紫微", -1: "天機", -3: "太陽", -4: "武曲", -5: "天同", -8: "廉貞"}
    for offset, name in ziwei_offsets.items():
        idx = (ziwei_pos + offset) % 12
        palaces[idx]['stars'].append({"name": name, "type": "major", "hua": ""})

    # 天府系 (順時針)
    # 天府與紫微 對照寅申線 (紫微+天府 = 2 或 14) -> x + y = 2
    tianfu_pos = (2 - ziwei_pos) % 12 
    tianfu_offsets = {0: "天府", 1: "太陰", 2: "貪狼", 3: "巨門", 4: "天相", 5: "天梁", 6: "七殺", 10: "破軍"}
    for offset, name in tianfu_offsets.items():
        idx = (tianfu_pos + offset) % 12
        palaces[idx]['stars'].append({"name": name, "type": "major", "hua": ""})

    # --- 7. 安四化 (依生年干) ---
    SIHUA = {
        "甲": {"廉貞":"祿", "破軍":"權", "武曲":"科", "太陽":"忌"},
        "乙": {"天機":"祿", "天梁":"權", "紫微":"科", "太陰":"忌"},
        "丙": {"天同":"祿", "天機":"權", "文昌":"科", "廉貞":"忌"},
        "丁": {"太陰":"祿", "天同":"權", "天機":"科", "巨門":"忌"},
        "戊": {"貪狼":"祿", "太陰":"權", "右弼":"科", "天機":"忌"},
        "己": {"武曲":"祿", "貪狼":"權", "天梁":"科", "文曲":"忌"},
        "庚": {"太陽":"祿", "武曲":"權", "太陰":"科", "天同":"忌"},
        "辛": {"巨門":"祿", "太陽":"權", "文曲":"科", "文昌":"忌"},
        "壬": {"天梁":"祿", "紫微":"權", "左輔":"科", "武曲":"忌"},
        "癸": {"破軍":"祿", "巨門":"權", "太陰":"科", "貪狼":"忌"},
    }
    my_sihua = SIHUA.get(year_gan, {})
    for p in palaces:
        for s in p['stars']:
            if s['name'] in my_sihua: s['hua'] = my_sihua[s['name']]

    # --- 8. 輔佐煞星 (僅示範左輔右弼) ---
    # 左輔：辰(4)起正月順數
    zuofu_pos = (4 + (l_month - 1)) % 12
    # 右弼：戌(10)起正月逆數
    youbi_pos = (10 - (l_month - 1)) % 12
    
    palaces[zuofu_pos]['stars'].append({"name": "左輔", "type": "lucky", "hua": my_sihua.get("左輔", "")})
    palaces[youbi_pos]['stars'].append({"name": "右弼", "type": "lucky", "hua": my_sihua.get("右弼", "")})

    # --- 9. 大限 (起命宮) ---
    is_yang_year = ((l_year - 4) % 2 == 0) # 甲(0)陽, 乙(1)陰...
    is_male = (gender == "男")
    
    # 陽男陰女順行(1)，陰男陽女逆行(-1)
    if (is_yang_year and is_male) or (not is_yang_year and not is_male):
        direction = 1
    else:
        direction = -1
        
    for i in range(12):
        offset = i if direction == 1 else -i
        idx = (ming_idx + offset) % 12
        start_age = bureau_num + i * 10
        end_age = start_age + 9
        palaces[idx]['daxian'] = f"{start_age}-{end_age}"

    # --- 10. 流年標籤 (2025乙巳年) ---
    target_zhi_char = ZHI[(target_year - 4) % 12] # 2025 -> 巳
    
    # 計算虛歲
    age = target_year - solar_obj.getYear() + 1
    
    for i, p in enumerate(palaces):
        p['tags'] = {}
        # 流年：找宮位地支
        if ZHI[i] == target_zhi_char:
            p['tags']['liunian'] = True
            
        # 大限：看虛歲落在哪個區間
        start, end = map(int, p['daxian'].split('-'))
        if start <= age <= end:
            p['tags']['dayun'] = True

    return {
        "lunar_str": f"農曆：{l_year}年 {l_month}月 {l_day}日 {ZHI[time_idx]}時",
        "bureau": bureau_name,
        "age_info": f"流年 {target_year} ({target_zhi_char}年)  虛歲 {age}",
        "year_gan": year_gan,
        "year_zhi": year_zhi,
        "gender": gender,
        "palaces": palaces
    }

def error_chart(msg):
    # 回傳一個空的錯誤結構，避免畫圖當機
    return {
        "lunar_str": msg, "bureau": "-", "age_info": "-",
        "year_gan": "-", "year_zhi": "-", "gender": "-",
        "palaces": [{"name": "-", "ganzhi": "-", "stars": [], "daxian": "-", "is_body": False} for _ in range(12)]
    }
