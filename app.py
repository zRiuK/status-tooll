import os
import math
import unicodedata
from typing import Dict, List, Optional

import streamlit as st
from PIL import Image

# =========================
# キャラデータ（あなたのをそのまま）
# =========================

RAW_CHARACTER_DATA = [
    ("体","桐生 一馬",542,486,652,419),
    ("技","春日 一番",431,640,486,456),
    ("技","錦山 彰",646,431,431,535),
    ("心","真島 吾朗",431,658,431,511),
    ("体","冴島 大河",517,511,646,517),
    ("心","秋山 駿",437,627,437,603),
    ("体","品田 辰雄",529,523,585,596),
    ("技","郷田 龍司",652,437,431,517),
    ("技","ﾊﾝ・ｼﾞｭﾝｷﾞ",548,542,579,535),
    ("心","趙 天佑",498,498,627,542),
    ("心","足立 宏一",473,603,468,591),
    ("体","ソンヒ",689,437,456,554),
    ("技","ﾏｷﾑﾗ ﾏｺﾄ",523,523,708,548),
    ("心","西谷 誉",437,696,468,511),
    ("体","向田 紗栄子",542,529,689,535),
    ("技","寺田 行雄",621,511,511,573),
    ("心","澤村 遥",554,560,627,560),
    ("体","小野 ミチオ",603,480,696,529),
    ("技","タツ姐",696,437,462,529),
    ("心","渡瀬 勝",473,640,523,579),
    ("体","狭山 薫",683,431,462,560),
    ("技","桐生 一馬(龍0)",517,517,719,566),
    ("心","澤村 由美",554,554,671,554),
    ("技","伊達 真",517,450,511,560),
    ("体","柏木 修",492,492,560,517),
    ("技","老鬼",591,406,406,548),
    ("心","ｱﾝﾄﾞﾚ・ﾘﾁｬｰﾄﾞｿﾝ",504,511,529,529),
    ("技","世良 勝",548,437,456,579),
    ("体","相沢 聖人",529,529,517,468),
    ("体","千石 虎之介",486,480,603,473),
    ("技","田中 シンジ",412,596,406,523),
    ("技","森永 悠",529,437,523,504),
    ("心","新藤 浩二",406,603,400,511),
    ("体","林 弘",560,437,450,554),
    ("体","谷村 正義",498,498,542,535),
    ("心","星野 龍平",400,591,406,542),
    ("心","玉城 鉄生",480,486,603,480),
    ("心","荒瀬 和人",412,596,425,492),
]

ZUKAN_IDX = {name: idx for idx, (_, name, *_rest) in enumerate(RAW_CHARACTER_DATA)}

CHARACTER_DATA: Dict[str, Dict[str, int]] = {}
CHAR_ATTR: Dict[str, str] = {}
for attr, name, s, i, v, a in RAW_CHARACTER_DATA:
    CHARACTER_DATA[name] = {"str": s, "int": i, "vit": v, "agi": a}
    CHAR_ATTR[name] = attr

STAT_KEYS = ["str", "int", "vit", "agi"]
STAT_CHOICES = ["なし", "筋力", "知性", "根性", "素早さ"]
STAT_MAP = {"なし": None, "筋力": "str", "知性": "int", "根性": "vit", "素早さ": "agi"}

SERIES_BONUS = {
    "なし": {},
    "サイバー": {"str": 40},
    "司祭": {"int": 40},
    "浪漫": {"vit": 55},
    "ロマン": {"agi": 40},
}
EQUIP_BASE = {"head": {"int": 80}, "body": {"vit": 110}, "legs": {"str": 80}}

EMPTY_CHAR = "-"

# =========================
# 画像関連（軽量化：選択中の1枚だけ読む）
# =========================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, "images")

def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("\u3000", " ")
    s = s.strip()
    s = " ".join(s.split())
    return s

