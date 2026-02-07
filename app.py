# app.py
from pathlib import Path

import streamlit as st
import streamlit_authenticator as stauth
from PIL import Image

from core import calc, STAT_CHOICES, STAT_MAP, SERIES_BONUS

# =========================
# キャラデータ（属性付き）
# =========================
RAW_CHARACTER_DATA = [
    ("心","秋山 駿",437,627,437,603),
    ("体","品田 辰雄",529,523,585,596),
    ("心","足立 宏一",473,603,468,591),
    ("技","寺田 行雄",621,511,511,573),
    ("心","澤村 遥",554,560,627,560),
    ("体","ソンヒ",689,437,456,554),
    ("技","ﾏｷﾑﾗ ﾏｺﾄ",523,523,708,548),
    ("心","趙 天佑",498,498,627,542),
    ("技","錦山 彰",646,431,431,535),
    ("技","ﾊﾝ・ｼﾞｭﾝｷﾞ",548,542,579,535),
    ("体","向田 紗栄子",542,529,689,535),
    ("技","タツ姐",696,437,462,529),
    ("体","小野 ミチオ",603,480,696,529),
    ("技","郷田 龍司",652,437,431,517),
    ("体","冴島 大河",517,511,646,517),
    ("心","西谷 誉",437,696,468,511),
    ("心","真島 吾朗",431,658,431,511),
    ("技","春日 一番",431,640,486,456),
    ("体","桐生 一馬",542,486,652,419),
    ("体","柏木 修",492,492,560,517),
    ("体","相沢 聖人",529,529,517,468),
    ("体","千石 虎之介",486,480,603,473),
    ("心","新藤 浩二",406,603,400,511),
    ("体","林 弘",560,437,450,554),
    ("体","谷村 正義",498,498,542,535),
    ("心","ｱﾝﾄﾞﾚ・ﾘﾁｬｰﾄﾞｿﾝ",504,511,529,529),
    ("心","星野 龍平",400,591,406,542),
    ("技","森永 悠",529,437,523,504),
    ("心","玉城 鉄生",480,486,603,480),
    ("心","荒瀬 和人",412,596,425,492),
    ("技","伊達 真",517,450,511,560),
    ("技","老鬼",591,406,406,548),
    ("心","渡瀬 勝",473,640,523,579),
    ("体","狭山 薫",683,431,462,560),
    ("技","桐生 一馬(龍0)",517,517,719,566),
    ("心","澤村 由美",554,554,671,554),
    ("技","世良 勝",548,437,456,579),
    ("技","田中 シンジ",412,596,406,523),
]

CHARACTER_DATA = {}
CHAR_ATTR = {}
for attr, name, s, i, v, a in RAW_CHARACTER_DATA:
    CHARACTER_DATA[name] = {"str": s, "int": i, "vit": v, "agi": a}
    CHAR_ATTR[name] = attr

EMPTY_CHAR = "-"

BASE_DIR = Path(__file__).resolve().parent
IMG_DIR = BASE_DIR / "images"

# =========================
# 認証（Streamlit Community Cloud の Secrets から読む）
# =========================
def require_login():
    users = st.secrets["auth"]["users"]  # dict: username -> hashed_password
    cookie_name = st.secrets["auth"]["cookie_name"]
    cookie_key = st.secrets["auth"]["cookie_key"]
    cookie_exp_days = int(st.secrets["auth"]["cookie_exp_days"])

    credentials = {"usernames": {}}
    for u, hashed_pw in users.items():
        credentials["usernames"][u] = {"name": u, "password": hashed_pw}

    authenticator = stauth.Authenticate(
        credentials=credentials,
        cookie_name=cookie_name,
        cookie_key=cookie_key,
        cookie_expiry_days=cookie_exp_days,
    )

    _, status, _ = authenticator.login("ログイン", "main")

    if status is False:
        st.error("ユーザー名またはパスワードが違います。")
        st.stop()
    if status is None:
        st.info("ログインしてください。")
        st.stop()

    authenticator.logout("ログアウト", "sidebar")

# =========================
# 画像（ファイル名がキャラ名完全一致前提）
# =========================
def find_image_path(name: str):
    for ext in (".png", ".jpg", ".jpeg", ".webp", ".gif"):
        p = IMG_DIR / f"{name}{ext}"
        if p.exists():
            return p
    return None

def filtered_names(attr_filter: str, query: str):
    names = [
        n for n in CHARACTER_DATA.keys()
        if attr_filter == "すべて" or CHAR_ATTR[n] == attr_filter
    ]
    names.sort()
    if query:
        names = [n for n in names if query in n]
    return names

# =========================
# UI
# =========================
st.set_page_config(page_title="ステータス計算ツール", layout="wide")

# まずログイン必須
require_login()

st.title("ステータス計算ツール（身内限定）")

with st.sidebar:
    attr_filter = st.selectbox("編成の属性", ["すべて", "心", "技", "体"])
    search = st.text_input("キャラ検索（部分一致）", "")
    layout_mode = st.radio("表示レイアウト", ["縦（スマホ向け）", "横3列（PC向け）"], index=0)

names = [EMPTY_CHAR] + filtered_names(attr_filter, search)

def person_block(i: int):
    st.subheader(f"{i+1}人目")

    name = st.selectbox("キャラ", names, key=f"name_{i}")

    left, right = st.columns(2)
    with left:
        limit = st.selectbox("凸数", list(range(6)), index=0, key=f"limit_{i}")
        trait = st.selectbox("特性", STAT_CHOICES, index=0, key=f"trait_{i}")
        j1 = st.selectbox("宝飾①", STAT_CHOICES, index=0, key=f"j1_{i}")
        j2 = st.selectbox("宝飾②", STAT_CHOICES, index=0, key=f"j2_{i}")

    with right:
        head = st.selectbox("頭 (SSR Lv.60固定)", list(SERIES_BONUS.keys()), index=0, key=f"head_{i}")
        body = st.selectbox("胴 (SSR Lv.60固定)", list(SERIES_BONUS.keys()), index=0, key=f"body_{i}")
        legs = st.selectbox("足 (SSR Lv.60固定)", list(SERIES_BONUS.keys()), index=0, key=f"legs_{i}")

    # 画像表示
    if name != EMPTY_CHAR:
        img_path = find_image_path(name)
        if img_path:
            st.image(Image.open(img_path), caption=name, use_container_width=True)
        else:
            st.warning("画像が見つかりません（images/ にファイルがあるか確認）")

    return name, limit, trait, j1, j2, head, body, legs

# 入力UI（縦 or 横）
if layout_mode.startswith("縦"):
    p0 = person_block(0)
    st.divider()
    p1 = person_block(1)
    st.divider()
    p2 = person_block(2)
else:
    c1, c2, c3 = st.columns(3)
    with c1:
        p0 = person_block(0)
    with c2:
        p1 = person_block(1)
    with c3:
        p2 = person_block(2)

# 計算
if st.button("計算", type="primary", use_container_width=True):
    for i, p in enumerate([p0, p1, p2]):
        name, limit, trait, j1, j2, head, body, legs = p

        st.markdown("---")
        st.write(f"**{i+1}人目**")

        if name == EMPTY_CHAR:
            st.info("未選択")
            continue

        s = calc(
            CHARACTER_DATA,
            name,
            int(limit),
            STAT_MAP[trait],
            STAT_MAP[j1],
            STAT_MAP[j2],
            head, body, legs
        )

        st.success(f"{name} の結果")
        st.write({"筋力": s["str"], "知性": s["int"], "根性": s["vit"], "素早さ": s["agi"]})
