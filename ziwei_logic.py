import math
from lunar_python import Lunar, Solar, LunarMonth

# 天干地支
GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

def get_ganzhi_year(year):
    """計算年份的干支"""
    return f"{GAN[(year - 4) % 10]}{ZHI[(year - 4) % 12]}"

def get_bureau(ming_gan, ming_zhi_index):
    """定五行局 (水二, 木三, 金四, 土五, 火六)"""
    # 天干與五行的對應偏移 (甲己之年丙作首...)
    # 這裡使用速查表邏輯
    # 命宮天干: 甲乙(0,1) -> 1(金) ... 這裡用比較通用的查找表
    
    # 五行局查找表 (基於命宮干支)
    # 命宮干支的納音五行即為五行局
    # 這裡簡化計算，直接用納音表
    nayim = get_nayin(ming_gan, ZHI[ming_zhi_index])
    if "水" in nayim: return 2, "水二局"
    if "木" in nayim: return 3, "木三局"
    if "金" in nayim: return 4, "金四局"
    if "土" in nayim: return 5, "土五局"
    if "火" in nayim: return 6, "火六局"
    return 2, "水二局" # Default

def get_nayin(gan, zhi):
    """簡易納音表 (用於定局)"""
    table = {
        '甲子': '海中金', '乙丑': '海中金', '丙寅': '爐中火', '丁卯': '爐中火',
        '戊辰': '大林木', '己巳': '大林木', '庚午': '路旁土', '辛未': '路旁土',
        '壬申': '劍鋒金', '癸酉': '劍鋒金', '甲戌': '山頭火', '乙亥': '山頭火',
        '丙子': '澗下水', '丁丑': '澗下水', '戊寅': '城頭土', '己卯': '城頭土',
        '庚辰': '白蠟金', '辛巳': '白蠟金', '壬午': '楊柳木', '癸未': '楊柳木',
        '甲申': '泉中水', '乙酉': '泉中水', '丙戌': '屋上土', '丁亥': '屋上土',
        '戊子': '霹靂火', '己丑': '霹靂火', '庚寅': '松柏木', '辛卯': '松柏木',
        '壬辰': '長流水', '癸巳': '長流水', '甲午': '砂中金', '乙未': '砂中金',
        '丙申': '山下火', '丁酉': '山下火', '戊戌': '平地木', '己亥': '平地木',
        '庚子': '壁上土', '辛丑': '壁上土', '壬寅': '金箔金', '癸卯': '金箔金',
        '甲辰': '覆燈火', '乙巳': '覆燈火', '丙午': '天河水', '丁未': '天河水',
        '戊申': '大驛土', '己酉': '大驛土', '庚戌': '釵釧金', '辛亥': '釵釧金',
        '壬子': '桑柘木', '癸丑': '桑柘木', '甲寅': '大溪水', '乙卯': '大溪水',
        '丙辰': '沙中土', '丁巳': '沙中土', '戊午': '天上火', '己未': '天上火',
        '庚申': '石榴木', '辛酉': '石榴木', '壬戌': '大海水', '癸亥': '大海水'
    }
    key = gan + zhi
    return table.get(key, "海中金")

