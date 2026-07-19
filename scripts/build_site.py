#!/usr/bin/env python3
"""Build the complete static Web/H5 guide from data/places.json."""

from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path
from urllib.parse import quote, urlencode


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://laypen-netizen.github.io/shenzhen-outdoor-guide-ebook/"
FEATURED_NAMES = (
    "莲花山公园",
    "梧桐山风景名胜区",
    "深圳湾公园",
    "盐田海滨栈道",
    "欢乐港湾",
    "大芬油画村",
    "观澜版画村",
    "马峦山郊野公园",
    "深圳科学技术馆",
    "深圳市天文台",
)
PROFILE_ICONS = {
    "mountain": "山",
    "coast": "海",
    "wetland": "湿",
    "city": "城",
    "waterway": "水",
    "museum": "博",
    "art": "艺",
    "science": "科",
    "heritage": "古",
    "family": "亲",
}


def h(value: object) -> str:
    return html.escape(str(value), quote=True)


def write(relative: str, content: str) -> None:
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = "\n".join(line.rstrip() for line in content.strip().splitlines())
    path.write_text(normalized + "\n", encoding="utf-8")


def versioned_asset(prefix: str, relative: str) -> str:
    digest = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()[:10]
    return f"{prefix}{relative}?v={digest}"


def nav(prefix: str, active: str, *, district_slug: str | None = None) -> str:
    items = (
        ("home", f"{prefix}index.html", "首页"),
        ("places", f"{prefix}places/", "全部景点"),
        ("districts", f"{prefix}index.html#districts", "十区指南"),
        ("downloads", f"{prefix}downloads/", "电子书附件"),
    )
    desktop = "".join(
        f'<a href="{href}"{(" aria-current=\"page\"" if key == active else "")}>{label}</a>'
        for key, href, label in items
    )
    district_href = f"{prefix}districts/{district_slug}/" if district_slug else f"{prefix}index.html#districts"
    return f"""
    <a class="skip-link" href="#main-content">跳到主要内容</a>
    <header class="site-header">
      <div class="page-width header-inner">
        <a class="brand" href="{prefix}index.html" aria-label="深圳户外景点指南首页">
          <span class="brand-mark" aria-hidden="true">深</span>
          <span>深圳户外景点指南</span>
        </a>
        <nav class="desktop-nav" aria-label="主要导航">{desktop}</nav>
        <button class="menu-button" type="button" aria-expanded="false" aria-controls="mobile-menu">
          <span aria-hidden="true">☰</span><span class="sr-only">打开导航</span>
        </button>
      </div>
      <nav class="mobile-menu" id="mobile-menu" aria-label="移动端导航" hidden>{desktop}</nav>
    </header>
    <nav class="mobile-tabbar" aria-label="移动端快捷导航">
      <a href="{prefix}index.html"{(" aria-current=\"page\"" if active == "home" else "")}><span aria-hidden="true">⌂</span>首页</a>
      <a href="{prefix}places/"{(" aria-current=\"page\"" if active == "places" else "")}><span aria-hidden="true">⌕</span>景点</a>
      <a href="{district_href}"{(" aria-current=\"page\"" if active == "districts" else "")}><span aria-hidden="true">区</span>本区</a>
      <a href="{prefix}places/?favorites=1"><span aria-hidden="true">♡</span>收藏</a>
    </nav>
    """


def footer(prefix: str, place_count: int, updated_at: str) -> str:
    return f"""
    <footer class="site-footer">
      <div class="page-width footer-grid">
        <div>
          <a class="footer-brand" href="{prefix}index.html">深圳户外景点指南</a>
          <p>{place_count} 个景点完整网页版，让每一次出发都少一点信息差。</p>
        </div>
        <div class="footer-links">
          <a href="{prefix}places/">全部景点</a>
          <a href="{prefix}index.html#districts">十区指南</a>
          <a href="{prefix}downloads/">PDF / DOCX 附件</a>
          <a href="{prefix}data/places.json">开放数据</a>
        </div>
      </div>
      <div class="page-width footer-bottom">
        <span>更新于 {h(updated_at)}</span>
        <span>开放、票务与交通可能调整，出发前请再次核对官方公告。</span>
      </div>
    </footer>
    """


