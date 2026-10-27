#!/usr/bin/env python3
"""把 PokeAPI 的 CSV 数据与游戏内的精灵图合成为站点内容文件。

用法：
    python3 site/tools/import_pokeapi.py <csv目录> <精灵图目录>

csv 目录需包含 PokeAPI data/v2/csv 下的 pokemon、pokemon_species、
pokemon_stats、pokemon_types、pokemon_abilities、pokemon_species_names、
pokemon_species_flavor_text、pokemon_evolution、type_names、type_efficacy、
moves、move_names、abilities、ability_names、items、item_names、item_categories。
"""
import csv
import json
import os
import re
import shutil
import sys

ZH = "12"
EN = "9"

TYPE_COLORS = {
    "normal": "#9aa4b2", "fire": "#ff5c4d", "water": "#3ea6ff", "electric": "#ffc400",
    "grass": "#35c96a", "ice": "#4fd8e8", "fighting": "#e04a5f", "poison": "#b565e0",
    "ground": "#d99a2b", "flying": "#8fb8ff", "psychic": "#ff5fa2", "bug": "#8fd14f",
    "rock": "#c9a227", "ghost": "#7a6bd8", "dragon": "#5a6cff", "dark": "#5b5f78",
    "steel": "#7f98b3", "fairy": "#ff8fd0",
}

STAT_KEYS = {"1": "hp", "2": "atk", "3": "def", "4": "spa", "5": "spd", "6": "spe"}

DAMAGE_CLASS = {"1": "变化", "2": "物理", "3": "特殊"}

ITEM_CATS = {
    "standard-balls": "精灵球", "special-balls": "特殊球", "apricorn-balls": "球果球",
    "medicine": "药品", "status-cures": "状态回复", "healing": "回复", "revival": "复活",
    "pp-recovery": "PP 回复", "vitamins": "营养饮料", "effort-training": "努力值道具",
    "evolution": "进化道具", "plates": "属性石板", "memories": "记忆碟",
    "mega-stones": "超级石", "z-crystals": "Z 纯晶", "held-items": "携带道具",
    "choice": "讲究类", "type-enhancement": "属性强化", "type-protection": "属性保护",
    "species-specific": "专属道具", "training": "训练道具", "loot": "战利品",
    "collectibles": "收藏品", "mulch": "堆肥", "flutes": "笛子", "scarves": "围巾",
    "jewels": "宝石", "all-machines": "招式学习器", "tm-materials": "学习器材料",
    "curry-ingredients": "咖喱材料", "sandwich-ingredients": "三明治材料",
    "picnic": "野餐", "dynamax-crystals": "极巨结晶", "nature-mints": "性格薄荷",
    "tera-shard": "太晶碎块", "gameplay": "重要道具", "plot-advancement": "剧情道具",
    "event-items": "活动道具", "dex-completion": "图鉴完成", "baking-only": "料理",
    "in-a-pinch": "危机时", "picky-healing": "偏食回复", "bad-held-items": "负面道具",
    "stat-boosts": "能力提升", "effort-drop": "努力值下降", "other": "其他",
    "species-candies": "宝可梦糖果", "catching-bonus": "捕获辅助",
    "all-mail": "邮件", "apricorn-box": "球果盒", "data-cards": "数据卡",
    "miracle-shooter": "奇迹发射器", "spelunking": "探险道具", "unused": "未使用",
}

EGG_GROUP_ZH = {
    "monster": "怪兽", "water1": "水中1", "bug": "虫", "flying": "飞行",
    "field": "陆上", "ground": "陆上", "fairy": "妖精", "grass": "植物",
    "plant": "植物", "human-like": "人形", "humanshape": "人形",
    "water3": "水中3", "mineral": "矿物", "amorphous": "不定形",
    "indeterminate": "不定形", "water2": "水中2", "ditto": "百变怪",
    "dragon": "龙", "undiscovered": "未发现", "no-eggs": "未发现",
}

TRIGGER_TEXT = {
    "1": "等级提升", "2": "通讯交换", "3": "使用道具",
    "4": "特殊条件", "5": "特殊条件", "6": "特殊条件", "7": "特殊条件", "8": "特殊条件",
}


