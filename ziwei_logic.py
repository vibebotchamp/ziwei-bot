import math
from lunar_python import Lunar, Solar

# --- 基礎資料 ---
GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 五行局納音表 (定局神器，絕對準確)
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
    紫微斗數排盤 (終極修正版：正確日期 + 正確紫微星 + 完整吉煞星)
    """
    
    # --- 1. 時間標準化 (陰陽曆轉換) ---
    if is_lunar:
        try:
            lunar_obj = Lunar.fromYmd(year, month, day)
            solar_obj = lunar_obj.getSolar()
        except:
            return error_chart("日期格式錯誤")
    else:
        solar_obj = Solar.fromYmd(year, month, day)

    lunar = solar_obj.getLunar()
    l_year = lunar.getYear()
    l_month = lunar.getMonth()
    if l_month < 0: l_month = abs(l_month) # 處理閏月
    l_day = lunar.getDay()
    
    # 時辰索引 (0=子, 1=丑...)
    time_idx = (hour + 1) // 2 % 12
    
    year_gan_idx = (l_year - 4) % 10
    year_zhi_idx = (l_year - 4) % 12
    year_gan = GAN[year_gan_idx]
    year_zhi = ZHI[year_zhi_idx]

    # --- 2. 定命宮、身宮 ---
    # 命宮 = 月數 - 時數 + 寅宮(2)
    ming_idx = (l_month - 1 - time_idx + 2) % 12
    # 身宮 = 月數 + 時數 + 寅宮(2)
    shen_idx = (l_month - 1 + time_idx + 2) % 12

    # --- 3. 佈十二宮 (含干支) ---
    # 五虎遁：甲己之年丙作首...
    start_gan_idx = (year_gan_idx % 5) * 2 + 2
    start_gan_idx %= 10
    
    palaces = [None] * 12
    base_names = ["命宮", "兄弟", "夫妻", "子女", "財帛", "疾厄", "遷移", "交友", "官祿", "田宅", "福德", "父母"]
    
    for i in range(12):
        # 逆布十二宮
        current_idx = (ming_idx - i) % 12
        
        # 宮位天干
        p_gan_idx = (current_idx - 2 + start_gan_idx) % 10
        p_ganzhi = GAN[p_gan_idx] + ZHI[current_idx]
        
        palaces[current_idx] = {
            "name": base_names[i],
            "is_body": (current_idx == shen_idx),
            "ganzhi": p_ganzhi,
            "stars": [],
            "daxian": ""
        }

    # --- 4. 定五行局 ---
    ming_ganzhi = palaces[ming_idx]['ganzhi']
    bureau_num = NAYIN_BUREAU.get(ming_ganzhi, 2)
    bureau_name = BUREAU_NAMES[bureau_num]

    # --- 5. 安紫微星 (標準公式) ---
    remainder = l_day % bureau_num
    quotient = l_day // bureau_num
    ziwei_pos = 0
    if remainder == 0:
        ziwei_pos = (2 + (quotient - 1)) % 12
    else:
        add_num = bureau_num - remainder
        new_quotient = quotient + 1
        base_pos = (2 + (new_quotient - 1)) % 12
        ziwei_pos = (base_pos - add_num) % 12

    # --- 6. 安十四主星 ---
    # 紫微系
    ziwei_offsets = {0: "紫微", -1: "天機", -3: "太陽", -4: "武曲", -5: "天同", -8: "廉貞"}
    for offset, name in ziwei_offsets.items():
        idx = (ziwei_pos + offset) % 12
        palaces[idx]['stars'].append({"name": name, "type": "major", "hua": ""})

    # 天府系 (寅申線對稱)
    tianfu_pos = (2 - ziwei_pos) % 12 
    tianfu_offsets = {0: "天府", 1: "太陰", 2: "貪狼", 3: "巨門", 4: "天相", 5: "天梁", 6: "七殺", 10: "破軍"}
    for offset, name in tianfu_offsets.items():
        idx = (tianfu_pos + offset) % 12
        palaces[idx]['stars'].append({"name": name, "type": "major", "hua": ""})

    # --- 7. 🔥 安吉星與煞星 (找回遺失的星星！) 🔥 ---
    
    # 7.1 左輔右弼 (依月分)
    # 左輔：辰(4)順數月
    zuofu = (4 + l_month - 1) % 12
    # 右弼：戌(10)逆數月
    youbi = (10 - (l_month - 1)) % 12
    palaces[zuofu]['stars'].append({"name": "左輔", "type": "lucky", "hua": ""})
    palaces[youbi]['stars'].append({"name": "右弼", "type": "lucky", "hua": ""})

    # 7.2 文昌文曲 (依時辰)
    # 文昌：戌(10)逆數時
    wenchang = (10 - time_idx) % 12
    # 文曲：辰(4)順數時
    wenqu = (4 + time_idx) % 12
    palaces[wenchang]['stars'].append({"name": "文昌", "type": "lucky", "hua": ""})
    palaces[wenqu]['stars'].append({"name": "文曲", "type": "lucky", "hua": ""})

    # 7.3 天魁天鉞 (依年干)
    kui_yue_table = {
        "甲": (1, 7), "乙": (0, 8), "丙": (11, 9), "丁": (11, 9), "戊": (1, 7),
        "己": (0, 8), "庚": (1, 7), "辛": (6, 2), "壬": (3, 5), "癸": (3, 5)
    }
    if year_gan in kui_yue_table:
        k, y = kui_yue_table[year_gan]
        palaces[k]['stars'].append({"name": "天魁", "type": "lucky", "hua": ""})
        palaces[y]['stars'].append({"name": "天鉞", "type": "lucky", "hua": ""})

    # 7.4 祿存、擎羊、陀羅 (依年干)
    lucun_table = {"甲": 2, "乙": 3, "丙": 5, "丁": 6, "戊": 5, "己": 6, "庚": 8, "辛": 9, "壬": 11, "癸": 0}
    if year_gan in lucun_table:
        lu_idx = lucun_table[year_gan]
        yang_idx = (lu_idx + 1) % 12 # 擎羊在祿存前
        tuo_idx = (lu_idx - 1) % 12  # 陀羅在祿存後
        # 祿存通常不單獨列為吉星，但可顯示，這裡僅示範煞星
        # palaces[lu_idx]['stars'].append({"name": "祿存", "type": "lucky", "hua": ""}) 
        palaces[yang_idx]['stars'].append({"name": "擎羊", "type": "bad", "hua": ""})
        palaces[tuo_idx]['stars'].append({"name": "陀羅", "type": "bad", "hua": ""})

    # 7.5 火星、鈴星 (依年支+時支)
    # 簡易口訣：
    # 寅午戌人丑卯方，申子辰人寅戌揚，亥卯未人酉戌位，巳酉丑人卯戌房 (火星)
    # 這裡用查表法較穩
    huo_start = {"寅": 1, "午": 1, "戌": 1, "申": 2, "子": 2, "辰": 2, "亥": 9, "卯": 9, "未": 9, "巳": 3, "酉": 3, "丑": 3}
    ling_start = {"寅": 3, "午": 3, "戌": 3, "申": 10, "子": 10, "辰": 10, "亥": 10, "卯": 10, "未": 10, "巳": 10, "酉": 10, "丑": 10}
    
    if year_zhi in huo_start:
        # 順數時
        huo_pos = (huo_start[year_zhi] + time_idx) % 12
        palaces[huo_pos]['stars'].append({"name": "火星", "type": "bad", "hua": ""})
        
    if year_zhi in ling_start:
        # 順數時
        ling_pos = (ling_start[year_zhi] + time_idx) % 12
        palaces[ling_pos]['stars'].append({"name": "鈴星", "type": "bad", "hua": ""})

    # 7.6 地空地劫 (依時辰)
    # 地劫：亥(11)順數時
    dijie = (11 + time_idx) % 12
    # 地空：亥(11)逆數時
    dikong = (11 - time_idx) % 12
    palaces[dijie]['stars'].append({"name": "地劫", "type": "bad", "hua": ""})
    palaces[dikong]['stars'].append({"name": "地空", "type": "bad", "hua": ""})


    # --- 8. 安四化 (含吉煞星) ---
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

    # --- 9. 計算大限 ---
    is_yang_year = ((l_year - 4) % 2 == 0) 
    is_male = (gender == "男")
    direction = 1 if (is_yang_year and is_male) or (not is_yang_year and not is_male) else -1
        
    for i in range(12):
        offset = i if direction == 1 else -i
        idx = (ming_idx + offset) % 12
        start_age = bureau_num + i * 10
        end_age = start_age + 9
        palaces[idx]['daxian'] = f"{start_age}-{end_age}"

    # --- 10. 流年/大限標籤 ---
    target_zhi_char = ZHI[(target_year - 4) % 12]
    age = target_year - solar_obj.getYear() + 1
    
    for i, p in enumerate(palaces):
        p['tags'] = {}
        if ZHI[i] == target_zhi_char: p['tags']['liunian'] = True
        start, end = map(int, p['daxian'].split('-'))
        if start <= age <= end: p['tags']['dayun'] = True

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
    return {
        "lunar_str": msg, "bureau": "-", "age_info": "-",
        "year_gan": "-", "year_zhi": "-", "gender": "-",
        "palaces": [{"name": "-", "ganzhi": "-", "stars": [], "daxian": "-", "is_body": False} for _ in range(12)]
    }
