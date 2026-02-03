from lunar_python import Solar, Lunar
import math

# --- 基礎資料 ---
ZHI = list('子丑寅卯辰巳午未申酉戌亥')
GAN = list('甲乙丙丁戊己庚辛壬癸')
PALACES_NAMES = list('命宮,兄弟,夫妻,子女,財帛,疾厄,遷移,交友,官祿,田宅,福德,父母'.split(','))

# 五行局名稱
BUREAU_NAMES = {2: "水二局", 3: "木三局", 4: "金四局", 5: "土五局", 6: "火六局"}

# 四化表
SIHUA = {
    '甲': {'廉貞': '祿', '破軍': '權', '武曲': '科', '太陽': '忌'},
    '乙': {'天機': '祿', '天梁': '權', '紫微': '科', '太陰': '忌'},
    '丙': {'天同': '祿', '天機': '權', '文昌': '科', '廉貞': '忌'},
    '丁': {'太陰': '祿', '天同': '權', '天機': '科', '巨門': '忌'},
    '戊': {'貪狼': '祿', '太陰': '權', '右弼': '科', '天機': '忌'},
    '己': {'武曲': '祿', '貪狼': '權', '天梁': '科', '文曲': '忌'},
    '庚': {'太陽': '祿', '武曲': '權', '太陰': '科', '天同': '忌'},
    '辛': {'巨門': '祿', '太陽': '權', '文曲': '科', '文昌': '忌'},
    '壬': {'天梁': '祿', '紫微': '權', '左輔': '科', '武曲': '忌'},
    '癸': {'破軍': '祿', '巨門': '權', '太陰': '科', '貪狼': '忌'}
}

# --- 核心演算法：納音五行計算 ---
def get_nayin_number(gan_idx, zhi_idx):
    full_map = {
        '甲子': 4, '乙丑': 4, '丙寅': 6, '丁卯': 6, '戊辰': 3, '己巳': 3, '庚午': 5, '辛未': 5, '壬申': 4, '癸酉': 4,
        '甲戌': 6, '乙亥': 6, '丙子': 2, '丁丑': 2, '戊寅': 5, '己卯': 5, '庚辰': 4, '辛巳': 4, '壬午': 3, '癸未': 3,
        '甲申': 2, '乙酉': 2, '丙戌': 5, '丁亥': 5, '戊子': 6, '己丑': 6, '庚寅': 3, '辛卯': 3, '壬辰': 2, '癸巳': 2,
        '甲午': 4, '乙未': 4, '丙申': 6, '丁酉': 6, '戊戌': 3, '己亥': 3, '庚子': 5, '辛丑': 5, '壬寅': 4, '癸卯': 4,
        '甲辰': 6, '乙巳': 6, '丙午': 2, '丁未': 2, '戊申': 5, '己酉': 5, '庚戌': 4, '辛亥': 4, '壬子': 3, '癸丑': 3,
        '甲寅': 2, '乙卯': 2, '丙辰': 5, '丁巳': 5, '戊午': 6, '己未': 6, '庚申': 3, '辛酉': 3, '壬戌': 2, '癸亥': 2
    }
    gan = GAN[gan_idx]
    zhi = ZHI[zhi_idx]
    return full_map.get(gan + zhi, 2)

