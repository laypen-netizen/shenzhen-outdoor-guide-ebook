# 深圳户外景点指南 Web / H5

《深圳户外景点指南》的完整响应式内容站。网页本身是主要阅读载体，PDF / DOCX 仅作为离线附件。

- 在线站点：<https://laypen-netizen.github.io/shenzhen-outdoor-guide-ebook/>
- 全部景点：<https://laypen-netizen.github.io/shenzhen-outdoor-guide-ebook/places/>
- PDF / DOCX：`downloads/`

## 内容概览

- 330 个独立景点专页，完整保留介绍、亮点、适合人群、首次游览建议、票务、交通、停车、季节气候、开放状态与图片来源
- 深圳 10 个行政区 / 新区专题页
- 68 家博物馆、20 处美术空间
- 补充各区具名开放绿道、跨区远足径、历史风貌区、古村建筑和代表性公园
- 支持关键词、区域、主题、票务、室内场馆与收藏筛选
- Web 桌面布局和 H5 移动布局，含移动端底部导航、收藏和分享
- 授权实景图逐张保留作者、许可与来源；其余图片明确标注为“编辑配图·非现场实景”

## 页面结构

- `index.html`：首页与十区入口
- `places/index.html`：330 个景点的可筛选目录
- `places/001/`—`places/330/`：景点详情页
- `districts/`：十区专题页
- `downloads/`：PDF / DOCX 离线附件
- `data/places.json`：站点结构化数据
- `data/place_ids.json`：永久公开编号注册表；既有网址不因内容增补而变化

## 本地预览与校验

```bash
# 从审核后的电子书数据导出结构化内容与图片
python3 scripts/export_from_ebook.py \
  --source-dir ../shenzhen-outdoor-guide/ebook

# 生成首页、目录、十区页、330 个详情页与 sitemap
python3 scripts/build_site.py

# 校验内容数量、字段、链接、图片和离线附件
python3 scripts/verify_site.py

# 本地预览
python3 -m http.server 4173
```

首次迁移旧站时才使用 `--id-baseline <historical places.json>` 建立编号注册表；日常导出只读取并增补 `data/place_ids.json`，新景点顺延编号，不重排旧网址。

站点不依赖前端框架或第三方脚本，可直接由 GitHub Pages 托管。本仓库只承载公开阅读内容，不包含原应用源码、密钥或运行时配置。