def read(name, base):
    path = os.path.join(base, name + ".csv")
    if not os.path.exists(path):
        print("缺少 %s，跳过" % path)
        return []
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def norm(s):
    return re.sub(r"[^A-Za-z0-9]", "", s).upper()


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    csvdir, spritedir = sys.argv[1], sys.argv[2]
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    content = os.path.join(root, "content")
    sprites_out = os.path.join(root, "static", "sprites")
    os.makedirs(content, exist_ok=True)
    os.makedirs(sprites_out, exist_ok=True)

    type_zh = {r["type_id"]: r["name"] for r in read("type_names", csvdir) if r["local_language_id"] == ZH}
    type_en = {r["type_id"]: r["name"] for r in read("type_names", csvdir) if r["local_language_id"] == EN}
    species_zh = {r["pokemon_species_id"]: r["name"] for r in read("pokemon_species_names", csvdir) if r["local_language_id"] == ZH}
    species_en = {r["pokemon_species_id"]: r["name"] for r in read("pokemon_species_names", csvdir) if r["local_language_id"] == EN}
    genus = {r["pokemon_species_id"]: r["genus"] for r in read("pokemon_species_names", csvdir)
             if r["local_language_id"] == ZH and r.get("genus")}
    ability_zh = {r["ability_id"]: r["name"] for r in read("ability_names", csvdir) if r["local_language_id"] == ZH}
    ability_en = {r["ability_id"]: r["name"] for r in read("ability_names", csvdir) if r["local_language_id"] == EN}
    move_zh = {r["move_id"]: r["name"] for r in read("move_names", csvdir) if r["local_language_id"] == ZH}
    move_en = {r["move_id"]: r["name"] for r in read("move_names", csvdir) if r["local_language_id"] == EN}
    item_zh = {r["item_id"]: r["name"] for r in read("item_names", csvdir) if r["local_language_id"] == ZH}
    item_en = {r["item_id"]: r["name"] for r in read("item_names", csvdir) if r["local_language_id"] == EN}
    cat_name = {r["id"]: ITEM_CATS.get(r["identifier"], r["identifier"]) for r in read("item_categories", csvdir)}

    sprite_files = {}
    if os.path.isdir(spritedir):
        for f in os.listdir(spritedir):
            if not f.lower().endswith(".png"):
                continue
            base = f.rsplit(".", 1)[0]
            if re.search(r"_(female|gmax|gf|\d+)$", base):
                continue
            sprite_files.setdefault(norm(base), f)
    print("精灵图索引:", len(sprite_files))

    special_sprite = {"nidorina": "NIDORANfE", "nidorino": "NIDORANmA",
                      "nidoran-f": "NIDORANF", "nidoran-m": "NIDORANM"}

    flavor = {}
    for r in read("pokemon_species_flavor_text", csvdir):
        if r["language_id"] != ZH:
            continue
        text = r["flavor_text"].replace("\n", "").replace("\f", "").replace("\u3000", " ")
        flavor.setdefault(r["species_id"], text)

    evo_by_target = {}
    for r in read("pokemon_evolution", csvdir):
        evo_by_target.setdefault(r["evolved_species_id"], r)

    def evo_method(species_id):
        r = evo_by_target.get(species_id)
        if not r:
            return ""
        bits = []
        if r.get("minimum_level"):
            bits.append("等级 %s" % r["minimum_level"])
        if r.get("trigger_item_id"):
            bits.append("使用 %s" % item_zh.get(r["trigger_item_id"], "道具"))
        if r.get("evolution_trigger_id") == "2":
            bits.append("通讯交换")
        if r.get("minimum_happiness"):
            bits.append("亲密度")
        if r.get("time_of_day"):
            bits.append({"day": "白天", "night": "夜晚", "dusk": "黄昏"}.get(r["time_of_day"], r["time_of_day"]))
        if r.get("known_move_id"):
            bits.append("学会特定招式")
        if r.get("location_id"):
            bits.append("在特定地点")
        if r.get("relative_physical_stats"):
            bits.append("攻击／防御比较")
        if not bits and r.get("evolution_trigger_id"):
            bits.append(TRIGGER_TEXT.get(r["evolution_trigger_id"], "特殊条件"))
        return " · ".join(bits)

    species_rows = {r["id"]: r for r in read("pokemon_species", csvdir)}
    pokemon_rows = [r for r in read("pokemon", csvdir) if r.get("is_default") == "1"]

    stats = {}
    for r in read("pokemon_stats", csvdir):
        stats.setdefault(r["pokemon_id"], {})[STAT_KEYS[r["stat_id"]]] = int(r["base_stat"])

    types, slots = {}, {}
    for r in read("pokemon_types", csvdir):
        types.setdefault(r["pokemon_id"], []).append(type_zh.get(r["type_id"], "一般"))
        slots.setdefault(r["pokemon_id"], []).append(int(r["slot"]))
    for pid in types:
        types[pid] = [t for _, t in sorted(zip(slots[pid], types[pid]))]

    abilities, hidden = {}, {}
    for r in read("pokemon_abilities", csvdir):
        name = ability_zh.get(r["ability_id"])
        if not name:
            continue
        (hidden if r["is_hidden"] == "1" else abilities).setdefault(r["pokemon_id"], []).append(name)

    egg_of = {}
    for r in read("pokemon_egg_groups", csvdir):
        egg_of.setdefault(r["species_id"], []).append(r["egg_group_id"])
    egg_names = {r["id"]: EGG_GROUP_ZH.get(r["identifier"], r["identifier"]) for r in read("egg_groups", csvdir)}

    # 可学招式：优先现代版本组，缺省回退到该宝可梦出现的最新版本组
    LEARN_VG = {"25", "20", "17", "16"}
    level_moves, machine_moves, seen_vg = {}, {}, {}
    for r in read("pokemon_moves", csvdir):
        pid, vg, method = r["pokemon_id"], r["version_group_id"], r["pokemon_move_method_id"]
        if vg not in LEARN_VG:
            continue
        if seen_vg.get(pid) and seen_vg[pid] != vg:
            continue
        seen_vg[pid] = vg
        name = move_zh.get(r["move_id"])
        if not name:
            continue
        if method == "1":
            lv = int(r["level"] or 0)
            bucket = level_moves.setdefault(pid, {})
            if lv not in bucket:
                bucket[lv] = name
        elif method == "4":
            lst = machine_moves.setdefault(pid, [])
            if name not in lst:
                lst.append(name)

    children = {}
    for sid, r in species_rows.items():
        if r.get("evolves_from_species_id"):
            children.setdefault(r["evolves_from_species_id"], []).append(sid)

    def chain_of(sid):
        path, cur, guard = [], sid, 0
        while cur and guard < 10:
            path.append(cur)
            cur = species_rows.get(cur, {}).get("evolves_from_species_id") or ""
            guard += 1
        path.reverse()
        for child in sorted(children.get(sid, []), key=lambda x: int(x))[:9]:
            path.append(child)
        return path

    pokemon, copied = [], 0
    for row in pokemon_rows:
        sid = row["species_id"]
        if sid not in species_rows:
            continue
        pid = int(row["id"])
        identifier = species_rows[sid]["identifier"]
        # 立绘由 site/tools/fetch_sprites.py 下载；这里只声明路径，不复制原始资源
        sprite = ""
        if os.path.exists(os.path.join(sprites_out, "%d.png" % pid)):
            sprite = "sprites/%d.png" % pid
            copied += 1

        gender_rate = int(species_rows[sid]["gender_rate"] or "-1")
        if gender_rate < 0:
            gender = "无性别"
        elif gender_rate == 8:
            gender = "仅雌性"
        elif gender_rate == 0:
            gender = "仅雄性"
        else:
            gender = "%d:1" % (8 - gender_rate)

        has_evo = bool(children.get(sid) or species_rows[sid].get("evolves_from_species_id"))
        pokemon.append({
            "id": pid,
            "name": species_zh.get(sid) or species_en.get(sid) or row["identifier"],
            "en": species_en.get(sid) or row["identifier"].title(),
            "identifier": identifier,
            "types": types.get(row["id"], []),
            "generation": int(species_rows[sid]["generation_id"]),
            "category": genus.get(sid, ""),
            "abilities": abilities.get(row["id"], []),
            "hiddenAbilities": hidden.get(row["id"], []),
            "height": round(int(row["height"]) / 10, 1),
            "weight": round(int(row["weight"]) / 10, 1),
            "gender": gender,
            "catchRate": int(species_rows[sid]["capture_rate"] or 0),
            "stats": stats.get(row["id"], {}),
            "sprite": sprite,
            "dex": flavor.get(sid, ""),
            "eggGroups": [egg_names.get(e, e) for e in egg_of.get(sid, [])],
            "hatchSteps": (int(species_rows[sid]["hatch_counter"] or 0) * 255),
            "learnset": {
                "level": [[lv, name] for lv, name in sorted(level_moves.get(row["id"], {}).items())],
                "machine": machine_moves.get(row["id"], []),
            },
            "evolution": [{"id": int(x), "name": species_zh.get(x, x), "method": evo_method(x)} for x in chain_of(sid)] if has_evo else [],
        })

    pokemon.sort(key=lambda p: p["id"])
    with open(os.path.join(content, "pokemon.json"), "w", encoding="utf-8") as f:
        json.dump(pokemon, f, ensure_ascii=False, separators=(",", ":"))
    print("宝可梦: %d 条，精灵图 %d 张" % (len(pokemon), copied))

    moves = [{
        "id": int(r["id"]),
        "name": move_zh.get(r["id"]) or move_en.get(r["id"]) or r["identifier"],
        "en": move_en.get(r["id"]) or r["identifier"].replace("-", " ").title(),
        "type": type_zh.get(r["type_id"], "一般"),
        "category": DAMAGE_CLASS.get(r["damage_class_id"], "变化"),
        "power": int(r["power"]) if r["power"] else None,
        "accuracy": int(r["accuracy"]) if r["accuracy"] else None,
        "pp": int(r["pp"]) if r["pp"] else None,
        "generation": int(r["generation_id"]),
    } for r in read("moves", csvdir)]
    moves.sort(key=lambda m: m["id"])
    with open(os.path.join(content, "moves.json"), "w", encoding="utf-8") as f:
        json.dump(moves, f, ensure_ascii=False, separators=(",", ":"))
    print("招式: %d 条" % len(moves))

    abilities_out = [{
        "id": int(r["id"]),
        "name": ability_zh.get(r["id"]) or ability_en.get(r["id"]) or r["identifier"],
        "en": ability_en.get(r["id"]) or r["identifier"].replace("-", " ").title(),
        "generation": int(r["generation_id"]),
        "identifier": r["identifier"],
    } for r in read("abilities", csvdir)]
    abilities_out.sort(key=lambda a: a["id"])
    with open(os.path.join(content, "abilities.json"), "w", encoding="utf-8") as f:
        json.dump(abilities_out, f, ensure_ascii=False, separators=(",", ":"))
    print("特性: %d 条" % len(abilities_out))

    items = [{
        "id": int(r["id"]),
        "name": item_zh.get(r["id"]) or item_en.get(r["id"]) or r["identifier"],
        "en": item_en.get(r["id"]) or r["identifier"].replace("-", " ").title(),
        "category": cat_name.get(r["category_id"], "其他"),
        "cost": int(r["cost"]) if r.get("cost") else 0,
        "generation": int(r["generation_id"]) if r.get("generation_id") else 0,
        "identifier": r["identifier"],
    } for r in read("items", csvdir)]
    items.sort(key=lambda i: i["id"])
    with open(os.path.join(content, "items.json"), "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, separators=(",", ":"))
    print("道具: %d 条" % len(items))

    # ---------- 地点 ----------
    region_zh = {r["region_id"]: r["name"] for r in read("region_names", csvdir) if r["local_language_id"] == ZH}
    region_order = {"1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 8, "10": 9}
    loc_zh = {r["location_id"]: r["name"] for r in read("location_names", csvdir) if r["local_language_id"] == ZH}
    loc_en = {r["location_id"]: r["name"] for r in read("location_names", csvdir) if r["local_language_id"] == EN}
    locations, seen = [], set()
    for r in read("locations", csvdir):
        rid = r.get("region_id")
        if rid not in region_order:
            continue
        name = loc_zh.get(r["id"]) or loc_en.get(r["id"]) or r["identifier"].replace("-", " ").title()
        key = (rid, name)
        if key in seen:
            continue
        seen.add(key)
        locations.append({
            "name": name,
            "en": loc_en.get(r["id"]) or r["identifier"].replace("-", " ").title(),
            "region": region_zh.get(rid, rid),
            "generation": region_order[rid],
            "desc": "",
        })
    locations.sort(key=lambda x: (x["generation"], x["region"], x["name"]))
    with open(os.path.join(content, "locations.json"), "w", encoding="utf-8") as f:
        json.dump(locations, f, ensure_ascii=False, separators=(",", ":"))
    print("地点: %d 条（中文名 %d 条）" % (len(locations), sum(1 for x in locations if x["name"] != x["en"])))

    eff = {(r["damage_type_id"], r["target_type_id"]): int(r["damage_factor"])
           for r in read("type_efficacy", csvdir)}
    types_out = []
    for tid, zh in sorted(type_zh.items(), key=lambda x: int(x[0])):
        if int(tid) > 18:
            continue
        en = type_en.get(tid, "")
        strong, weak, immune = [], [], []
        for other in range(1, 19):
            oname = type_zh.get(str(other))
            if not oname:
                continue
            f = eff.get((tid, str(other)), 100)
            if f == 200:
                strong.append(oname)
            elif f == 50:
                weak.append(oname)
            elif f == 0:
                immune.append(oname)
        types_out.append({"name": zh, "en": en, "color": TYPE_COLORS.get(en.lower(), "#8899aa"),
                          "strong": strong, "weak": weak, "immune": immune, "desc": ""})
    with open(os.path.join(content, "types.json"), "w", encoding="utf-8") as f:
        json.dump(types_out, f, ensure_ascii=False, indent=1)
    print("属性: %d 条" % len(types_out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
