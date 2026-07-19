# 深圳户外指南 GitHub Pages 前端

GitHub Pages 首页使用 `shenzhen-outdoor-guide` Next.js 项目的“深圳城市户外编辑部”重构视觉，静态展示六条明确标记的演示索引；原有 330 个景点内容页、PDF 和 DOCX 继续保留。

- 在线站点：<https://laypen-netizen.github.io/shenzhen-outdoor-guide-ebook/>
- 全部景点：<https://laypen-netizen.github.io/shenzhen-outdoor-guide-ebook/places/>
- PDF / DOCX：`downloads/`

## 内容概览

- 首页、移动主导航、渐进式筛选、出发前复核、评级规则、来源状态和纠错入口与 Next.js 重构版保持一致
- 六条演示索引支持关键词、区域、玩法、难度、耗时、人群、设施、来源与时间筛选；高级条件有值时自动展开
- canonical、Open Graph 和 Twitter 元数据指向 GitHub Pages 正式 URL
- 330 个独立景点专页，完整保留介绍、亮点、适合人群、首次游览建议、票务、交通、停车、季节气候、开放状态与图片来源
- 深圳 10 个行政区 / 新区专题页
- 68 家博物馆、20 处美术空间
- 补充各区具名开放绿道、跨区远足径、历史风貌区、古村建筑和代表性公园
- 支持关键词、区域、主题、票务、室内场馆与收藏筛选
- Web 桌面布局和 H5 移动布局，含移动端底部导航、收藏和分享
- 首页使用响应式 WebP 主视觉；移动端主题、十区和代表景点采用原生横向滑动，减少首屏下载和纵向滚动
- 目录卡片只展示 60 字以内摘要，完整介绍只保留在详情页；景点图片按 720w / 960w / 原图 `srcset` 自适应加载
- 69 张授权实景图逐张保留作者、许可与来源；其余 261 张图片明确标注为“编辑配图·非现场实景”

## 页面结构

- `index.html`：重构版攻略索引首页与六条演示数据
- `rating/`、`source-status/`、`takedown/`：评级、平台能力边界和纠错入口
- `places/index.html`：保留的 330 个景点内容目录
- `places/001/`—`places/330/`：景点详情页
- `districts/`：十区专题页
- `downloads/`：PDF / DOCX 离线附件
- `data/places.json`：站点结构化数据
- `data/place_ids.json`：永久公开编号注册表；既有网址不因内容增补而变化
- `assets/places/720/`、`assets/places/960/`：由生成器维护的响应式景点图；原图缺失会使构建失败
- 响应式 JPG 重采样优先使用本机 Pillow；未安装时在 macOS 回退到 `sips`，不增加前端运行时依赖
- `sources/wechat/`：公众号 Markdown 与媒体的本地审计输入；已由 `.gitignore` 排除，禁止随站点提交或发布

## 本地预览与校验

```bash
# 从审核后的电子书数据导出结构化内容与图片
python3 scripts/export_from_ebook.py \
  --source-dir ../shenzhen-outdoor-guide/ebook

# 生成首页、目录、十区页、330 个详情页与 sitemap
python3 scripts/build_site.py

# 最后覆盖为 Next.js 重构版首页，并补齐静态评级、来源与纠错页
python3 scripts/import_next_static.py

# 校验内容数量、字段、链接、SEO / 分享元数据、图片和离线附件
python3 scripts/verify_site.py

# 验证静态迁移、历史生成器与客户端脚本
python3 -m unittest discover -s scripts -p 'test_*.py'
node --check static-app.js

# 在另一个终端启动带调试端口的本机 Chrome 后，检查桌面与 390px 真实渲染
node scripts/browser_check.mjs

# 本地预览
python3 -m http.server 4173
```

首次迁移旧站时才使用 `--id-baseline <historical places.json>` 建立编号注册表；日常导出只读取并增补 `data/place_ids.json`，新景点顺延编号，不重排旧网址。

站点不依赖前端框架或第三方脚本，可直接由 GitHub Pages 托管。本仓库只承载公开阅读内容，不包含原应用源码、密钥或运行时配置。

## 静态与服务端边界

GitHub Pages 不运行 PostgreSQL、API、Cron、Next.js Data Cache、React `cache` 或数据库错误脱敏边界。首页筛选基于六条公开演示数据在浏览器本地执行；地点详情、博主详情和纠错表单需要服务端时，链接会明确进入 `https://shenzhen-outdoor-guide.vercel.app`。完整迁移规格见 `docs/github-pages-next-static-spec.md`。

`browser_check.mjs` 默认连接 `http://127.0.0.1:9231` 的 Chrome 调试端口，并检查 `http://127.0.0.1:4173`；需要改端口时使用 `CHROME_DEBUG_ORIGIN` 与 `SITE_ORIGIN`。检查包含移动首页 6,500px 高度预算、900KB 首次传输预算、目录 1,000KB 与详情页 600KB 首次传输预算、主视觉水平对齐、延迟图片按需加载、三组横向内容轨道，以及每轮检查后 Chrome 调试页数量不增加。公众号抓取正文和媒体只留在本地，不属于可发布站点内容。
