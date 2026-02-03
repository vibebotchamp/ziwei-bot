import math
from lunar_python import Lunar, Solar

# --- 基礎資料 ---
GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 納音五行局對照表
NAYIN = {
    '甲子': 4, '乙丑': 4, '丙寅': 6, '丁卯': 6, '戊辰': 3, '己巳': 3, '庚午': 5, '辛未': 5, '壬申': 4, '癸酉': 4, '甲戌': 6, '乙亥': 6,
    '丙子': 2, '丁丑': 2, '戊寅': 5, '己卯': 5, '庚辰': 4, '辛巳': 4, '壬午': 3, '癸未': 3, '甲申': 2, '乙酉': 2, '丙戌': 5, '丁亥': 5,
    '戊子': 6, '己丑': 6, '庚寅': 3, '辛卯': 3, '壬辰': 2, '癸巳': 2, '甲午': 4, '乙未': 4, '丙申': 6, '丁酉': 6, '戊戌': 3, '己亥': 3,
    '庚子': 5, '辛丑': 5, '壬寅': 4, '癸卯': 4, '甲辰': 6, '乙巳': 6, '丙午': 2, '丁未': 2, '戊申': 5, '己酉': 5, '庚戌': 4, '辛亥': 4,
    '壬子': 3, '癸丑': 3, '甲寅': 2, '乙卯': 2, '丙辰': 5, '丁巳': 5, '戊午': 6, '己未': 6, '庚申': 3, '辛酉': 3, '壬戌': 2, '癸亥': 2
}
BUREAU_NAMES = {2: "水二局", 3: "木三局", 4: "金四局", 5: "土五局", 6: "火六局"}

