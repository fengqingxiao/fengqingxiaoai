#!/usr/bin/env python3
"""宝可梦图鉴站点的静态生成器。

读取 site/content/*.json，生成 docs/ 下的静态页面。
不依赖任何第三方库，构建命令：python3 site/build.py
"""
import json
import math
import os
import re
import shutil
from html import escape

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(ROOT, "content")
STATIC = os.path.join(ROOT, "static")
OUT = os.path.join(os.path.dirname(ROOT), "docs")

SITE_NAME = "宝可梦图鉴"
SITE_EN = "POKÉMON ATLAS"
SITE_DESC = "一个由数据驱动的宝可梦资料库：图鉴、招式、特性、道具、属性相克与世代沿革。"

NAV = [
    ("index.html", "首页", "home"),
    ("pokedex.html", "图鉴", "pokedex"),
    ("moves.html", "招式", "moves"),
    ("abilities.html", "特性", "abilities"),
    ("items.html", "道具", "items"),
    ("types.html", "属性", "types"),
    ("locations.html", "地区", "locations"),
    ("characters.html", "人物", "characters"),
    ("games.html", "游戏", "games"),
    ("anime.html", "动画", "anime"),
]


# ---------------------------------------------------------------- 基础工具

def load(name):
    path = os.path.join(CONTENT, name + ".json")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def esc(v):
    return escape("" if v is None else str(v))


def type_color(types, name):
    for t in types:
        if t["name"] == name:
            return t.get("color", "#8899aa")
    return "#8899aa"


def type_chip(name, types, small=False, link=True):
    """link=False 时输出 span：卡片本身就是 <a>，HTML 不允许嵌套链接。"""
    cls = "chip-type chip-type-sm" if small else "chip-type"
    tag = "a" if link else "span"
    href = ' href="types.html#t-%s"' % esc(name) if link else ""
    return '<%s class="%s"%s style="--tc:%s">%s</%s>' % (
        tag, cls, href, type_color(types, name), esc(name), tag)


def stat_bar(label, value, maxv=255):
    pct = max(2, min(100, round(value / maxv * 100)))
    tone = "is-low" if value < 50 else ("is-high" if value >= 110 else "")
    return (
        '<div class="stat-row">'
        '<span class="stat-name">%s</span>'
        '<span class="stat-track"><i class="%s" style="width:%d%%"></i></span>'
        '<b class="stat-num">%s</b>'
        "</div>" % (esc(label), tone, pct, esc(value))
    )


def page(title, body, active="", desc="", depth=0):
    prefix = "../" * depth
    nav_html = "".join(
        '<a class="nav-link%s" href="%s%s">%s</a>'
        % (" is-active" if key == active else "", prefix, url, esc(label))
        for url, label, key in NAV
    )
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s · %s</title>
<meta name="description" content="%s">
<link rel="icon" href="%sassets/favicon.svg">
<link rel="stylesheet" href="%sassets/style.css">
</head>
<body data-depth="%d">
<header class="topbar">
  <div class="wrap topbar-inner">
    <a class="brand" href="%sindex.html">
      <span class="brand-mark">◈</span>
      <span class="brand-text"><b>%s</b><i>%s</i></span>
    </a>
    <nav class="nav">%s</nav>
    <div class="topbar-actions">
      <button class="icon-btn" id="searchOpen" title="搜索（按 / 或 Ctrl+K）" aria-label="搜索">
        <svg width="17" height="17" viewBox="0 0 16 16" fill="currentColor"><path d="M10.68 11.74l3.29 3.29-.71.71-3.29-3.29a5.5 5.5 0 1 1 .71-.71ZM6.5 11a4.5 4.5 0 1 0 0-9 4.5 4.5 0 0 0 0 9Z"/></svg>
      </button>
      <button class="icon-btn" id="randomBtn" title="随机条目" aria-label="随机条目">
        <svg width="17" height="17" viewBox="0 0 16 16" fill="currentColor"><path d="M3 3h3.5v1.5H3a.5.5 0 0 0-.5.5v6a.5.5 0 0 0 .5.5h3.5V13H3a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Zm7.44 1.44L13.5 7.5l-3.06 3.06-1.06-1.06 1.25-1.25H7.5v-1.5h3.13L9.38 5.5l1.06-1.06Z"/></svg>
      </button>
      <button class="nav-toggle" id="navToggle" aria-label="菜单">☰</button>
    </div>
  </div>
</header>
<main class="wrap">%s</main>
<footer class="footer">
  <div class="wrap footer-inner">
    <span>%s · 社区资料库框架</span>
    <span class="footer-dim">内容由站点数据文件提供，欢迎补充</span>
  </div>
