#!/usr/bin/env python3
"""从 Gmeek 产物与 Issue 备份生成图鉴索引 docs/wiki.json。

在 Gmeek 生成 docs/ 之后运行：读取 docs/postList.json 得到条目与 URL，
再从 backup/*.md 提取摘要、字数与阅读时长，供首页卡片使用。
"""
import json
import math
import os
import re
import sys

POST_LIST = "docs/postList.json"
BACKUP_DIR = "backup"
OUT = "docs/wiki.json"

CHARS_PER_MINUTE = 350


def md_filename(title: str) -> str:
    """与 Gmeek.py addOnePostJson 中的命名规则保持一致。"""
    name = re.sub(r'[<>:/\\|?*"]|[\0-\31]', "-", title)
    return name + ".md"


def clean_body(raw: str) -> str:
    lines = raw.rstrip("\n").split("\n")
    if lines and lines[-1].lstrip().startswith("##"):
        lines = lines[:-1]
    text = "\n".join(lines)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"^\s*>\s?", "", text, flags=re.M)
    text = re.sub(r"^\s*#+\s*", "", text, flags=re.M)
    text = re.sub(r"[*_`~]", "", text)
    return text.strip()


def excerpt_of(text: str, limit: int = 90) -> str:
    for block in re.split(r"\n\s*\n", text):
        block = " ".join(block.split())
        if len(block) >= 8 and not block.startswith("这是示例篇"):
            return block[:limit] + ("…" if len(block) > limit else "")
    return ""


def stats_of(text: str):
    chars = len(re.sub(r"\s", "", text))
    words = len(re.findall(r"[A-Za-z0-9]+", text))
    total = chars + words
    return total, max(1, math.ceil(total / CHARS_PER_MINUTE))


def main() -> int:
    if not os.path.exists(POST_LIST):
        print("缺少 %s，跳过" % POST_LIST)
        return 0

    with open(POST_LIST, encoding="utf-8") as f:
        raw = json.load(f)

    posts = []
    for key, item in raw.items():
        if not key.startswith("P"):
            continue
        title = item.get("postTitle", "")
        body = ""
        path = os.path.join(BACKUP_DIR, md_filename(title))
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                body = clean_body(f.read())

        words, minutes = stats_of(body)
        date = item.get("createdDate", "")
        posts.append(
            {
                "title": title,
                "url": item.get("postUrl", ""),
                "labels": item.get("labels", []),
                "date": date,
                "year": date[:4],
                "excerpt": excerpt_of(body),
                "words": words,
                "minutes": minutes,
            }
        )

    posts.sort(key=lambda p: p["date"])
    data = {"count": len(posts), "posts": posts}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

    print("已生成 %s：%d 条" % (OUT, len(posts)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