@st.cache_data(show_spinner=False)
def build_image_index() -> Dict[str, str]:
    idx: Dict[str, str] = {}
    if not os.path.isdir(IMG_DIR):
        return idx
    for fn in os.listdir(IMG_DIR):
        base, ext = os.path.splitext(fn)
        ext_l = ext.lower()
        if ext_l not in (".png", ".gif", ".jpg", ".jpeg", ".webp"):
            continue
        idx[norm(base)] = os.path.join(IMG_DIR, fn)
    return idx

IMAGE_INDEX = build_image_index()

def find_image_path(name: str) -> Optional[str]:
    if not name or name == EMPTY_CHAR:
        return None
    key = norm(name)
    p = IMAGE_INDEX.get(key)
    if p and os.path.exists(p):
        return p
    for ext in (".png", ".gif", ".jpg", ".jpeg", ".webp"):
        p2 = os.path.join(IMG_DIR, f"{name}{ext}")
        if os.path.exists(p2):
            return p2
    return None

@st.cache_data(show_spinner=False)
def load_image_for_display(path: str, max_w: int = 420) -> Image.Image:
    """表示用に軽くリサイズして返す（元画像がデカいと重いので）"""
    img = Image.open(path)
    # アスペクト比を維持して縮小
    if img.width > max_w:
        ratio = max_w / float(img.width)
        new_h = int(img.height * ratio)
        img = img.resize((max_w, new_h))
    return img

# =========================
# 計算（あなたのロジック維持）
# =========================

def calc(name, limit, trait, j1, j2, head, body, legs,
         dash1: bool, dash2: bool, ambush: bool, mastery: bool):
    base = CHARACTER_DATA[name]
    percent = {k: 0.0 for k in STAT_KEYS}

    for k in ["str", "int", "vit"]:
        percent[k] += limit * 0.05

    for p in [trait, j1, j2]:
        if p:
            percent[p] += 0.07

    stats = {k: math.ceil(base[k] * (1 + percent[k])) for k in STAT_KEYS}

    equips = {"head": head, "body": body, "legs": legs}
    for part, series in equips.items():
        if series != "なし":
            for k, v in EQUIP_BASE[part].items():
                stats[k] += v
            for k, v in SERIES_BONUS[series].items():
                stats[k] += v

    agi_mul = 1.0
    if dash1:
        agi_mul *= 1.15
    if dash2:
        agi_mul *= 1.15
    if ambush:
        agi_mul *= 1.15
    if mastery:
        agi_mul *= 1.12

    stats["agi"] = math.ceil(stats["agi"] * agi_mul)
    return stats

# =========================
# UI（1人だけ）
# =========================

st.set_page_config(page_title="ステータス計算ツール", layout="centered")
st.title("ステータス計算ツール（軽量・1人版）")

attr = st.selectbox("編成の属性", ["すべて", "心", "技", "体"], index=0)

def get_filtered_names(attr_value: str) -> List[str]:
    names = [n for n in CHARACTER_DATA.keys() if attr_value == "すべて" or CHAR_ATTR[n] == attr_value]
    names.sort(key=lambda n: ZUKAN_IDX.get(n, 999999))
    return names

all_names = get_filtered_names(attr)

st.session_state.setdefault("char", EMPTY_CHAR)

# 検索（selectboxの候補を絞るだけ。重い画像グリッドは別にする）
q = st.text_input("キャラ検索（部分一致）", placeholder="例：桐生 / 真島 / 春日 ...")
if q.strip():
    filtered = [EMPTY_CHAR] + [n for n in all_names if q.strip() in n]
else:
    filtered = [EMPTY_CHAR] + all_names

st.selectbox("キャラ（選択）", filtered, key="char")

# 選択画像（1枚だけ読み込み＆縮小して表示）
sel = st.session_state["char"]
img_path = find_image_path(sel)
if img_path:
    try:
        st.image(load_image_for_display(img_path), caption=sel, use_container_width=True)
    except Exception:
        st.warning("画像の読み込みに失敗しました。形式や破損を確認してください。")