</footer>
<div class="search-overlay" id="searchOverlay" hidden>
  <div class="search-panel">
    <div class="search-head">
      <input id="searchInput" type="search" placeholder="搜索宝可梦、招式、特性、道具、地区…" autocomplete="off">
      <button id="searchClose" class="search-close" aria-label="关闭">Esc</button>
    </div>
    <div class="search-results" id="searchResults"></div>
  </div>
</div>
<script src="%sassets/app.js" defer></script>
</body>
</html>
""" % (
        esc(title), SITE_NAME, esc(desc or SITE_DESC), prefix, prefix, depth, prefix,
        esc(SITE_NAME), esc(SITE_EN), nav_html, body, esc(SITE_NAME), prefix)


# ---------------------------------------------------------------- 首页

def render_index(data):
    pokemon = data["pokemon"]
    games = data["games"]
    counts = [
        ("宝可梦", len(pokemon), "pokedex.html"),
        ("招式", len(data["moves"]), "moves.html"),
        ("特性", len(data["abilities"]), "abilities.html"),
        ("道具", len(data["items"]), "items.html"),
        ("属性", len(data["types"]), "types.html"),
        ("地区", len(data["locations"]), "locations.html"),
        ("人物", len(data["characters"]), "characters.html"),
        ("游戏", len(games), "games.html"),
        ("动画", len(data["anime"]), "anime.html"),
    ]

    stats = "".join(
        '<a class="stat" href="%s"><b>%d</b><span>%s</span></a>' % (url, n, esc(label))
        for label, n, url in counts
    )

    cards = "".join(
        """<a class="module" href="%(url)s">
  <span class="module-icon" style="--g1:%(c1)s;--g2:%(c2)s">%(glyph)s</span>
  <span class="module-body">
    <b>%(label)s</b>
    <i>%(desc)s</i>
  </span>
  <span class="module-count">%(n)d</span>
</a>""" % {
            "url": url, "label": esc(label), "desc": esc(desc), "n": n,
            "glyph": glyph, "c1": c1, "c2": c2,
        }
        for label, n, url, glyph, desc, c1, c2 in [
            ("宝可梦图鉴", len(pokemon), "pokedex.html", "◉", "按属性与世代检索的完整名录", "#3ea6ff", "#7c5cff"),
            ("招式大全", len(data["moves"]), "moves.html", "✦", "威力、命中、PP 与学习条件", "#ff7a45", "#ffb347"),
            ("特性一览", len(data["abilities"]), "abilities.html", "◈", "战斗中生效的被动能力", "#35c96a", "#a8e63f"),
            ("道具资料", len(data["items"]), "items.html", "❖", "球、树果、进化石与战斗道具", "#b565e0", "#ff5fa2"),
            ("属性相克", len(data["types"]), "types.html", "▲", "十八属性的攻防关系矩阵", "#4fd8e8", "#3ea6ff"),
            ("地区地点", len(data["locations"]), "locations.html", "◍", "各世代舞台与城镇道路", "#8fd14f", "#35c96a"),
            ("人物档案", len(data["characters"]), "characters.html", "☗", "同伴、道馆馆主与劲敌", "#ff5c4d", "#ff8fa0"),
            ("游戏世代", len(games), "games.html", "▤", "正作、重制与平台沿革", "#5a6cff", "#7c5cff"),
            ("动画系列", len(data["anime"]), "anime.html", "▷", "各系列与剧场版脉络", "#ffcc00", "#ff7a45"),
        ]
    )

    gens = sorted({g.get("generation", 0) for g in games if g.get("generation")})
    timeline = "".join(
        '<div class="tl"><b>%s</b><span>%s</span></div>' % (esc(g.get("generation", "")), esc(g.get("title", "")))
        for g in sorted(games, key=lambda x: x.get("generation", 0))
    ) if games else '<p class="muted">尚未录入游戏世代数据。</p>'

    featured = "".join(
        """<a class="dex-card" href="pokemon/%s.html" style="--tc:%s">
  <span class="dex-no">#%s</span>
  <span class="dex-art"></span>
  <span class="dex-name">%s</span>
  <span class="dex-types">%s</span>
</a>""" % (esc(p["id"]), type_color(data["types"], p["types"][0]), esc(p["id"]), esc(p["name"]),
           "".join(type_chip(t, data["types"], True, link=False) for t in p["types"]))
        for p in pokemon[:8]
    ) or '<p class="muted">图鉴数据为空，先把条目写进 site/content/pokemon.json。</p>'

    body = """
