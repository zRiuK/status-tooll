import os
import math
import unicodedata
from typing import Dict, List, Tuple, Optional

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

# 図鑑順ソート用
ZUKAN_IDX = {name: idx for idx, (_, name, *_rest) in enumerate(RAW_CHARACTER_DATA)}

# データ整形
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
# 画像関連
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
    # 念のため「そのままの名前+拡張子」も探す
    for ext in (".png", ".gif", ".jpg", ".jpeg", ".webp"):
        p2 = os.path.join(IMG_DIR, f"{name}{ext}")
        if os.path.exists(p2):
            return p2
    return None

# =========================
# 計算（あなたのロジックを維持）
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

    # 最後に速度(agi)へ倍率（最終値に対して）
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
# UI
# =========================

st.set_page_config(page_title="ステータス計算ツール", layout="wide")
st.title("ステータス計算ツール（Streamlit版）")

# 上部：属性フィルタ
attr = st.selectbox("編成の属性", ["すべて", "心", "技", "体"], index=0)

def get_filtered_names(attr_value: str) -> List[str]:
    names = [n for n in CHARACTER_DATA.keys() if attr_value == "すべて" or CHAR_ATTR[n] == attr_value]
    names.sort(key=lambda n: ZUKAN_IDX.get(n, 999999))
    return names

all_names = get_filtered_names(attr)
values = [EMPTY_CHAR] + all_names

st.caption("※ 画像は images/ フォルダに置いたファイル名（拡張子除く）とキャラ名が一致すると自動表示します。")

# 3人ブロックを横並び
cols = st.columns(3, gap="large")

