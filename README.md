# 宝可梦图鉴

数据驱动的宝可梦资料库，白底明亮未来风。页面全部由 `site/build.py` 依据 `site/content/*.json` 生成，推送到 `main` 后自动部署 GitHub Pages。

## 本地构建

```bash
python3 site/build.py               # 输出到 docs/
python3 -m http.server -d docs 8000 # 预览
```

## 内容数据

| 文件 | 内容 | 来源 |
| --- | --- | --- |
| `pokemon.json` | 1025 只宝可梦（属性、种族值、特性、图鉴说明、进化链） | PokeAPI |
| `moves.json` | 937 个招式 | PokeAPI |
| `abilities.json` | 374 个特性 | PokeAPI |
| `items.json` | 2223 件道具 | PokeAPI |
| `types.json` | 18 属性及相克关系 | PokeAPI |
| `locations.json` | 地区地点 | 手工维护 |
| `characters.json` | 人物 | 手工维护 |
| `games.json` | 游戏世代 | 手工维护 |
| `anime.json` | 动画系列 | 手工维护 |

## 工具

- `site/tools/import_pokeapi.py <csv目录> <精灵图目录>`：把 PokeAPI 的 CSV 与本地精灵图合成为上述内容文件。
- `site/tools/fetch_sprites.py [并发数]`：下载 96px 官方图鉴立绘到 `site/static/sprites/`，可重复运行补齐失败项。

## 关于原始整合包

PKSA 整合包的 `Data/*.dat`、`Graphics/**`、`Data/Scripts.rxdata` 均由 SAplay 打包器加密（文件头 `CRACKERS-ASS-HOLE`），密钥位于 `Game.exe`，无法离线读取。因此站内数值采用官方公开数据，精灵立绘使用 PokeAPI/sprites。

## 声明

非官方粉丝资料库。宝可梦相关名称、图像与设定版权归任天堂、Game Freak、The Pokémon Company 所有。