<section class="hero">
  <div class="hero-grid"></div>
  <div class="hero-glow g1"></div><div class="hero-glow g2"></div><div class="hero-glow g3"></div>
  <p class="eyebrow">POKÉMON ATLAS</p>
  <h1>宝可梦资料库<span class="hero-dot">.</span></h1>
  <p class="lede">%(desc)s</p>
  <div class="hero-search">
    <button class="hero-search-btn" id="heroSearch">
      <svg width="18" height="18" viewBox="0 0 16 16" fill="currentColor"><path d="M10.68 11.74l3.29 3.29-.71.71-3.29-3.29a5.5 5.5 0 1 1 .71-.71ZM6.5 11a4.5 4.5 0 1 0 0-9 4.5 4.5 0 0 0 0 9Z"/></svg>
      搜索宝可梦、招式、特性、道具…
      <kbd>/</kbd>
    </button>
  </div>
  <div class="hero-stats">%(stats)s</div>
</section>

<section class="section">
  <div class="section-head"><h2>浏览模块</h2><span class="section-note">9 个分类 · 持续补充中</span></div>
  <div class="modules">%(cards)s</div>
</section>

<section class="section">
  <div class="section-head"><h2>精选图鉴</h2><a class="more" href="pokedex.html">查看全部 →</a></div>
  <div class="dex-grid">%(featured)s</div>
</section>

<section class="section">
  <div class="section-head"><h2>世代沿革</h2><a class="more" href="games.html">游戏列表 →</a></div>
  <div class="timeline">%(timeline)s</div>
</section>
""" % {
        "desc": esc(SITE_DESC), "stats": stats, "cards": cards,
        "featured": featured, "timeline": timeline,
    }
    return page("首页", body, "home")


# ---------------------------------------------------------------- 图鉴

def render_pokedex(data):
    pokemon = sorted(data["pokemon"], key=lambda p: p.get("id", 0))
    gens = sorted({p.get("generation") for p in pokemon if p.get("generation")})
    used_types = [t["name"] for t in data["types"] if any(t["name"] in p.get("types", []) for p in pokemon)]

    cards = "".join(
        """<a class="dex-card" href="pokemon/%(id)s.html" data-id="%(id)s" data-no="#%(id)s" data-name="%(name)s" data-en="%(en)s" data-types="%(types_attr)s" data-gen="%(gen)s" data-hp="%(hp)s" data-atk="%(atk)s" data-spe="%(spe)s" style="--tc:%(color)s">
  <span class="dex-no">#%(id)s</span>
  <span class="dex-art"></span>
  <span class="dex-name">%(name)s</span>
  <span class="dex-sub">%(en)s</span>
  <span class="dex-types">%(chips)s</span>
</a>""" % {
            "id": esc(p["id"]), "gen": esc(p.get("generation", "")),
            "types_attr": esc(",".join(p.get("types", []))),
            "name": esc(p["name"]), "en": esc(p.get("en", "")),
            "color": type_color(data["types"], p["types"][0]),
            "chips": "".join(type_chip(t, data["types"], True, link=False) for t in p.get("types", [])),
            "hp": p.get("stats", {}).get("hp", 0),
            "atk": p.get("stats", {}).get("atk", 0),
            "spe": p.get("stats", {}).get("spe", 0),
        }
        for p in pokemon
    ) or '<p class="muted">暂无数据。</p>'

    type_filters = "".join(
        '<button class="fchip" data-type="%s" style="--tc:%s">%s</button>' % (
            esc(t), type_color(data["types"], t), esc(t))
        for t in used_types
    )
    gen_filters = "".join(
        '<button class="fchip" data-gen="%s">%s 世代</button>' % (esc(g), esc(g))
        for g in gens
    )

    body = """
<section class="page-head">
  <p class="eyebrow">POKÉDEX</p>
  <h1>宝可梦图鉴</h1>
  <p class="lede">共 %(count)d 条记录。按属性、世代筛选，或直接搜索名称。</p>
</section>

<div class="toolbar">
  <div class="field">
    <svg width="15" height="15" viewBox="0 0 16 16" fill="currentColor"><path d="M10.68 11.74l3.29 3.29-.71.71-3.29-3.29a5.5 5.5 0 1 1 .71-.71ZM6.5 11a4.5 4.5 0 1 0 0-9 4.5 4.5 0 0 0 0 9Z"/></svg>
    <input id="dexSearch" type="search" placeholder="输入名称或图鉴编号">
  </div>
  <div class="sort-wrap">
    <label>排序</label>
    <select id="dexSort">
      <option value="id">图鉴编号</option>
      <option value="name">名称</option>
      <option value="hp">HP</option>
      <option value="atk">攻击</option>
      <option value="spe">速度</option>
    </select>
  </div>