# 任意：画像から選ぶ（軽量化：ページング＆表示枚数制限）
with st.expander("画像から選ぶ（必要なときだけ開く）", expanded=False):
    st.caption("※ ここを開くと画像を読み込むので、重い場合は使わず上の検索で選ぶのが最速です。")
    q2 = st.text_input("この中でさらに検索", key="grid_q", placeholder="例：桐生")
    names_for_grid = all_names
    if q2.strip():
        names_for_grid = [n for n in names_for_grid if q2.strip() in n]

    page_size = st.slider("1ページの表示数", 8, 40, 16, step=4)
    total = len(names_for_grid)
    pages = max(1, (total + page_size - 1) // page_size)
    page = st.number_input("ページ", min_value=1, max_value=pages, value=1, step=1)

    start = (page - 1) * page_size
    end = min(total, start + page_size)
    slice_names = names_for_grid[start:end]

    gcols = st.columns(4)
    ci = 0
    for name in slice_names:
        with gcols[ci]:
            p = find_image_path(name)
            if p:
                try:
                    st.image(load_image_for_display(p, max_w=240), use_container_width=True)
                except Exception:
                    st.write("(画像読込失敗)")
            if st.button(name, key=f"pick_{name}", use_container_width=True):
                st.session_state["char"] = name
                st.rerun()
        ci = (ci + 1) % 4

    if st.button("(未選択) -", use_container_width=True):
        st.session_state["char"] = EMPTY_CHAR
        st.rerun()

st.divider()

# 入力
limit = st.selectbox("凸数", list(range(6)), index=0)
trait = st.selectbox("特性", STAT_CHOICES, index=0)

st.markdown("**宝飾①**")
j1c1, j1c2 = st.columns([2, 1])
with j1c1:
    j1 = st.selectbox("宝飾① 効果", STAT_CHOICES, index=0, label_visibility="collapsed")
with j1c2:
    dash1 = st.checkbox("100mダッシュ", value=False, key="dash1")

st.markdown("**宝飾②**")
j2c1, j2c2 = st.columns([2, 1])
with j2c1:
    j2 = st.selectbox("宝飾② 効果", STAT_CHOICES, index=0, label_visibility="collapsed")
with j2c2:
    dash2 = st.checkbox("100mダッシュ", value=False, key="dash2")

st.markdown("**頭 (SSR Lv.60固定)**")
head = st.selectbox("頭シリーズ", list(SERIES_BONUS.keys()), index=0, label_visibility="collapsed")
st.markdown("**胴 (SSR Lv.60固定)**")
body = st.selectbox("胴シリーズ", list(SERIES_BONUS.keys()), index=0, label_visibility="collapsed")
st.markdown("**足 (SSR Lv.60固定)**")
legs = st.selectbox("足シリーズ", list(SERIES_BONUS.keys()), index=0, label_visibility="collapsed")

ambush = st.checkbox("アンブッシュ（速度+15%）", value=False, key="ambush")
mastery = st.checkbox("習熟の道（速度+12%）", value=False, key="mastery")

# 計算
if st.button("計算", type="primary", use_container_width=True):
    name = st.session_state["char"]
    if not name or name == EMPTY_CHAR:
        st.info("キャラが未選択です")
    elif name not in CHARACTER_DATA:
        st.error("キャラが不正です")
    else:
        s = calc(
            name=name,
            limit=int(limit),
            trait=STAT_MAP[trait],
            j1=STAT_MAP[j1],
            j2=STAT_MAP[j2],
            head=head,
            body=body,
            legs=legs,
            dash1=bool(dash1),
            dash2=bool(dash2),
            ambush=bool(ambush),
            mastery=bool(mastery),
        )
        st.success(name)
        st.write(f"筋力: {s['str']}")
        st.write(f"知性: {s['int']}")
        st.write(f"根性: {s['vit']}")
        st.write(f"素早さ: {s['agi']}")