def shell(
    *,
    title: str,
    description: str,
    canonical_path: str,
    prefix: str,
    active: str,
    body: str,
    image_path: str = "assets/shenzhen-nine-scenes.png",
    scripts: tuple[str, ...] = (),
    district_slug: str | None = None,
    json_ld: dict[str, object] | None = None,
    body_class: str = "",
    place_count: int,
    updated_at: str,
) -> str:
    canonical = f"{BASE_URL}{canonical_path}"
    script_tags = "".join(
        f'<script src="{versioned_asset(prefix, script)}" defer></script>' for script in ("app.js", *scripts)
    )
    structured = ""
    if json_ld:
        structured = (
            '<script type="application/ld+json">'
            + json.dumps(json_ld, ensure_ascii=False).replace("</", "<\\/")
            + "</script>"
        )
    return f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
    <meta name="theme-color" content="#075b52">
    <meta name="description" content="{h(description)}">
    <meta property="og:type" content="website">
    <meta property="og:locale" content="zh_CN">
    <meta property="og:title" content="{h(title)}">
    <meta property="og:description" content="{h(description)}">
    <meta property="og:url" content="{canonical}">
    <meta property="og:image" content="{BASE_URL}{h(image_path)}">
    <link rel="canonical" href="{canonical}">
    <link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml">
    <link rel="manifest" href="{prefix}manifest.webmanifest">
    <link rel="stylesheet" href="{versioned_asset(prefix, 'styles.css')}">
    <title>{h(title)}</title>
    {structured}
  </head>
  <body class="{h(body_class)}">
    {nav(prefix, active, district_slug=district_slug)}
    <main id="main-content">{body}</main>
    {footer(prefix, place_count, updated_at)}
    {script_tags}
  </body>