</div>

<div class="filters" id="dexFilters">
  <div class="frow"><span class="flabel">属性</span>%(type_filters)s<button class="fchip" data-type="">全部</button></div>
  <div class="frow"><span class="flabel">世代</span>%(gen_filters)s<button class="fchip" data-gen="">全部</button></div>
</div>

<p class="result-meta" id="dexMeta"></p>
<div class="dex-grid" id="dexGrid">%(cards)s</div>
<p class="empty" id="dexEmpty" hidden>没有符合条件的宝可梦。</p>
""" % {
        "count": len(pokemon), "type_filters": type_filters,
        "gen_filters": gen_filters, "cards": cards,
    }
    return page("图鉴", body, "pokedex", desc="按属性与世代检索宝可梦")


def render_pokemon(p, data, prev_p, next_p):
    types = data["types"]
    stats = p.get("stats", {})
    stat_labels = [("HP", "hp"), ("攻击", "atk"), ("防御", "def"), ("特攻", "spa"), ("特防", "spd"), ("速度", "spe")]
    total = sum(stats.get(k, 0) for _, k in stat_labels)

    stat_html = "".join(stat_bar(label, stats.get(k, 0)) for label, k in stat_labels)
    stat_html += '<div class="stat-row stat-total"><span class="stat-name">合计</span><span class="stat-track"><i style="width:%d%%"></i></span><b class="stat-num">%d</b></div>' % (
        min(100, round(total / 720 * 100)), total)

    def info_row(k, v):
        if not v:
            return ""
        return '<div class="info-row"><dt>%s</dt><dd>%s</dd></div>' % (esc(k), v)

    abilities = "、".join(
        '<a href="../abilities.html#a-%s">%s</a>' % (esc(a), esc(a)) for a in p.get("abilities", [])
    ) or "—"

    evo = ""
    if p.get("evolution"):
        parts = []
        for i, step in enumerate(p["evolution"]):
            parts.append('<span class="evo-node"><b>%s</b></span>' % esc(step.get("name", "")))
            if i < len(p["evolution"]) - 1:
                parts.append('<span class="evo-arrow">%s</span>' % esc(step.get("method", "→")))
        evo = '<section class="panel"><h2>进化链</h2><div class="evo">%s</div></section>' % "".join(parts)

    dex_text = ('<section class="panel"><h2>图鉴说明</h2><p class="dex-text">%s</p></section>' % esc(p["dex"])) if p.get("dex") else ""
    trivia = ""
    if p.get("trivia"):
        trivia = '<section class="panel"><h2>补充</h2><ul class="bullets">%s</ul></section>' % "".join(
            "<li>%s</li>" % esc(t) for t in p["trivia"])

    nav = '<div class="prevnext">%s%s</div>' % (
        ('<a class="pn" href="%s.html"><span>← 上一号</span><b>%s</b></a>' % (esc(prev_p["id"]), esc(prev_p["name"]))) if prev_p else "<span></span>",
        ('<a class="pn pn-next" href="%s.html"><span>下一号 →</span><b>%s</b></a>' % (esc(next_p["id"]), esc(next_p["name"]))) if next_p else "<span></span>",
    )

    body = """
<nav class="crumbs"><a href="../index.html">首页</a><i>/</i><a href="../pokedex.html">图鉴</a><i>/</i><span>%s</span></nav>

<section class="entry-head">
  <div class="entry-title">
    <span class="entry-no" style="--tc:%s">#%s</span>
    <h1>%s</h1>
    <p class="entry-en">%s</p>
    <div class="entry-types">%s</div>
  </div>
  <div class="entry-art" style="--tc:%s"><span></span></div>
</section>

<div class="entry-grid">
  <aside class="panel info-panel">
    <h2>基本信息</h2>
    <dl class="info-list">
      %s
      %s
      %s
      %s
      %s
      %s
      %s
      %s
    </dl>
  </aside>
  <section class="panel">
    <h2>种族值</h2>
    %s
  </section>
</div>

