# Spec: 深圳全域景点 Web / H5 指南

## Objective

将《深圳户外景点指南》完整转换为可直接浏览的 Web 与 H5 静态产品，而不是只提供在线 PDF。316 个景点必须全部出现在网页目录中，并各有独立详情页；PDF / DOCX 仅作为附加下载格式。

## Users and Core Journeys

- 手机游客：按区域、类型和票务筛选，查看交通、停车、季节与状态后直接出发。
- 桌面读者：搜索景点，浏览十区目录，并在独立详情页阅读完整介绍与图片来源。
- 内容维护者：从结构化数据重新生成全站，并用自动检查证明没有遗漏景点。

## Tech Stack

- 纯 HTML、CSS、原生 JavaScript 与 Python 标准库生成器
- GitHub Pages 静态托管
- 无前端框架、无运行时 API、无第三方脚本

## Commands

- 导出内容：`python3 scripts/export_from_ebook.py --source-dir ../shenzhen-outdoor-guide/ebook`
- 生成站点：`python3 scripts/build_site.py`
- 内容与链接校验：`python3 scripts/verify_site.py`
- JavaScript 校验：`node --check app.js && node --check catalog.js`
- 本地预览：`python3 -m http.server 4173`

## Project Structure

- `index.html`：Web / H5 首页、快速入口与精选景点
- `places/index.html`：316 个景点的搜索与筛选目录
- `places/<编号>/index.html`：逐景点完整详情页
- `districts/<区>/index.html`：深圳十区专题页
- `data/places.json`：全站结构化内容真源
- `assets/places/`：316 张逐景点图片
- `scripts/export_from_ebook.py`：从电子书工程导出内容与图片
- `scripts/build_site.py`：静态页面生成器
- `scripts/verify_site.py`：覆盖、链接、哈希与 H5 合同检查
- `downloads/`：PDF / DOCX 附件

## Content Contract

每个景点详情页必须包含：

1. 景点名称、区域、类型和图片类型标注
2. 120–220 字专属介绍
3. 2–3 个核心看点
4. 适合人群与第一次游览建议
5. 免费 / 收费 / 预约等票务标签
6. 公共交通指引
7. 自驾停车引导
8. 季节气候匹配
9. 当前开放状态
10. 官方参考来源及实景图授权信息（适用时）

## Web / H5 Interaction Contract

- 目录支持关键词、区域、主题类型、票务筛选，筛选结果即时计数。
- 所有内容在关闭 JavaScript 后仍可浏览；JavaScript 只增强筛选、收藏、分享和移动导航。
- 手机端提供底部快捷导航、足够大的点击区域、单列详情布局和安全区适配。
- PDF 不在首屏或后台自动加载，仅作为附件下载。
- 每个详情页提供上一站、下一站和同区相关推荐。

## Testing Strategy

- 校验 316 个唯一景点、10 个区域、316 个详情页和 316 张图片一一对应。
- 校验每页内容合同、所有内部链接、站点地图和附件 SHA-256。
- 本地 HTTP 检查首页、目录、典型区页和典型详情页。
- 浏览器检查 1440px 桌面、390px H5，无横向溢出、无控制台错误。
- 发布后检查首页、目录、随机详情页和附件均返回 200。

## Boundaries

- Always：保留免费/收费、交通、停车、季节、状态、来源与图片类型透明标注。
- Ask first：自定义域名、付费服务、用户账号、地图 SDK 或实时定位。
- Never：省略景点、将编辑配图冒充实景图、提交密钥、依赖运行时数据库。

## Success Criteria

- 线上首页以 Web 内容为主体，不以 PDF 阅读器为主体。
- 316 个景点均可从目录进入独立详情页，页面内容字段完整。
- 十区专题页、关键词和筛选功能可用。
- 390px 手机宽度无横向滚动，主要按钮触控尺寸不小于 44px。
- GitHub Pages 构建成功，公开地址无需登录即可访问。

## Open Questions

- 暂不接入地图和实时导航；交通与停车先使用经过审查的文字指引。
- 暂不绑定自定义域名；保持 GitHub Pages 项目地址。