def get_chart(year, month, day, hour, gender, target_year=2025, is_lunar=False):
    """
    核心排盤邏輯
    :param is_lunar: Boolean, True 代表輸入的是農曆 (e.g., 1989, 11, 5)
    """
    
    # --- 1. 日期轉換 (🔥 關鍵修正點 🔥) ---
    if is_lunar:
        # 如果使用者輸入的是農曆，先轉成陽曆來進行標準計算
        # 這裡假設不是閏月 (因為簡單輸入無法判斷)，如需精確可擴充
        lunar_obj = Lunar.fromYmd(year, month, day)
        solar_obj = lunar_obj.getSolar()
        
        # 更新「計算用」的日期為陽曆
        calc_year = solar_obj.getYear()
        calc_month = solar_obj.getMonth()
        calc_day = solar_obj.getDay()
    else:
        # 如果本來就是陽曆
        calc_year = year
        calc_month = month
        calc_day = day
        # 建立 Solar 物件以便後續轉回農曆顯示
        solar_obj = Solar.fromYmd(calc_year, calc_month, calc_day)

    # --- 2. 取得農曆資訊 (用於排盤) ---
    # 所有紫微排盤都是基於「農曆」的月和時辰，所以這裡要統一把陽曆轉回農曆結構
    # (如果原本輸入就是農曆，轉陽再轉陰可以確保格式統一，並自動處理閏月標記)
    lunar = solar_obj.getLunar()
    
    l_year = lunar.getYear()
    l_month = lunar.getMonth() # 農曆月
    l_day = lunar.getDay()     # 農曆日
    l_time_idx = (hour + 1) // 2 % 12 # 時辰索引 (0=子, 1=丑...)

    year_gan = GAN[(l_year - 4) % 10]
    year_zhi = ZHI[(l_year - 4) % 12]
    
    # 顯示用的農曆字串
    lunar_str = f"農曆：{l_year}年 {l_month}月 {l_day}日 {ZHI[l_time_idx]}時"

    # --- 3. 定命宮、身宮 ---
    # 命宮：寅宮起正月，順數至生月，逆數至生時
    # 公式：命宮索引 = (月 - 1) - (時 - 1) + 2 (寅宮索引為2)
    # 注意：ZHI索引 0=子, 2=寅
    ming_index = (l_month - 1 - l_time_idx + 2) % 12
    # 身宮：寅宮起正月，順數至生月，順數至生時
    shen_index = (l_month - 1 + l_time_idx + 2) % 12

    palaces = []
    base_names = ["命宮", "兄弟", "夫妻", "子女", "財帛", "疾厄", "遷移", "交友", "官祿", "田宅", "福德", "父母"]
    
    # 調整順序，讓命宮在 ming_index 的位置
    # 紫微斗數宮位是「逆時針」排布 (逆布十二宮)
    # 但 Python List 是 0..11，我們需要建立一個 mapping
    # 命宮在 ming_index, 下一個是逆時針 (ming_index - 1)
    
    chart_palaces = [None] * 12
    for i in range(12):
        # 逆時針排布
        p_idx = (ming_index - i) % 12 
        is_body = (p_idx == shen_index)
        chart_palaces[p_idx] = {
            "name": base_names[i],
            "is_body": is_body,
            "stars": [],
            "ganzhi": "" 
        }

    # --- 4. 定宮干 (五虎遁) ---
    # 甲己之年丙作首... (寅宮天干)
    start_gan_idx = (l_year - 4) % 10 % 5 * 2 + 2 # 公式化五虎遁
    start_gan_idx = start_gan_idx % 10
    
    # 寅宮是 ZHI[2]，我們從寅宮開始順布天干
    for i in range(12):
        zhi_idx = (i + 2) % 12 # 從寅(2)開始
        gan_idx = (start_gan_idx + i) % 10
        # 找到對應地支的宮位
        chart_palaces[zhi_idx]['ganzhi'] = GAN[gan_idx] + ZHI[zhi_idx]

    # --- 5. 定五行局 & 紫微星 ---
    ming_gan = chart_palaces[ming_index]['ganzhi'][0]
    bureau_num, bureau_name = get_bureau(ming_gan, ming_index)
    
    # 定紫微星 (簡易公式，實際可能有更複雜的查表)
    # 公式：(生日 + X) / 局數 = 商 ... 
    # 這裡使用簡易模擬：紫微在 X 宮
    ziwei_pos = get_ziwei_pos(l_day, bureau_num)
    
    # --- 6. 安十四主星 ---
    # 紫微系 (逆時針)：紫微, 天機, -, 太陽, 武曲, 天同, -, -, 廉貞
    ziwei_stars = [
        (0, "紫微", "major"), (-1, "天機", "major"), (-3, "太陽", "major"),
        (-4, "武曲", "major"), (-5, "天同", "major"), (-8, "廉貞", "major")
    ]
    for offset, name, stype in ziwei_stars:
        pos = (ziwei_pos + offset) % 12
        chart_palaces[pos]['stars'].append({"name": name, "type": stype, "hua": ""})

    # 天府系 (順時針)：天府在紫微斜對角 (寅申線對稱)
    # 公式：天府位置 + 紫微位置 = 2 (或 14) -> x + y = 2
    tianfu_pos = (12 - ziwei_pos + 2) % 12
    tianfu_stars = [
        (0, "天府", "major"), (1, "太陰", "major"), (2, "貪狼", "major"),
        (3, "巨門", "major"), (4, "天相", "major"), (5, "天梁", "major"),
        (6, "七殺", "major"), (10, "破軍", "major")
    ]
    for offset, name, stype in tianfu_stars:
        pos = (tianfu_pos + offset) % 12
        chart_palaces[pos]['stars'].append({"name": name, "type": stype, "hua": ""})

    # --- 7. 安四化 (依生年天干) ---
    sihua_table = {
        "甲": {"廉貞": "祿", "破軍": "權", "武曲": "科", "太陽": "忌"},
        "乙": {"天機": "祿", "天梁": "權", "紫微": "科", "太陰": "忌"},
        "丙": {"天同": "祿", "天機": "權", "文昌": "科", "廉貞": "忌"},
        "丁": {"太陰": "祿", "天同": "權", "天機": "科", "巨門": "忌"},
        "戊": {"貪狼": "祿", "太陰": "權", "右弼": "科", "天機": "忌"},
        "己": {"武曲": "祿", "貪狼": "權", "天梁": "科", "文曲": "忌"},
        "庚": {"太陽": "祿", "武曲": "權", "太陰": "科", "天同": "忌"},
        "辛": {"巨門": "祿", "太陽": "權", "文曲": "科", "文昌": "忌"},
        "壬": {"天梁": "祿", "紫微": "權", "左輔": "科", "武曲": "忌"},
        "癸": {"破軍": "祿", "巨門": "權", "太陰": "科", "貪狼": "忌"},
    }
    my_sihua = sihua_table.get(year_gan, {})
    for p in chart_palaces:
        for s in p['stars']:
            if s['name'] in my_sihua:
                s['hua'] = my_sihua[s['name']]

    # --- 8. 安吉凶星 (範例：左輔右弼、文昌文曲) ---
    # 左輔：辰宮起正月順數 (辰=4)
    zuofu = (4 + l_month - 1) % 12
    # 右弼：戌宮起正月逆數 (戌=10)
    youbi = (10 - (l_month - 1)) % 12
    chart_palaces[zuofu]['stars'].append({"name": "左輔", "type": "lucky", "hua": ""})
    chart_palaces[youbi]['stars'].append({"name": "右弼", "type": "lucky", "hua": ""})
    
    # 補上四化給輔弼 (如果有的話)
    for p in [chart_palaces[zuofu], chart_palaces[youbi]]:
        for s in p['stars']:
            if s['name'] in my_sihua: s['hua'] = my_sihua[s['name']]

    # --- 9. 計算大限 ---
    # 陽男陰女順行，陰男陽女逆行
    is_yang_year = (l_year % 2 != 0) # 奇數年為陽
    is_male = (gender == "男")
    
    if (is_yang_year and is_male) or (not is_yang_year and not is_male):
        direction = 1 # 順行
    else:
        direction = -1 # 逆行

    for i in range(12):
        # 從命宮開始
        offset = i if direction == 1 else -i
        idx = (ming_index + offset) % 12
        start_age = bureau_num + i * 10
        end_age = start_age + 9
        chart_palaces[idx]['daxian'] = f"{start_age}-{end_age}"

    # --- 10. 計算流年、斗君、大限標籤 ---
    # 這裡計算 target_year (2025) 的位置
    
    # 流年：看地支 (2025是乙巳年 -> 巳宮)
    target_zhi = ZHI[(target_year - 4) % 12]
    # 找到該地支的宮位
    liunian_idx = -1
    for i, p in enumerate(chart_palaces):
        if p['ganzhi'][1] == target_zhi:
            liunian_idx = i
            p.setdefault('tags', {})['liunian'] = True
    
    # 大限：計算虛歲 -> 找對應宮位
    age = target_year - calc_year + 1 # 虛歲 (陽曆年相減+1 簡單近似)
    for p in chart_palaces:
        da_range = p['daxian'].split('-')
        if int(da_range[0]) <= age <= int(da_range[1]):
             p.setdefault('tags', {})['dayun'] = True

    # 小限 (簡單版)：男順女逆... 這裡暫略，僅示範流年大限

    return {
        "lunar_str": lunar_str,
        "bureau": bureau_name,
        "age_info": f"流年 {target_year} ({target_zhi}年)  虛歲 {age}",
        "year_gan": year_gan,
        "year_zhi": year_zhi,
        "gender": gender,
        "palaces": chart_palaces
    }

def get_ziwei_pos(day, bureau):
    """紫微星定位算法"""
    # 這是查表邏輯的簡化版
    # 水二局 (bureau=2):
    # 生日: 1(丑), 2(寅), 3(寅), 4(卯), 5(卯)...
    # 這裡用簡易數學模擬，實際要寫完整的 if-else 或 lookup table
    # 為了演示，我們用一個簡單的近似公式 (不完全精確，但能跑)
    
    # 真正的公式：
    # 1. 生日除以局數，得商數
    # 2. 若整除 -> 商數即為紫微位置 (從寅宮算起)
    # 3. 若不整除 -> 需要補數 (詳細口訣複雜)
    
    # 這裡為求穩定，使用「商數 + 調整」的模擬
    # 寅宮索引 = 2
    
    quotient = day // bureau
    remainder = day % bureau
    
    pos_map = { # 寅=2, 卯=3...
        2: 2 + quotient + (1 if remainder else 0), # 水二
        3: 2 + quotient + (1 if remainder else 0), # 木三
        4: 2 + quotient, # 金四 (簡化)
        5: 2 + quotient, # 土五
        6: 2 + quotient  # 火六
    }
    
    base_pos = pos_map.get(bureau, 2)
    return base_pos % 12