%s
%s
%s
%s
""" % (
        esc(p["name"]), type_color(types, p["types"][0]), esc(p["id"]), esc(p["name"]), esc(p.get("en", "")),
        "".join(type_chip(t, types) for t in p.get("types", [])),
        type_color(types, p["types"][0]),
        info_row("分类", esc(p.get("category", ""))),
        info_row("特性", abilities),
        info_row("身高", ("%s m" % p["height"]) if p.get("height") else ""),
        info_row("体重", ("%s kg" % p["weight"]) if p.get("weight") else ""),
        info_row("性别比例", esc(p.get("gender", ""))),
        info_row("登场世代", ("第 %s 世代" % p["generation"]) if p.get("generation") else ""),
        info_row("捕获率", esc(p.get("catchRate", ""))),
        info_row("基础经验", esc(p.get("exp", ""))),
        stat_html, dex_text, evo, trivia, nav,
    )
    return page(p["name"], body, "pokedex", desc="%s（%s）的资料页" % (p["name"], p.get("en", "")), depth=1)


# ---------------------------------------------------------------- 通用列表页

def render_moves(data):
    rows = "".join(
        """<tr>
  <td class="col-name"><a href="#m-%(name)s">%(name)s</a><i>%(en)s</i></td>
  <td>%(type)s</td>
  <td><span class="cat cat-%(cat)s">%(cat)s</span></td>
  <td class="num">%(power)s</td>
  <td class="num">%(acc)s</td>
  <td class="num">%(pp)s</td>
  <td class="dim">%(desc)s</td>
</tr>""" % {
            "name": esc(m["name"]), "en": esc(m.get("en", "")),
            "type": type_chip(m.get("type", "一般"), data["types"], True),
            "cat": esc(m.get("category", "变化")), "power": esc(m.get("power", "—")),
            "acc": esc(m.get("accuracy", "—")), "pp": esc(m.get("pp", "—")),
            "desc": esc(m.get("desc", "")),
        }
        for m in data["moves"]
    ) or '<tr><td colspan="7" class="muted">暂无数据，把招式写入 site/content/moves.json。</td></tr>'

    body = """
<section class="page-head">
  <p class="eyebrow">MOVES</p>
  <h1>招式大全</h1>
  <p class="lede">共 %d 个招式。可按名称筛选，表头点击可排序。</p>
</section>
<div class="toolbar">
  <div class="field"><svg width="15" height="15" viewBox="0 0 16 16" fill="currentColor"><path d="M10.68 11.74l3.29 3.29-.71.71-3.29-3.29a5.5 5.5 0 1 1 .71-.71ZM6.5 11a4.5 4.5 0 1 0 0-9 4.5 4.5 0 0 0 0 9Z"/></svg>
  <input class="table-filter" data-target="movesTable" type="search" placeholder="搜索招式名"></div>
</div>
<div class="table-wrap">
<table class="data-table" id="movesTable">
  <thead><tr><th>招式</th><th>属性</th><th>分类</th><th class="num">威力</th><th class="num">命中</th><th class="num">PP</th><th>说明</th></tr></thead>
  <tbody>%s</tbody>
</table>
</div>
""" % (len(data["moves"]), rows)
    return page("招式", body, "moves", desc="宝可梦招式数据")


def render_abilities(data):
    cards = "".join(
        """<article class="mini-card" id="a-%(name)s">
  <h3>%(name)s <i>%(en)s</i></h3>
  <p>%(effect)s</p>
  <div class="mini-meta">第 %(gen)s 世代</div>
</article>""" % {
            "name": esc(a["name"]), "en": esc(a.get("en", "")),
            "effect": esc(a.get("effect", "")), "gen": esc(a.get("generation", "—")),
        }
        for a in data["abilities"]
    ) or '<p class="muted">暂无数据。</p>'

    body = """
<section class="page-head">
  <p class="eyebrow">ABILITIES</p>
  <h1>特性一览</h1>
  <p class="lede">共 %d 个特性。特性在战斗中持续生效，多数无法被主动触发。</p>
</section>
<div class="toolbar">
  <div class="field"><svg width="15" height="15" viewBox="0 0 16 16" fill="currentColor"><path d="M10.68 11.74l3.29 3.29-.71.71-3.29-3.29a5.5 5.5 0 1 1 .71-.71ZM6.5 11a4.5 4.5 0 1 0 0-9 4.5 4.5 0 0 0 0 9Z"/></svg>
  <input class="card-filter" data-target="abilityList" type="search" placeholder="搜索特性"></div>
</div>
<div class="mini-grid" id="abilityList">%s</div>
""" % (len(data["abilities"]), cards)
    return page("特性", body, "abilities", desc="宝可梦特性数据")


def render_items(data):
    cats = sorted({i.get("category", "其他") for i in data["items"]})
    cards = "".join(
        """<article class="mini-card" data-cat="%(cat)s">
  <span class="mini-tag">%(cat)s</span>
  <h3>%(name)s <i>%(en)s</i></h3>
  <p>%(effect)s</p>
  <div class="mini-meta">%(where)s</div>
