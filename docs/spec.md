# Spec: 深圳户外景点指南 GitHub Pages

## Objective

将已经完成并通过验收的《深圳户外景点指南》发布为公开、稳定、无需登录即可访问的 GitHub Pages 静态站点。读者可以先了解覆盖范围，再在线打开 PDF，或下载 PDF / DOCX。

## Tech Stack

- 纯 HTML、CSS、原生 JavaScript
- GitHub Pages，公开仓库 `laypen-netizen/shenzhen-outdoor-guide-ebook`
- 不引入构建工具和第三方前端依赖

## Commands

- 本地预览：`python3 -m http.server 4173`
- HTML 链接检查：`python3 scripts/verify_site.py`
- Git 校验：`git diff --check`
- 在线检查：`curl -I https://laypen-netizen.github.io/shenzhen-outdoor-guide-ebook/`

## Project Structure

- `index.html`：站点首页及阅读入口
- `styles.css`：响应式样式
- `app.js`：按需加载 PDF 阅读器、复制链接
- `assets/`：封面与站点图标
- `downloads/`：PDF 与 DOCX 成品
- `scripts/verify_site.py`：静态资源、文案和文件完整性校验

## Code Style

```html
<a class="button button-primary" href="downloads/shenzhen-outdoor-guide.pdf">
  在线打开 PDF
</a>
```

- 使用语义化 HTML 和简体中文可访问标签。
- CSS 类名描述用途，不依赖框架缩写。
- JavaScript 仅增强体验；关闭 JavaScript 仍可访问和下载电子书。

## Testing Strategy

- 静态校验所有本地链接、必需元数据、电子书文件名和 SHA-256。
- 使用本地 HTTP 服务检查首页、PDF、DOCX 的 200 响应。
- 检查桌面与窄屏布局，不让 PDF 在首屏自动下载。
- 发布后读取 GitHub Pages 状态，并对线上首页和下载文件进行 HTTP 回查。

## Boundaries

- Always：保留图片类型说明、来源透明度和出行前复核提示；验证成品哈希。
- Ask first：自定义域名、付费服务或公开现有私有应用仓库。
- Never：提交密钥、将无关应用源码复制进公开仓库、修改原电子书内容。

## Success Criteria

- GitHub Pages 首页无需登录即可返回 200。
- PDF 与 DOCX 下载地址均可访问，线上文件大小与本地成品一致。
- 页面明确展示 229 个景点、10 个区、68 家博物馆、20 处美术空间和 271 页。
- 桌面及移动端均有清晰的阅读和下载入口。
- 原项目仓库保持私有，未提交改动不进入发布仓库。

## Open Questions

- 暂不绑定自定义域名；后续可单独配置。
