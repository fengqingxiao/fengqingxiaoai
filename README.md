# 宝可梦图鉴

数据驱动的宝可梦资料库，白底明亮未来风。所有页面由 `site/build.py` 依据 `site/content/*.json` 生成，推送到 `main` 后自动部署到 GitHub Pages。

## 本地构建

```bash
python3 site/build.py      # 输出到 docs/
python3 -m http.server 8000 -d docs
```

## 内容文件

| 文件 | 内容 |
| --- | --- |
| `site/content/pokemon.json` | 图鉴条目（编号、属性、种族值、进化链） |
| `site/content/moves.json` | 招式 |
| `site/content/abilities.json` | 特性 |
| `site/content/items.json` | 道具 |
| `site/content/types.json` | 18 属性与相克关系 |
| `site/content/locations.json` | 地区地点 |
| `site/content/characters.json` | 人物 |
| `site/content/games.json` | 游戏世代 |
| `site/content/anime.json` | 动画系列 |

新增条目后执行一次构建即可，无需改动模板。