</article>""" % {
            "cat": esc(i.get("category", "其他")), "name": esc(i["name"]), "en": esc(i.get("en", "")),
            "effect": esc(i.get("effect", "")), "where": esc(i.get("where", "")),
        }
        for i in data["items"]
    ) or '<p class="muted">暂无数据。</p>'

    chips = "".join('<button class="fchip" data-cat="%s">%s</button>' % (esc(c), esc(c)) for c in cats)

    body = """
<section class="page-head">
  <p class="eyebrow">ITEMS</p>
  <h1>道具资料</h1>
  <p class="lede">共 %d 件道具，按类别浏览。</p>
</section>
<div class="filters"><div class="frow"><span class="flabel">类别</span>%s<button class="fchip" data-cat="">全部</button></div></div>
<div class="mini-grid" id="itemList">%s</div>
""" % (len(data["items"]), chips, cards)
    return page("道具", body, "items", desc="宝可梦道具数据")


def render_types(data):
    types = data["types"]
    matrix_rows = []
    for atk in types:
        cells = []
        for dfn in types:
            if dfn["name"] in atk.get("strong", []):
                v, cls = 2, "eff2"
            elif dfn["name"] in atk.get("weak", []):
                v, cls = 0.5, "eff-half"
            elif dfn["name"] in atk.get("immune", []):
                v, cls = 0, "eff0"
            else:
                v, cls = 1, "eff1"
            cells.append('<td class="%s">%s</td>' % (cls, "2" if v == 2 else ("½" if v == 0.5 else ("0" if v == 0 else ""))))
        matrix_rows.append(
            '<tr><th><span class="chip-type chip-type-sm" style="--tc:%s">%s</span></th>%s</tr>'
            % (type_color(types, atk["name"]), esc(atk["name"]), "".join(cells))
        )
    head_cells = "".join(
        '<th><span class="chip-type chip-type-sm" style="--tc:%s">%s</span></th>' % (type_color(types, t["name"]), esc(t["name"]))
        for t in types
    )

    cards = "".join(
        """<article class="type-card" id="t-%(name)s" style="--tc:%(color)s">
  <header><span class="type-dot"></span><h3>%(name)s</h3><i>%(en)s</i></header>
  <p>%(desc)s</p>
  <div class="type-rel">
    <span class="rel-label">克制</span>%(strong)s
  </div>
  <div class="type-rel">
    <span class="rel-label">被抗</span>%(weak)s
  </div>
  <div class="type-rel">
    <span class="rel-label">无效</span>%(immune)s
  </div>
</article>""" % {
            "name": esc(t["name"]), "en": esc(t.get("en", "")), "color": t.get("color", "#8899aa"),
            "desc": esc(t.get("desc", "")),
            "strong": "".join(type_chip(x, types, True) for x in t.get("strong", [])) or '<span class="dim">—</span>',
            "weak": "".join(type_chip(x, types, True) for x in t.get("weak", [])) or '<span class="dim">—</span>',
            "immune": "".join(type_chip(x, types, True) for x in t.get("immune", [])) or '<span class="dim">—</span>',
        }
        for t in types
    )

    body = """
<section class="page-head">
  <p class="eyebrow">TYPES</p>
  <h1>属性相克</h1>
  <p class="lede">18 种属性，行表示攻击方，列表示防御方。</p>
</section>
<div class="table-wrap matrix-wrap">
  <table class="data-table matrix" id="typeMatrix">
    <thead><tr><th class="corner">攻 \\ 防</th>%s</tr></thead>
    <tbody>%s</tbody>
  </table>
</div>
<div class="matrix-legend"><span class="eff2">2</span> 效果拔群 <span class="eff-half">½</span> 效果不佳 <span class="eff0">0</span> 无效 <span class="eff1">空白</span> 一般</div>
<section class="section"><div class="section-head"><h2>属性说明</h2></div>
<div class="type-grid">%s</div></section>
""" % (head_cells, "".join(matrix_rows), cards)
    return page("属性", body, "types", desc="18 属性相克关系")


def render_locations(data):
    groups = {}
    for loc in data["locations"]:
        groups.setdefault(loc.get("region", "其他"), []).append(loc)
    sections = []
    for region, items in groups.items():
        cards = "".join(
            """<article class="mini-card" id="l-%(name)s">
  <span class="mini-tag">%(gen)s</span>
  <h3>%(name)s <i>%(en)s</i></h3>
  <p>%(desc)s</p>
</article>""" % {
                "gen": esc(loc.get("generation", "")), "name": esc(loc["name"]), "en": esc(loc.get("en", "")),
                "desc": esc(loc.get("desc", "")),
            }
            for loc in items
        )
        sections.append(
            '<section class="section" id="r-%s"><div class="section-head"><h2>%s地区</h2><span class="section-note">%d 个地点</span></div><div class="mini-grid">%s</div></section>'
            % (esc(region), esc(region), len(items), cards)
        )

    body = """