</html>"""


def ticket_class(kind: str) -> str:
    return {
        "free": "tag-free",
        "paid": "tag-paid",
        "reservation": "tag-reservation",
        "closed": "tag-closed",
    }[kind]


def place_card(spot: dict[str, object], prefix: str, *, eager: bool = False) -> str:
    image = spot["image"]
    loading = "eager" if eager else "lazy"
    alt = image["description"] if image["kind"] == "real_photo" else f'{spot["name"]}主题编辑配图（非现场实景）'
    return f"""
    <article class="place-card" data-name="{h(spot['name'])}" data-area="{h(spot['area'])}"
      data-district="{h(spot['district_primary'])}" data-profile="{h(spot['profile_key'])}"
      data-ticket="{h(spot['ticket_kind'])}" data-indoor="{str(bool(spot['indoor'])).lower()}"
      data-place-id="{h(spot['spot_number'])}">
      <a class="place-card-image" href="{prefix}{h(spot['detail_path'])}">
        <img src="{prefix}{h(image['path'])}" alt="{h(alt)}" loading="{loading}" decoding="async" width="1200" height="540">
        <span class="image-kind {('real-photo' if image['kind'] == 'real_photo' else 'editorial-image')}">{h(image['kind_label'])}</span>
      </a>
      <div class="place-card-body">
        <div class="card-tags">
          <span>{h(spot['district_primary'])}</span>
          <span>{h(spot['profile_label'])}</span>
          <span class="{ticket_class(str(spot['ticket_kind']))}">{h(str(spot['ticket']).split('｜')[0])}</span>
        </div>
        <h3><a href="{prefix}{h(spot['detail_path'])}">{h(spot['name'])}</a></h3>
        <p>{h(spot['intro'])}</p>
        <div class="card-footer">
          <span>{h(spot['area'])}</span>
          <a href="{prefix}{h(spot['detail_path'])}" aria-label="查看{h(spot['name'])}完整介绍">完整介绍 <span aria-hidden="true">→</span></a>
        </div>
      </div>
    </article>
    """


def index_body(data: dict[str, object]) -> str:
    meta = data["meta"]
    places = data["places"]
    place_by_name = {spot["name"]: spot for spot in places}
    featured = [place_by_name[name] for name in FEATURED_NAMES if name in place_by_name]
    profiles = data["profiles"]
    profile_links = "".join(
        f'<a class="scene-card" href="places/?{urlencode({"profile": key})}"><span aria-hidden="true">{PROFILE_ICONS[key]}</span><strong>{h(label)}</strong><small>查看相关景点</small></a>'
        for key, label in profiles.items()
    )
    district_cards = "".join(
        f"""
        <a class="district-card" href="districts/{h(district['slug'])}/">
          <span class="district-count">{district['count']} 处</span>
          <h3>{h(district['name'])}</h3>
          <p>{h(district['tagline'])}</p>
          <span class="district-link">打开本区指南 →</span>
        </a>
        """
        for district in data["districts"]
    )
    featured_cards = "".join(place_card(spot, "", eager=index < 2) for index, spot in enumerate(featured))
    return f"""
    <section class="web-hero">
      <div class="page-width web-hero-grid">
        <div class="web-hero-copy">
          <p class="eyebrow eyebrow-warm">SHENZHEN · COMPLETE WEB GUIDE</p>
          <h1>深圳 {meta['place_count']} 个景点，<br>都在这里完整展开。</h1>
          <p>不是一张景点名单，也不只是一份 PDF。每个景点都有独立网页，完整呈现介绍、票务、公共交通、自驾停车、季节气候、开放状态与图片来源。</p>
          <form class="hero-search" action="places/" method="get" role="search">
            <label class="sr-only" for="home-search">搜索景点、区域或类型</label>
            <input id="home-search" name="q" type="search" placeholder="搜索景点、区域或类型，例如：天文台" autocomplete="off">
            <button type="submit">查找景点</button>
          </form>
          <div class="hero-actions">
            <a class="button button-primary" href="places/">浏览全部 {meta['place_count']} 个景点</a>
            <a class="button button-secondary" href="#districts">按区域查看</a>
          </div>
          <p class="attachment-note">需要离线保存？<a href="downloads/">PDF / DOCX 作为附加格式下载</a></p>
        </div>
        <div class="hero-visual" aria-label="指南内容概览">
          <img src="assets/shenzhen-nine-scenes.png" alt="深圳山海、城市、公园与文化场馆主题编辑插画拼图" width="1600" height="900" fetchpriority="high">
          <div class="hero-visual-label"><span>WEB + H5</span><strong>山海 · 城市 · 人文</strong></div>
          <dl class="hero-stats">
            <div><dt>{meta['place_count']}</dt><dd>景点独立网页</dd></div>
            <div><dt>{meta['district_count']}</dt><dd>区域专题</dd></div>
            <div><dt>{meta['museum_count']}</dt><dd>家博物馆</dd></div>
            <div><dt>{meta['art_count']}</dt><dd>处美术空间</dd></div>
          </dl>
        </div>
      </div>
    </section>
    <section class="section section-paper">
      <div class="page-width">
        <div class="section-heading"><p class="eyebrow">FIND YOUR SCENE</p><h2>今天想去哪里？</h2><p>按出行场景快速缩小范围，再进入完整目录精细筛选。</p></div>
        <div class="scene-grid">{profile_links}</div>
      </div>
    </section>
    <section class="section section-white" id="districts">
      <div class="page-width">
        <div class="section-heading"><p class="eyebrow">TEN DISTRICTS</p><h2>十区各有自己的深圳</h2><p>从福田中心区到大鹏山海，把跨城清单拆成真正可执行的区域行程。</p></div>
        <div class="district-grid">{district_cards}</div>
      </div>
    </section>
    <section class="section section-paper">
      <div class="page-width">
        <div class="section-heading heading-row"><div><p class="eyebrow">START HERE</p><h2>十个代表性起点</h2></div><a class="text-link" href="places/">查看全部景点 →</a></div>
        <div class="place-grid featured-grid">{featured_cards}</div>
      </div>
    </section>
    <section class="section decision-section">
      <div class="page-width decision-grid">
        <div><p class="eyebrow eyebrow-warm">DECIDE BEFORE YOU GO</p><h2>每一页，都帮你做出行决定</h2></div>
        <div class="decision-list">
          <article><span>01</span><h3>免费还是收费</h3><p>用显眼标签区分免费、收费、预约与暂不开放。</p></article>
          <article><span>02</span><h3>地铁公交怎么到</h3><p>说明到达片区、入口选择与返程节点，而不只给一个站名。</p></article>
          <article><span>03</span><h3>自驾停在哪里</h3><p>标明正规停车选择、满位替代方案和不能临停的位置。</p></article>
          <article><span>04</span><h3>什么季节更合适</h3><p>结合深圳高温、雷雨、台风季和滨海天气调整行程。</p></article>
        </div>
      </div>
    </section>
    """


def catalog_body(data: dict[str, object]) -> str:
    district_options = "".join(f'<option value="{h(item["name"])}">{h(item["name"])}（{item["count"]}）</option>' for item in data["districts"])
    profile_options = "".join(f'<option value="{h(key)}">{h(label)}</option>' for key, label in data["profiles"].items())
    cards = "".join(place_card(spot, "../") for spot in data["places"])
    return f"""
    <section class="catalog-hero compact-hero">
      <div class="page-width">
        <nav class="breadcrumb" aria-label="面包屑"><a href="../index.html">首页</a><span>／</span><span aria-current="page">全部景点</span></nav>
        <p class="eyebrow eyebrow-warm">ALL {data['meta']['place_count']} PLACES</p>
        <h1>深圳全域景点目录</h1>
        <p>{data['meta']['place_count']} 个景点全部在网页中展开。输入名字、所在片区或主题，也可以组合区域、类型与票务筛选。</p>
      </div>
    </section>
    <section class="catalog-section">
      <div class="page-width catalog-layout">
        <aside class="filter-panel" id="filter-panel" aria-label="景点筛选">
          <form id="filter-form">
            <div class="filter-heading"><h2>筛选景点</h2><button id="reset-filters" type="reset">清除</button></div>
            <label for="place-search">关键词</label>
            <input id="place-search" name="q" type="search" placeholder="景点、片区、类型" autocomplete="off">
            <label for="district-filter">区域</label>
            <select id="district-filter" name="district"><option value="">全部区域</option>{district_options}</select>
            <label for="profile-filter">主题类型</label>
            <select id="profile-filter" name="profile"><option value="">全部类型</option>{profile_options}</select>
            <label for="ticket-filter">票务</label>
            <select id="ticket-filter" name="ticket">
              <option value="">全部票务</option><option value="free">免费</option><option value="paid">收费</option>
              <option value="reservation">预约 / 待核</option><option value="closed">暂不开放</option>
            </select>
            <label class="check-label"><input id="indoor-filter" name="indoor" type="checkbox" value="1"> 只看室内场馆</label>
            <label class="check-label"><input id="favorites-filter" name="favorites" type="checkbox" value="1"> 只看我的收藏</label>
          </form>
          <div class="filter-help"><strong>提示</strong><p>开放与票务会变化，详情页保留了当前状态和官方来源。</p></div>
        </aside>
        <div class="catalog-results">
          <div class="results-toolbar"><p id="results-count" role="status" aria-live="polite">共 {data['meta']['place_count']} 个景点</p><button class="mobile-filter-button" id="mobile-filter-button" type="button" aria-expanded="false" aria-controls="filter-panel">筛选</button></div>
          <div class="place-grid catalog-grid" id="place-grid">{cards}</div>
          <div class="empty-state" id="empty-state" hidden><strong>没有匹配的景点</strong><p>试试减少筛选条件，或换一个关键词。</p></div>
        </div>
      </div>
    </section>
    """


def district_body(district: dict[str, object], spots: list[dict[str, object]]) -> str:
    profiles = sorted({spot["profile_label"] for spot in spots})
    profile_chips = "".join(f"<span>{h(item)}</span>" for item in profiles)
    cards = "".join(place_card(spot, "../../", eager=index < 2) for index, spot in enumerate(spots))
    return f"""
    <section class="district-hero">
      <div class="page-width">
        <nav class="breadcrumb" aria-label="面包屑"><a href="../../index.html">首页</a><span>／</span><a href="../../index.html#districts">十区指南</a><span>／</span><span aria-current="page">{h(district['name'])}</span></nav>
        <div class="district-hero-grid">
          <div><p class="eyebrow eyebrow-warm">DISTRICT GUIDE · {district['count']} PLACES</p><h1>{h(district['name'])}</h1><p>{h(district['tagline'])}</p><div class="chip-row">{profile_chips}</div></div>
          <aside class="route-card"><span>建议组合</span><p>{h(district['route'])}</p></aside>
        </div>
      </div>
    </section>
    <section class="section section-paper">
      <div class="page-width district-tip"><div><p class="eyebrow">SMALL PICKS</p><h2>本区小众选择</h2></div><p>{h(district['small_pick'])}</p></div>
    </section>
    <section class="section section-white">
      <div class="page-width">
        <div class="section-heading heading-row"><div><p class="eyebrow">ALL PLACES</p><h2>{h(district['name'])}全部 {district['count']} 个景点</h2></div><a class="text-link" href="../../places/?district={quote(str(district['name']))}">在总目录中筛选 →</a></div>
        <div class="place-grid">{cards}</div>
      </div>
    </section>
    """


def info_block(icon: str, title: str, content: str, css_class: str = "") -> str:
    return f'<article class="info-card {css_class}"><span class="info-icon" aria-hidden="true">{icon}</span><div><h2>{h(title)}</h2><p>{h(content)}</p></div></article>'


def detail_body(
    spot: dict[str, object],
    previous: dict[str, object] | None,
    next_spot: dict[str, object] | None,
    related: list[dict[str, object]],
) -> str:
    image = spot["image"]
    alt = image["description"] if image["kind"] == "real_photo" else f'{spot["name"]}主题编辑配图（非现场实景）'
    highlights = "".join(f"<li>{h(item)}</li>" for item in spot["highlights"])
    related_cards = "".join(place_card(item, "../../") for item in related)
    image_credit = ""
    if image["kind"] == "real_photo":
        image_credit = f"""
        <div class="image-credit"><strong>实景图来源</strong><span>{h(image['description'])}</span>
          <span>作者：{h(image['artist'])}</span>
          <a href="{h(image['detail_url'])}" target="_blank" rel="noopener">查看原图</a>
          <a href="{h(image['license_url'])}" target="_blank" rel="noopener">{h(image['license'])}</a>
        </div>
        """
    else:
        image_credit = '<div class="image-credit editorial-credit"><strong>图片说明</strong><span>本图为编辑配图，用于表达景点类型与游览氛围，不是现场实景照片。</span></div>'

    prev_link = (
        f'<a href="../../{h(previous["detail_path"])}"><span>← 上一站</span><strong>{h(previous["name"])}</strong></a>'
        if previous
        else "<span></span>"
    )
    next_link = (
        f'<a class="next-link" href="../../{h(next_spot["detail_path"])}"><span>下一站 →</span><strong>{h(next_spot["name"])}</strong></a>'
        if next_spot
        else "<span></span>"
    )
    return f"""
    <section class="detail-hero">
      <div class="page-width">
        <nav class="breadcrumb" aria-label="面包屑"><a href="../../index.html">首页</a><span>／</span><a href="../../places/">全部景点</a><span>／</span><a href="../../districts/{h(spot['district_slug'])}/">{h(spot['district_primary'])}</a><span>／</span><span aria-current="page">{h(spot['name'])}</span></nav>
        <div class="detail-hero-grid">
          <figure class="detail-image-wrap">
            <img src="../../{h(image['path'])}" alt="{h(alt)}" width="1200" height="540" fetchpriority="high">
            <figcaption class="image-kind {('real-photo' if image['kind'] == 'real_photo' else 'editorial-image')}">{h(image['kind_label'])}</figcaption>
          </figure>
          <div class="detail-title">
            <div class="card-tags"><span>{h(spot['district_primary'])}</span><span>{h(spot['profile_label'])}</span><span class="{ticket_class(str(spot['ticket_kind']))}">{h(str(spot['ticket']).split('｜')[0])}</span></div>
            <p class="spot-number">SHENZHEN GUIDE · {h(spot['spot_number'])}</p>
            <h1>{h(spot['name'])}</h1>
            <p class="detail-area">{h(spot['area'])} · {h(spot['category'])}</p>
            <p class="detail-intro">{h(spot['intro'])}</p>
            <div class="detail-actions">
              <button class="button button-primary favorite-button" type="button" data-favorite="{h(spot['spot_number'])}" aria-pressed="false">♡ 收藏景点</button>
              <button class="button button-outline share-button" type="button" data-share-title="{h(spot['name'])}">分享本页</button>
            </div>
            <p class="action-status" role="status" aria-live="polite"></p>
          </div>
        </div>
      </div>
    </section>
    <section class="detail-content-section">
      <div class="page-width detail-content-grid">
        <div class="detail-main">
          <section class="highlight-section"><p class="eyebrow">WHY GO</p><h2>核心看点</h2><ol>{highlights}</ol></section>
          <div class="info-grid">
            {info_block('人', '适合谁', str(spot['fit']))}
            {info_block('径', '第一次怎样看', str(spot['first_visit']))}
            {info_block('交', '公共交通', str(spot['transport']), 'transport-card')}
            {info_block('停', '自驾停车', str(spot['parking']), 'parking-card')}
            {info_block('季', '季节气候', str(spot['season']), 'season-card')}
          </div>
        </div>
        <aside class="detail-aside">
          <div class="fact-card"><span>票务标签</span><strong class="{ticket_class(str(spot['ticket_kind']))}">{h(spot['ticket'])}</strong></div>
          <div class="fact-card"><span>当前状态</span><p>{h(spot['status'])}</p></div>
          <div class="fact-card"><span>官方参考</span><a href="{h(spot['source_url'])}" target="_blank" rel="noopener">{h(spot['source_label'])} ↗</a><small>规则可能更新，请在出发当天复核。</small></div>
          {image_credit}
        </aside>
      </div>
    </section>
    <section class="section section-paper">
      <div class="page-width"><div class="section-heading heading-row"><div><p class="eyebrow">NEARBY IDEAS</p><h2>{h(spot['district_primary'])}还可以去</h2></div><a class="text-link" href="../../districts/{h(spot['district_slug'])}/">查看本区全部景点 →</a></div><div class="place-grid related-grid">{related_cards}</div></div>
    </section>
    <nav class="page-turn page-width" aria-label="景点翻页">{prev_link}{next_link}</nav>
    """


def downloads_body() -> str:
    return """
    <section class="compact-hero download-hero"><div class="page-width"><nav class="breadcrumb" aria-label="面包屑"><a href="../index.html">首页</a><span>／</span><span aria-current="page">电子书附件</span></nav><p class="eyebrow eyebrow-warm">OFFLINE EDITIONS</p><h1>电子书附件下载</h1><p>完整 Web / H5 是主要阅读方式；需要离线保存、打印或二次编辑时，可下载 PDF 与 DOCX。</p></div></section>
    <section class="section section-paper"><div class="page-width download-grid">
      <article class="download-card"><span>PDF · 固定版式</span><h2>离线阅读版</h2><p>适合离线阅读、归档与打印；内容与网站同源，但不具备网页筛选功能。</p><a class="button button-primary" href="shenzhen-outdoor-guide.pdf" download="深圳户外景点指南.pdf">下载 PDF</a></article>
      <article class="download-card"><span>DOCX · 可编辑</span><h2>可编辑文档版</h2><p>适合在 Word 或兼容软件中批注、节选和调整个人出行计划。</p><a class="button button-primary" href="shenzhen-outdoor-guide.docx" download="深圳户外景点指南.docx">下载 DOCX</a></article>
    </div></section>
    """


def build() -> None:
    data = json.loads((ROOT / "data/places.json").read_text(encoding="utf-8"))
    data["meta"]["art_count"] = sum(spot["category"] == "美术馆 / 艺术空间" for spot in data["places"])
    places = data["places"]
    place_count = len(places)
    districts = {item["name"]: item for item in data["districts"]}

    write(
        "index.html",
        shell(
            title=f"深圳户外景点指南｜{place_count}个景点完整 Web / H5 版",
            description=f"深圳10区{place_count}个景点完整网页版，逐景点提供介绍、票务、交通、自驾停车、季节气候、开放状态与图片来源。",
            canonical_path="",
            prefix="",
            active="home",
            body=index_body(data),
            body_class="home-page",
            place_count=place_count,
            updated_at=str(data["meta"]["updated_at"]),
        ),
    )
    write(
        "places/index.html",
        shell(
            title=f"全部{place_count}个景点｜深圳户外景点指南",
            description=f"搜索和筛选深圳10区{place_count}个户外景点、博物馆、美术馆、科技馆、古村和小众目的地。",
            canonical_path="places/",
            prefix="../",
            active="places",
            body=catalog_body(data),
            scripts=("catalog.js",),
            body_class="catalog-page",
            place_count=place_count,
            updated_at=str(data["meta"]["updated_at"]),
        ),
    )
    write(
        "downloads/index.html",
        shell(
            title="PDF与DOCX附件｜深圳户外景点指南",
            description="下载《深圳户外景点指南》PDF固定版式和DOCX可编辑附件。",
            canonical_path="downloads/",
            prefix="../",
            active="downloads",
            body=downloads_body(),
            body_class="downloads-page",
            place_count=place_count,
            updated_at=str(data["meta"]["updated_at"]),
        ),
    )

    for district_name, district in districts.items():
        district_spots = [spot for spot in places if spot["district_primary"] == district_name]
        write(
            f'districts/{district["slug"]}/index.html',
            shell(
                title=f'{district_name}{len(district_spots)}个景点完整指南｜深圳户外景点指南',
                description=f'{district["tagline"]}收录{len(district_spots)}个景点，含票务、交通、停车和季节建议。',
                canonical_path=f'districts/{district["slug"]}/',
                prefix="../../",
                active="districts",
                body=district_body(district, district_spots),
                district_slug=str(district["slug"]),
                body_class="district-page",
                place_count=place_count,
                updated_at=str(data["meta"]["updated_at"]),
            ),
        )

    for index, spot in enumerate(places):
        previous = places[index - 1] if index else None
        next_spot = places[index + 1] if index + 1 < len(places) else None
        related = [
            candidate
            for candidate in places
            if candidate["district_primary"] == spot["district_primary"] and candidate["name"] != spot["name"]
        ][:3]
        image_path = spot["image"]["path"]
        json_ld = {
            "@context": "https://schema.org",
            "@type": "TouristAttraction",
            "name": spot["name"],
            "description": spot["intro"],
            "image": f"{BASE_URL}{image_path}",
            "address": {"@type": "PostalAddress", "addressLocality": spot["district_primary"], "streetAddress": spot["area"]},
            "url": f'{BASE_URL}{spot["detail_path"]}',
            "sameAs": spot["source_url"],
        }
        write(
            f'{spot["detail_path"]}index.html',
            shell(
                title=f'{spot["name"]}：票务、交通、停车与季节指南｜深圳户外景点指南',
                description=f'{spot["name"]}完整介绍：{spot["intro"][:70]}',
                canonical_path=str(spot["detail_path"]),
                prefix="../../",
                active="places",
                body=detail_body(spot, previous, next_spot, related),
                image_path=str(image_path),
                district_slug=str(spot["district_slug"]),
                json_ld=json_ld,
                body_class="detail-page",
                place_count=place_count,
                updated_at=str(data["meta"]["updated_at"]),
            ),
        )

    sitemap_paths = ["", "places/", "downloads/"]
    sitemap_paths.extend(f'districts/{item["slug"]}/' for item in data["districts"])
    sitemap_paths.extend(str(spot["detail_path"]) for spot in places)
    sitemap_urls = "".join(
        f"<url><loc>{BASE_URL}{h(path)}</loc><lastmod>{data['meta']['updated_at']}</lastmod></url>" for path in sitemap_paths
    )
    write(
        "sitemap.xml",
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sitemap_urls}</urlset>',
    )
    print(f"built {len(places)} place pages, {len(districts)} district pages and {len(sitemap_paths)} sitemap URLs")


if __name__ == "__main__":
    build()
