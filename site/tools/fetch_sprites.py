#!/usr/bin/env python3
"""下载官方图鉴立绘（96px）到 site/static/sprites/。

来源：PokeAPI/sprites 仓库，经 jsDelivr CDN 分发。
用法：python3 site/tools/fetch_sprites.py [并发数]
已存在的文件会跳过，可重复运行以补齐失败项。
"""
import concurrent.futures
import json
import os
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "static", "sprites")
MIRRORS = [
    "https://gcore.jsdelivr.net/gh/PokeAPI/sprites@master/sprites/pokemon/%d.png",
    "https://fastly.jsdelivr.net/gh/PokeAPI/sprites@master/sprites/pokemon/%d.png",
    "https://testingcf.jsdelivr.net/gh/PokeAPI/sprites@master/sprites/pokemon/%d.png",
    "https://cdn.jsdelivr.net/gh/PokeAPI/sprites@master/sprites/pokemon/%d.png",
]


def fetch(pid):
    dst = os.path.join(OUT, "%d.png" % pid)
    if os.path.exists(dst) and os.path.getsize(dst) > 200:
        return "skip"
    for attempt in range(4):
        url = MIRRORS[(pid + attempt) % len(MIRRORS)] % pid
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                data = r.read()
            if data[:4] == b"\x89PNG":
                with open(dst, "wb") as f:
                    f.write(data)
                return "ok"
        except Exception:
            time.sleep(1.5)
    return "fail"


def main():
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 16
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(ROOT, "content", "pokemon.json"), encoding="utf-8") as f:
        ids = [p["id"] for p in json.load(f)]

    t0 = time.time()
    stats = {"ok": 0, "skip": 0, "fail": 0}
    failed = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        for pid, r in zip(ids, ex.map(fetch, ids)):
            stats[r] += 1
            if r == "fail":
                failed.append(pid)
            done = sum(stats.values())
            if done % 100 == 0:
                print("%d/%d  ok=%d fail=%d  %.0fs" % (done, len(ids), stats["ok"], stats["fail"], time.time() - t0), flush=True)
    print("完成：新增 %d，已存在 %d，失败 %d，用时 %.0fs" % (stats["ok"], stats["skip"], stats["fail"], time.time() - t0))
    if failed:
        print("失败编号:", failed[:40])
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