<section class="page-head">
  <p class="eyebrow">REGIONS</p>
  <h1>地区与地点</h1>
  <p class="lede">按地区归档的城镇、道路与特殊场景。</p>
</section>
%s
""" % ("".join(sections) or '<p class="muted">暂无数据。</p>')
    return page("地区", body, "locations", desc="宝可梦世界地区与地点")


def render_characters(data):
    cards = "".join(
        """<article class="mini-card" id="c-%(name)s">
  <span class="mini-tag">%(role)s</span>
  <h3>%(name)s <i>%(en)s</i></h3>
  <p>%(desc)s</p>
  <div class="mini-meta">%(region)s</div>
</article>""" % {
            "role": esc(c.get("role", "人物")), "name": esc(c["name"]), "en": esc(c.get("en", "")),
            "desc": esc(c.get("desc", "")), "region": esc(c.get("region", "")),
        }
        for c in data["characters"]
    ) or '<p class="muted">暂无数据。</p>'

    body = """
<section class="page-head">
  <p class="eyebrow">CHARACTERS</p>
  <h1>人物档案</h1>
  <p class="lede">同伴、馆主、四天王与劲敌。</p>
</section>
<div class="toolbar">
  <div class="field"><svg width="15" height="15" viewBox="0 0 16 16" fill="currentColor"><path d="M10.68 11.74l3.29 3.29-.71.71-3.29-3.29a5.5 5.5 0 1 1 .71-.71ZM6.5 11a4.5 4.5 0 1 0 0-9 4.5 4.5 0 0 0 0 9Z"/></svg>
  <input class="card-filter" data-target="charList" type="search" placeholder="搜索人物"></div>
</div>
<div class="mini-grid" id="charList">%s</div>
""" % cards
    return page("人物", body, "characters", desc="宝可梦系列人物")


def render_games(data):
    items = sorted(data["games"], key=lambda g: g.get("generation", 0))
    rows = ""
    for g in items:
        rows += """<article class="game-row">
  <div class="game-gen"><b>%s</b><span>GEN</span></div>
  <div class="game-main">
    <h3>%s <i>%s</i></h3>
    <p>%s</p>
    <div class="game-meta"><span>%s</span><span>%s</span></div>
  </div>
</article>""" % (
            esc(g.get("generation", "?")), esc(g.get("title", "")), esc(g.get("en", "")),
            esc(g.get("desc", "")), esc(g.get("platform", "")), esc(g.get("release", "")),
        )

    body = """
<section class="page-head">
  <p class="eyebrow">SERIES</p>
  <h1>游戏世代</h1>
  <p class="lede">正作、重制与外传的时间线。</p>
</section>
<div class="game-list">%s</div>
""" % (rows or '<p class="muted">暂无数据。</p>')
    return page("游戏", body, "games", desc="宝可梦游戏世代")


def render_anime(data):
    rows = "".join(
        """<article class="anime-row">
  <div class="anime-year">%s</div>
  <div class="anime-main"><h3>%s <i>%s</i></h3><p>%s</p></div>
  <div class="anime-ep">%s 集</div>
</article>""" % (
            esc(a.get("year", "")), esc(a.get("series", "")), esc(a.get("en", "")),
            esc(a.get("desc", "")), esc(a.get("episodes", "—")),
        )
        for a in data["anime"]
    ) or '<p class="muted">暂无数据。</p>'

    body = """
<section class="page-head">
  <p class="eyebrow">ANIMATION</p>
  <h1>动画系列</h1>
  <p class="lede">各世代动画与剧场版脉络。</p>
</section>
<div class="anime-list">%s</div>
""" % rows
    return page("动画", body, "anime", desc="宝可梦动画系列")


def render_about(data):
    body = """
<section class="page-head">
  <p class="eyebrow">ABOUT</p>
  <h1>关于本站</h1>
  <p class="lede">这是一个数据驱动的宝可梦资料库框架，内容持续补充中。</p>