def get_chart(year, month, day, hour, gender, target_year=2025, is_lunar=False):
    # --- 1. 日期處理 ---
    if is_lunar:
        try:
            lunar_obj = Lunar.fromYmd(year, month, day)
            solar_obj = lunar_obj.getSolar()
        except:
            return error_chart("日期錯誤")
    else:
        solar_obj = Solar.fromYmd(year, month, day)

    lunar = solar_obj.getLunar()
    l_year = lunar.getYear()
    l_month = lunar.getMonth()
    if l_month < 0: l_month = abs(l_month)
    l_day = lunar.getDay()
    
    time_idx = (hour + 1) // 2 % 12
    
    year_gan_idx = (l_year - 4) % 10
    year_zhi_idx = (l_year - 4) % 12
    year_gan = GAN[year_gan_idx]
    year_zhi = ZHI[year_zhi_idx]

    # --- 2. 定命身宮 ---
    # 命宮 = 寅(2) + (月-1) - 時
    ming_idx = (2 + (l_month - 1) - time_idx) % 12
    # 身宮 = 寅(2) + (月-1) + 時
    shen_idx = (2 + (l_month - 1) + time_idx) % 12

    # --- 3. 佈十二宮 & 五虎遁 (🔥修正BUG🔥) ---
    # 起始干 (寅宮)
    start_gan_idx = (year_gan_idx % 5) * 2 + 2
    start_gan_idx %= 10
    
    palaces = [None] * 12
    base_names = ["命宮", "兄弟", "夫妻", "子女", "財帛", "疾厄", "遷移", "交友", "官祿", "田宅", "福德", "父母"]
    
    for i in range(12):
        current_idx = (ming_idx - i) % 12
        
        # 🔥 修正宮干公式：先算距離寅宮幾步，再加起始干
        # 寅(2) -> 距離0, 卯(3) -> 距離1 ... 子(0) -> 距離10
        steps_from_yin = (current_idx - 2) % 12
        p_gan_idx = (start_gan_idx + steps_from_yin) % 10
        
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
    bureau_num = NAYIN.get(ming_ganzhi, 2)
    bureau_name = BUREAU_NAMES[bureau_num]

    # --- 5. 安紫微星 ---
    ziwei_pos = get_ziwei_location(l_day, bureau_num)

    # --- 6. 安十四主星 (🔥修正天府公式🔥) ---
    # 紫微系
    ziwei_map = {0: "紫微", 11: "天機", 9: "太陽", 8: "武曲", 7: "天同", 4: "廉貞"}
    for offset, name in ziwei_map.items():
        idx = (ziwei_pos + offset) % 12
        palaces[idx]['stars'].append({"name": name, "type": "major", "hua": ""})

    # 天府系 (🔥修正：使用標準斜對角公式 (4 - 紫微) )
    # 公式：(4 - 紫微) % 12 (以子0為基準)
    # 例如：紫微在子(0) -> 天府在辰(4)。紫微在午(6) -> 天府在戌(10)。
    tianfu_pos = (4 - ziwei_pos) % 12
    
    tianfu_map = {0: "天府", 1: "太陰", 2: "貪狼", 3: "巨門", 4: "天相", 5: "天梁", 6: "七殺", 10: "破軍"}
    for offset, name in tianfu_map.items():
        idx = (tianfu_pos + offset) % 12
        palaces[idx]['stars'].append({"name": name, "type": "major", "hua": ""})

    # --- 7. 安吉煞星 ---
    
    # 昌曲
    wenchang = (10 - time_idx) % 12
    wenqu = (4 + time_idx) % 12
    palaces[wenchang]['stars'].append({"name": "文昌", "type": "lucky", "hua": ""})
    palaces[wenqu]['stars'].append({"name": "文曲", "type": "lucky", "hua": ""})

    # 輔弼
    zuofu = (4 + l_month - 1) % 12
    youbi = (10 - (l_month - 1)) % 12
    palaces[zuofu]['stars'].append({"name": "左輔", "type": "lucky", "hua": ""})
    palaces[youbi]['stars'].append({"name": "右弼", "type": "lucky", "hua": ""})

    # 魁鉞
    kui_yue = {
        "甲": (1, 7), "戊": (1, 7), "庚": (1, 7),
        "乙": (0, 8), "己": (0, 8),
        "丙": (11, 9), "丁": (11, 9),
        "壬": (3, 5), "癸": (3, 5),
        "辛": (6, 2)
    }
    if year_gan in kui_yue:
        k, y = kui_yue[year_gan]
        palaces[k]['stars'].append({"name": "天魁", "type": "lucky", "hua": ""})
        palaces[y]['stars'].append({"name": "天鉞", "type": "lucky", "hua": ""})

    # 祿存、羊陀
    lucun_pos_map = {"甲": 2, "乙": 3, "丙": 5, "丁": 6, "戊": 5, "己": 6, "庚": 8, "辛": 9, "壬": 11, "癸": 0}
    if year_gan in lucun_pos_map:
        lu = lucun_pos_map[year_gan]
        yang = (lu + 1) % 12
        tuo = (lu - 1) % 12
        palaces[lu]['stars'].append({"name": "祿存", "type": "lucky", "hua": ""})
        palaces[yang]['stars'].append({"name": "擎羊", "type": "bad", "hua": ""})
        palaces[tuo]['stars'].append({"name": "陀羅", "type": "bad", "hua": ""})

    # 火鈴
    huo_ling_start = {
        "寅": (1, 3), "午": (1, 3), "戌": (1, 3),
        "申": (2, 10), "子": (2, 10), "辰": (2, 10),
        "巳": (3, 10), "酉": (3, 10), "丑": (3, 10),
        "亥": (9, 10), "卯": (9, 10), "未": (9, 10)
    }
    if year_zhi in huo_ling_start:
        h_start, l_start = huo_ling_start[year_zhi]
        huo = (h_start + time_idx) % 12
        ling = (l_start + time_idx) % 12
        palaces[huo]['stars'].append({"name": "火星", "type": "bad", "hua": ""})
        palaces[ling]['stars'].append({"name": "鈴星", "type": "bad", "hua": ""})

    # 空劫
    dijie = (11 + time_idx) % 12
    dikong = (11 - time_idx) % 12
    palaces[dijie]['stars'].append({"name": "地劫", "type": "bad", "hua": ""})
    palaces[dikong]['stars'].append({"name": "地空", "type": "bad", "hua": ""})

    # 天馬 (年支) - 寅午戌在申
    tianma_map = {"寅": 8, "午": 8, "戌": 8, "申": 2, "子": 2, "辰": 2, "巳": 11, "酉": 11, "丑": 11, "亥": 5, "卯": 5, "未": 5}
    if year_zhi in tianma_map:
        palaces[tianma_map[year_zhi]]['stars'].append({"name": "天馬", "type": "flower", "hua": ""})

    # 紅鸞天喜
    hongluan = (3 - year_zhi_idx) % 12
    tianxi = (hongluan + 6) % 12
    palaces[hongluan]['stars'].append({"name": "紅鸞", "type": "flower", "hua": ""})
    palaces[tianxi]['stars'].append({"name": "天喜", "type": "flower", "hua": ""})

    # 天刑天姚
    tianxing = (9 + l_month - 1) % 12
    tianyao = (1 + l_month - 1) % 12
    palaces[tianxing]['stars'].append({"name": "天刑", "type": "bad", "hua": ""})
    palaces[tianyao]['stars'].append({"name": "天姚", "type": "bad", "hua": ""})

    # --- 8. 四化 ---
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

    # --- 9. 大限 ---
    is_yang_year = ((l_year - 4) % 2 == 0) 
    is_male = (gender == "男")
    direction = 1 if (is_yang_year and is_male) or (not is_yang_year and not is_male) else -1
    
    for i in range(12):
        offset = i * direction
        idx = (ming_idx + offset) % 12
        start_age = bureau_num + i * 10
        end_age = start_age + 9
        palaces[idx]['daxian'] = f"{start_age}-{end_age}"

    # --- 10. 流年標籤 ---
    target_zhi_char = ZHI[(target_year - 4) % 12] 
    age = target_year - solar_obj.getYear() + 1
    
    for i, p in enumerate(palaces):
        p['tags'] = {}
        if ZHI[i] == target_zhi_char: p['tags']['liunian'] = True
        start, end = map(int, p['daxian'].split('-'))
        if start <= age <= end: p['tags']['dayun'] = True

    date_str = f"農曆：{l_year}年 {l_month}月 {l_day}日"
    if not is_lunar:
        date_str = f"國曆：{year}年 {month}月 {day}日"

    return {
        "lunar_str": date_str,
        "bureau": bureau_name,
        "age_info": f"流年 {target_year} ({target_zhi_char}年)  虛歲 {age}",
        "year_gan": year_gan,
        "year_zhi": year_zhi,
        "gender": gender,
        "palaces": palaces
    }

def get_ziwei_location(day, bureau):
    remainder = day % bureau
    quotient = day // bureau
    
    if remainder == 0:
        return (2 + (quotient - 1)) % 12
    else:
        supplement = bureau - remainder
        new_quotient = (day + supplement) // bureau
        base_pos = (2 + (new_quotient - 1)) % 12
        if supplement % 2 == 1:
            return (base_pos - supplement) % 12
        else:
            return (base_pos + supplement) % 12

def error_chart(msg):
    return {
        "lunar_str": msg, "bureau": "-", "age_info": "-",
        "year_gan": "-", "year_zhi": "-", "gender": "-",
        "palaces": [{"name": "-", "ganzhi": "-", "stars": [], "daxian": "-", "is_body": False} for _ in range(12)]
    }