def block_ui(i: int, col):
    with col:
        st.subheader(f"{i+1}人目")

        # セッションキー（Streamlitは毎回再実行されるので state を使う）
        k_char = f"char_{i}"
        k_q = f"q_{i}"
        k_limit = f"limit_{i}"
        k_trait = f"trait_{i}"
        k_j1 = f"j1_{i}"
        k_j2 = f"j2_{i}"
        k_dash1 = f"dash1_{i}"
        k_dash2 = f"dash2_{i}"
        k_head = f"head_{i}"
        k_body = f"body_{i}"
        k_legs = f"legs_{i}"
        k_ambush = f"ambush_{i}"
        k_mastery = f"mastery_{i}"

        # 初期値（未設定なら）
        st.session_state.setdefault(k_char, EMPTY_CHAR)
        st.session_state.setdefault(k_q, "")
        st.session_state.setdefault(k_limit, 0)
        st.session_state.setdefault(k_trait, "なし")
        st.session_state.setdefault(k_j1, "なし")
        st.session_state.setdefault(k_j2, "なし")
        st.session_state.setdefault(k_dash1, False)
        st.session_state.setdefault(k_dash2, False)
        st.session_state.setdefault(k_head, "なし")
        st.session_state.setdefault(k_body, "なし")
        st.session_state.setdefault(k_legs, "なし")
        st.session_state.setdefault(k_ambush, False)
        st.session_state.setdefault(k_mastery, False)

        # 検索（名前の絞り込み）
        q = st.text_input("キャラ検索（部分一致）", key=k_q, placeholder="例：桐生 / 真島 など")
        filtered = values
        if q.strip():
            filtered = [EMPTY_CHAR] + [n for n in all_names if q.strip() in n]

        # キャラ選択
        st.selectbox("キャラ（選択）", filtered, key=k_char)

        # 画像表示
        sel = st.session_state[k_char]
        img_path = find_image_path(sel)
        if img_path:
            try:
                img = Image.open(img_path)
                st.image(img, caption=sel, use_container_width=True)
            except Exception:
                st.warning("画像は見つかったけど読み込みに失敗しました。形式を確認してください。")

        # 画像から選ぶ（グリッド）
        with st.expander("画像から選ぶ（クリックで選択）", expanded=False):
            q2 = st.text_input("ここでも検索", key=f"gridq_{i}", placeholder="例：春日")
            names_for_grid = all_names
            if q2.strip():
                names_for_grid = [n for n in names_for_grid if q2.strip() in n]

            grid_cols = st.columns(4)
            cidx = 0
            for name in names_for_grid:
                p = find_image_path(name)
                with grid_cols[cidx]:
                    if p:
                        try:
                            st.image(Image.open(p), caption="", use_container_width=True)
                        except Exception:
                            st.write("(画像読込失敗)")
                    # 画像がなくても選べるようにする
                    if st.button(name, key=f"pick_{i}_{name}", use_container_width=True):
                        st.session_state[k_char] = name
                        st.rerun()
                cidx = (cidx + 1) % 4

            if st.button("(未選択) -", key=f"pick_{i}_empty", use_container_width=True):
                st.session_state[k_char] = EMPTY_CHAR
                st.rerun()

        # ステータス設定
        st.selectbox("凸数", list(range(6)), key=k_limit)
        st.selectbox("特性", STAT_CHOICES, key=k_trait)

        # 宝飾① + 100mダッシュ
        st.markdown("**宝飾①**")
        j1c1, j1c2 = st.columns([2, 1])
        with j1c1:
            st.selectbox("宝飾① 効果", STAT_CHOICES, key=k_j1, label_visibility="collapsed")
        with j1c2:
            st.checkbox("100mダッシュ", key=k_dash1)

        # 宝飾② + 100mダッシュ
        st.markdown("**宝飾②**")
        j2c1, j2c2 = st.columns([2, 1])
        with j2c1:
            st.selectbox("宝飾② 効果", STAT_CHOICES, key=k_j2, label_visibility="collapsed")
        with j2c2:
            st.checkbox("100mダッシュ", key=k_dash2)

        # 装備
        st.markdown("**頭 (SSR Lv.60固定)**")
        st.selectbox("頭シリーズ", list(SERIES_BONUS.keys()), key=k_head, label_visibility="collapsed")
        st.markdown("**胴 (SSR Lv.60固定)**")
        st.selectbox("胴シリーズ", list(SERIES_BONUS.keys()), key=k_body, label_visibility="collapsed")
        st.markdown("**足 (SSR Lv.60固定)**")
        st.selectbox("足シリーズ", list(SERIES_BONUS.keys()), key=k_legs, label_visibility="collapsed")

        # 追加チェック
        st.checkbox("アンブッシュ（速度+15%）", key=k_ambush)
        st.checkbox("習熟の道（速度+12%）", key=k_mastery)

        return {
            "char": k_char,
            "limit": k_limit,
            "trait": k_trait,
            "j1": k_j1,
            "j2": k_j2,
            "head": k_head,
            "body": k_body,
            "legs": k_legs,
            "dash1": k_dash1,
            "dash2": k_dash2,
            "ambush": k_ambush,
            "mastery": k_mastery,
        }

keys = []
for i in range(3):
    keys.append(block_ui(i, cols[i]))

st.divider()

# 計算ボタン（全員分）
if st.button("計算", type="primary", use_container_width=True):
    out_cols = st.columns(3, gap="large")
    for i, k in enumerate(keys):
        with out_cols[i]:
            name = st.session_state[k["char"]]
            if not name or name == EMPTY_CHAR:
                st.info("未選択")
                continue
            if name not in CHARACTER_DATA:
                st.error("キャラが不正です")
                continue

            s = calc(
                name=name,
                limit=int(st.session_state[k["limit"]]),
                trait=STAT_MAP[st.session_state[k["trait"]]],
                j1=STAT_MAP[st.session_state[k["j1"]]],
                j2=STAT_MAP[st.session_state[k["j2"]]],
                head=st.session_state[k["head"]],
                body=st.session_state[k["body"]],
                legs=st.session_state[k["legs"]],
                dash1=bool(st.session_state[k["dash1"]]),
                dash2=bool(st.session_state[k["dash2"]]),
                ambush=bool(st.session_state[k["ambush"]]),
                mastery=bool(st.session_state[k["mastery"]]),
            )

            st.success(f"{name}")
            st.write(f"筋力: {s['str']}")
            st.write(f"知性: {s['int']}")
            st.write(f"根性: {s['vit']}")
            st.write(f"素早さ: {s['agi']}")