def get_chart(year, month, day, hour, gender="女", target_year=2025, is_lunar=False):
    # 1. 時間處理
    if is_lunar:
        lunar_year = year
        lunar_month = month
        lunar_day = day
        offset = (year - 4) % 60
        year_gan_idx = offset % 10
        year_zhi_idx = offset % 12
        year_gan = GAN[year_gan_idx]
        year_zhi = ZHI[year_zhi_idx]
    else:
        solar = Solar.fromYmd(year, month, day)
        lunar = solar.getLunar()
        lunar_year = lunar.getYear()
        lunar_month = lunar.getMonth()
        if lunar_month < 0: lunar_month *= -1
        lunar_day = lunar.getDay()
        year_gan = lunar.getYearGan() 
        year_zhi = lunar.getYearZhi()
        year_gan = year_gan.replace("Bg", "")
        year_zhi = year_zhi.replace("Bz", "")
        try:
            year_gan_idx = GAN.index(year_gan)
            year_zhi_idx = ZHI.index(year_zhi)
        except:
            offset = (lunar_year - 4) % 60
            year_gan_idx = offset % 10
            year_zhi_idx = offset % 12
            year_gan = GAN[year_gan_idx]
            year_zhi = ZHI[year_zhi_idx]

    # 時辰處理
    if hour == 23 or hour == 24: hour = 0
    time_idx = math.floor((hour + 1) / 2) % 12
    
    # 計算虛歲
    current_age = target_year - lunar_year + 1

    # 2. 安命身宮
    ming_idx = (2 + (lunar_month - 1) - time_idx + 12) % 12
    shen_idx = (2 + (lunar_month - 1) + time_idx) % 12
    
    # 3. 起五行局
    start_gan_idx = (year_gan_idx % 5) * 2 + 2 
    start_gan_idx = start_gan_idx % 10
    steps = (ming_idx - 2 + 12) % 12
    ming_gan_idx = (start_gan_idx + steps) % 10
    bureau_num = get_nayin_number(ming_gan_idx, ming_idx)
    bureau_name = BUREAU_NAMES[bureau_num]
    
    # 4. 安紫微星
    if lunar_day % bureau_num == 0:
        quotient = lunar_day // bureau_num
        ziwei_pos = (2 + quotient - 1) % 12
    else:
        remainder = lunar_day % bureau_num
        makeup = bureau_num - remainder
        quotient = (lunar_day + makeup) // bureau_num
        base_pos = (2 + quotient - 1) % 12
        if makeup % 2 == 1:
            ziwei_pos = (base_pos - makeup + 12) % 12
        else:
            ziwei_pos = (base_pos + makeup) % 12
            
    # 安天府
    tianfu_pos = (16 - ziwei_pos) % 12

    # --- 初始化星星容器 ---
    stars_map = {i: [] for i in range(12)}
    def add_star(name, idx, type='minor'):
        stars_map[idx % 12].append({'name': name, 'type': type})

    # 安十四主星
    z_seq = ['紫微','天機','','太陽','武曲','天同','','','廉貞']
    for i, s in enumerate(z_seq):
        if s: add_star(s, ziwei_pos - i, 'major')
        
    t_seq = ['天府','太陰','貪狼','巨門','天相','天梁','七殺','','','','破軍']
    for i, s in enumerate(t_seq):
        if s: add_star(s, tianfu_pos + i, 'major')

    # 5. 安輔星
    
    # 昌曲 (時)
    wc_pos = (10 - time_idx) % 12
    wq_pos = (4 + time_idx) % 12
    add_star('文昌', wc_pos, 'lucky')
    add_star('文曲', wq_pos, 'lucky')

    # 輔弼 (月)
    add_star('左輔', 4 + lunar_month - 1, 'lucky')
    add_star('右弼', 10 - lunar_month + 1, 'lucky')
    
    # 魁鉞 (年干)
    kui_yue = {'甲':(1,7),'乙':(0,8),'丙':(11,9),'丁':(11,9),'戊':(1,7),
               '己':(0,8),'庚':(1,7),'辛':(6,2),'壬':(3,5),'癸':(3,5)}
    if year_gan in kui_yue:
        k, y = kui_yue[year_gan]
        add_star('天魁', k, 'lucky')
        add_star('天鉞', y, 'lucky')
        
    # 祿存、羊陀 (年干)
    lucun = {'甲':2,'乙':3,'丙':5,'丁':6,'戊':5,'己':6,'庚':8,'辛':9,'壬':11,'癸':0}
    if year_gan in lucun:
        l_idx = lucun[year_gan]
        add_star('祿存', l_idx, 'lucky')
        add_star('擎羊', l_idx + 1, 'bad')
        add_star('陀羅', l_idx - 1, 'bad')

    # 天馬 (依月支計算)
    month_zhi_idx = (lunar_month + 1) % 12
    ma_map = {2:8, 6:8, 10:8, 8:2, 0:2, 4:2, 5:11, 9:11, 1:11, 11:5, 3:5, 7:5}
    tm_pos = ma_map.get(month_zhi_idx, (month_zhi_idx + 6) % 12)
    add_star('天馬', tm_pos, 'flower')

    # 空劫 (時)
    dj_pos = (11 + time_idx) % 12
    tk_pos = (11 - time_idx) % 12
    add_star('地劫', dj_pos, 'bad')
    add_star('天空', tk_pos, 'bad')

    # 火鈴 (年支 + 時)
    mod4 = year_zhi_idx % 4
    fire_start = {2:1, 0:2, 1:3, 3:9}
    bell_start = {2:3, 0:10, 1:10, 3:10}
    huo_pos = (fire_start[mod4] + time_idx) % 12
    ling_pos = (bell_start[mod4] + time_idx) % 12
    add_star('火星', huo_pos, 'bad')
    add_star('鈴星', ling_pos, 'bad')

    # 桃花星
    hong_idx = (3 - year_zhi_idx + 12) % 12
    add_star('紅鸞', hong_idx, 'flower')
    add_star('天喜', hong_idx + 6, 'flower')
    add_star('天姚', 1 + lunar_month - 1, 'flower')
    add_star('天刑', 9 + lunar_month - 1, 'bad')

    # 6. 大限運勢
    is_yang_gan = (year_gan_idx % 2 == 0)
    is_male = (gender == '男')
    is_clockwise = False
    if is_yang_gan and is_male: is_clockwise = True
    elif (not is_yang_gan) and (not is_male): is_clockwise = True
    
    # 7. 標籤計算 (流年/斗君)
    target_zhi_idx = (target_year - 4) % 12 
    doujun_idx = (target_zhi_idx - (lunar_month - 1) + time_idx + 12) % 12

    # 8. 組裝
    sihua_rules = SIHUA.get(year_gan, {})
    palaces = []
    
    for i in range(12):
        offset = (i - ming_idx + 12) % 12
        p_name_idx = (12 - offset) % 12 if offset != 0 else 0
        
        curr_gan_idx = (start_gan_idx + (i - 2 + 12) % 12) % 10
        curr_ganzhi = GAN[curr_gan_idx] + ZHI[i]
        
        dist_from_ming = (i - ming_idx + 12) % 12 if is_clockwise else (ming_idx - i + 12) % 12
        start_age = bureau_num + dist_from_ming * 10
        end_age = start_age + 9
        
        is_current_dayun = (current_age >= start_age and current_age <= end_age)
        is_current_liunian = (i == target_zhi_idx)
        is_current_doujun = (i == doujun_idx)

        final_stars = []
        for s in stars_map[i]:
            hua = sihua_rules.get(s['name'], '')
            final_stars.append({'name':s['name'], 'type':s['type'], 'hua':hua})

        palaces.append({
            "name": PALACES_NAMES[p_name_idx],
            "is_body": (i == shen_idx),
            "ganzhi": curr_ganzhi,
            "stars": final_stars,
            "daxian": f"{start_age}-{end_age}",
            "zhi": ZHI[i],
            "tags": {
                "dayun": is_current_dayun, 
                "liunian": is_current_liunian, 
                "doujun": is_current_doujun
            }
        })

    # 🔥🔥🔥 修復顯示文字邏輯 🔥🔥🔥
    if is_lunar:
        # 如果使用者輸入是農曆，就顯示轉換後的農曆日期
        date_str = f"農曆 {lunar_year}年 {lunar_month}月 {lunar_day}日"
    else:
        # 如果使用者輸入是國曆，就顯示原始輸入的國曆日期 (這裡直接拿 input year/month/day)
        date_str = f"國曆 {year}年 {month}月 {day}日"
    
    target_offset = (target_year - 4) % 60
    target_gan_char = GAN[target_offset % 10]
    target_zhi_char = ZHI[target_offset % 12]

    return {
        "lunar_str": f"{date_str} {ZHI[time_idx]}時", # 這裡的字串已經修正
        "bureau": bureau_name,
        "palaces": palaces,
        "age_info": f"流年 {target_year} ({target_gan_char}{target_zhi_char}年) 虛歲 {current_age}",
        "year_gan": year_gan,
        "year_zhi": year_zhi,
        "gender": gender
    }

def error_chart(msg):
    return {
        "lunar_str": msg, "bureau": "-", "age_info": "-",
        "year_gan": "-", "year_zhi": "-", "gender": "-",
        "palaces": [{"name": "-", "ganzhi": "-", "stars": [], "daxian": "-", "is_body": False} for _ in range(12)]
    }
