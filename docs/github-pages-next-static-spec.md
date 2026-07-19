# Spec: Next.js 攻略索引版 GitHub Pages 发布

## Objective

将 `projects/shenzhen-outdoor-guide/` 的重构版公开页面迁移到
`https://laypen-netizen.github.io/shenzhen-outdoor-guide-ebook/`，使桌面端和
390px 移动端首屏与已验收截图一致。GitHub Pages 只承载静态前端；数据库、API、
Cron、Next.js Data Cache、React `cache` 和数据库错误脱敏边界继续由 Vercel 版本承载。

## Tech Stack

- 来源：Next.js 16 重构版页面契约与 `globals.css`
- 目标：GitHub Pages 静态 HTML / CSS / JavaScript
- 构建：Python 3 标准库，不新增依赖

## Commands

```bash
python3 -m unittest scripts/test_import_next_static.py
python3 scripts/import_next_static.py
python3 scripts/verify_site.py
python3 -m unittest discover -s scripts -p 'test_*.py'
node --check static-app.js
```

## Project Structure

- `scripts/import_next_static.py`：固定来源与目标边界，生成静态页面和样式
- `scripts/test_import_next_static.py`：URL 重写、脚本清理和元数据回归
- `static-app.js`：在浏览器中执行六条演示索引的筛选与高级条件状态
- `index.html`、`rating/`、`source-status/`、`takedown/`：GitHub Pages 发布页面

## Code Style

```python
rewritten = rewrite_internal_url(
    value,
    source_origin=SOURCE_ORIGIN,
    public_base_url=PUBLIC_BASE_URL,
)
```

Python 使用类型标注和纯函数处理 HTML；客户端脚本只操作当前页面 DOM，不引入框架。

## Testing Strategy

- 单元测试先证明 Next.js 运行时脚本被移除、站内静态链接正确保留、动态详情链接回到
  Vercel、canonical/OG URL 指向 GitHub Pages。
- 站点验证继续检查 330 个历史内容页和资源完整性，同时增加新版首页关键文案与脚本检查。
- 最后用桌面和 390px 浏览器验证首屏、移动导航、筛选、无横向溢出和控制台错误。

## Boundaries

- Always：保留 `import-only`、演示数据和来源平台免责声明；发布前验证线上 HTML。
- Ask first：新增公开 API、数据库迁移、修改鉴权或 GitHub Pages 配置。
- Never：把静态站描述成已运行 PostgreSQL、Cron 或 Next.js 服务端缓存；提交凭据。

## Success Criteria

1. 目标域名首屏显示“周末去哪，先查别人走过的路。”及 `06 条演示索引`。
2. 桌面端与 390px 移动端布局与参考截图一致，无横向溢出。
3. 首页六条演示索引可按关键词、区域、玩法和高级条件筛选；有值时高级条件自动展开。
4. 移动主导航、纠错入口、出发前复核、评级页、来源页与 canonical/OG/Twitter 元数据存在。
5. 动态详情、博主页面和下架提交明确使用 Vercel 服务端，不伪装为 GitHub Pages 本地能力。
6. 测试、站点验证、JavaScript 语法检查、提交、推送和 GitHub Pages 线上回读全部通过。

## Open Questions

无。用户已指定视觉版本与目标域名；按“静态前端 + Vercel 服务端边界”实施。
