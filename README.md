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
| `locations.json` | 981 个地点（按 10 个地区分组） | PokeAPI |
| `characters.json` | 人物 | 手工维护 |
| `games.json` | 游戏世代 | 手工维护 |
| `anime.json` | 动画系列（含登场人物） | 手工维护 |

## 已实现的功能

- 图鉴：属性/世代筛选、按编号/名称/HP/攻击/速度排序、搜索、分批加载，状态写入 URL 并可恢复滚动位置
- 条目页：种族值、蛋组与孵化步数、图鉴说明、可点击的进化链、可学招式（升级 + 学习器）
- 属性：18×18 相克矩阵 + 双属性组合计算器
- 招式 / 特性 / 道具：可筛选表格，带结构化简介
- 地区：可点击的示意地图 + 981 个地点分组
- 动画：系列独立页、登场人物、官方观看渠道说明
- 全站：搜索浮层、随机条目、OG 分享卡片、sitemap.xml、robots.txt、资源版本号

## 工具

- `site/tools/import_pokeapi.py <csv目录> <精灵图目录>`：把 PokeAPI 的 CSV 与本地精灵图合成为上述内容文件。
- `site/tools/fetch_sprites.py [并发数]`：下载 96px 官方图鉴立绘到 `site/static/sprites/`，可重复运行补齐失败项。

## 关于原始整合包

PKSA 整合包的 `Data/*.dat`、`Graphics/**`、`Data/Scripts.rxdata` 均由 SAplay 打包器加密（文件头 `CRACKERS-ASS-HOLE`），密钥位于 `Game.exe`，无法离线读取。因此站内数值采用官方公开数据，精灵立绘使用 PokeAPI/sprites。

## 声明

非官方粉丝资料库。宝可梦相关名称、图像与设定版权归任天堂、Game Freak、The Pokémon Company 所有。