</section>
<section class="panel prose">
  <h2>站点结构</h2>
  <p>全部页面由 <code>site/build.py</code> 依据 <code>site/content/*.json</code> 生成。新增条目只需编辑对应 JSON，然后重新构建。</p>
  <ul class="bullets">
    <li><code>pokemon.json</code> — 图鉴条目（编号、名称、属性、种族值、进化链等）</li>
    <li><code>moves.json</code> / <code>abilities.json</code> / <code>items.json</code> — 招式、特性、道具</li>
    <li><code>types.json</code> — 18 属性及其相克关系</li>
    <li><code>locations.json</code> / <code>characters.json</code> — 地区地点与人物</li>
    <li><code>games.json</code> / <code>anime.json</code> — 游戏世代与动画系列</li>
  </ul>
  <h2>构建</h2>
  <p><code>python3 site/build.py</code> 会把页面输出到 <code>docs/</code>，推送到 main 后由 GitHub Actions 自动部署到 Pages。</p>
  <h2>声明</h2>
  <p>本站为非官方粉丝资料库，宝可梦相关名称与设定版权归任天堂、Game Freak 与 The Pokémon Company 所有。</p>
</section>
"""
    return page("关于", body, "about", desc="关于本站")


# ---------------------------------------------------------------- 搜索索引

def build_search_index(data):
    items = []
    for p in data["pokemon"]:
        items.append({
            "t": p["name"], "s": p.get("en", ""), "u": "pokemon/%s.html" % p["id"],
            "c": "宝可梦", "k": " ".join(p.get("types", [])),
        })
    for m in data["moves"]:
        items.append({"t": m["name"], "s": m.get("en", ""), "u": "moves.html#m-%s" % m["name"],
                      "c": "招式", "k": m.get("type", "")})
    for a in data["abilities"]:
        items.append({"t": a["name"], "s": a.get("en", ""), "u": "abilities.html#a-%s" % a["name"],
                      "c": "特性", "k": ""})
    for i in data["items"]:
        items.append({"t": i["name"], "s": i.get("en", ""), "u": "items.html#i-%s" % i["name"],
                      "c": "道具", "k": i.get("category", "")})
    for t in data["types"]:
        items.append({"t": t["name"], "s": t.get("en", ""), "u": "types.html#t-%s" % t["name"],
                      "c": "属性", "k": ""})
    for l in data["locations"]:
        items.append({"t": l["name"], "s": l.get("en", ""), "u": "locations.html#l-%s" % l["name"],
                      "c": "地点", "k": l.get("region", "")})
    for c in data["characters"]:
        items.append({"t": c["name"], "s": c.get("en", ""), "u": "characters.html#c-%s" % c["name"],
                      "c": "人物", "k": c.get("role", "")})
    for g in data["games"]:
        items.append({"t": g.get("title", ""), "s": g.get("en", ""), "u": "games.html",
                      "c": "游戏", "k": g.get("platform", "")})
    for a in data["anime"]:
        items.append({"t": a.get("series", ""), "s": a.get("en", ""), "u": "anime.html",
                      "c": "动画", "k": str(a.get("year", ""))})
    return {"items": items}


# ---------------------------------------------------------------- 主流程

def main():
    data = {
        "pokemon": load("pokemon"),
        "moves": load("moves"),
        "abilities": load("abilities"),
        "items": load("items"),
        "types": load("types"),
        "locations": load("locations"),
        "characters": load("characters"),
        "games": load("games"),
        "anime": load("anime"),
    }

    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, "assets"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "pokemon"), exist_ok=True)

    for name in os.listdir(STATIC):
        src = os.path.join(STATIC, name)
        dst = os.path.join(OUT, "assets", name)
        if os.path.isfile(src):
            shutil.copy2(src, dst)

    pages = {
        "index.html": render_index(data),
        "pokedex.html": render_pokedex(data),
        "moves.html": render_moves(data),
        "abilities.html": render_abilities(data),
        "items.html": render_items(data),
        "types.html": render_types(data),
        "locations.html": render_locations(data),
        "characters.html": render_characters(data),
        "games.html": render_games(data),
        "anime.html": render_anime(data),
        "about.html": render_about(data),
    }

    pokemon = sorted(data["pokemon"], key=lambda p: p.get("id", 0))
    for i, p in enumerate(pokemon):
        pages["pokemon/%s.html" % p["id"]] = render_pokemon(
            p, data,
            pokemon[i - 1] if i > 0 else None,
            pokemon[i + 1] if i < len(pokemon) - 1 else None,
        )

    for path, html in pages.items():
        full = os.path.join(OUT, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(html)

    with open(os.path.join(OUT, "assets", "search.json"), "w", encoding="utf-8") as f:
        json.dump(build_search_index(data), f, ensure_ascii=False, separators=(",", ":"))

    with open(os.path.join(OUT, "404.html"), "w", encoding="utf-8") as f:
        f.write(page("页面不存在", '<section class="page-head"><h1>404</h1><p class="lede">这个条目还没有被收录。<a href="index.html">回到首页</a></p></section>', desc="页面不存在"))

    print("构建完成：%d 个页面 → %s" % (len(pages) + 2, OUT))


if __name__ == "__main__":
    main()
