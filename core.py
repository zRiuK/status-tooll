# core.py
import math

STAT_KEYS = ["str", "int", "vit", "agi"]
STAT_CHOICES = ["なし", "筋力", "知性", "根性", "素早さ"]
STAT_MAP = {"なし": None, "筋力": "str", "知性": "int", "根性": "vit", "素早さ": "agi"}

SERIES_BONUS = {
    "なし": {},
    "サイバー(筋力)": {"str": 40},
    "司祭(知性)": {"int": 40},
    "浪漫(根性)": {"vit": 55},
    "ロマン(素早さ)": {"agi": 40},
}
EQUIP_BASE = {"head": {"int": 80}, "body": {"vit": 110}, "legs": {"str": 80}}

def calc(character_data, name, limit, trait, j1, j2, head, body, legs):
    base = character_data[name]
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

    return stats
