#!/usr/bin/env python3
"""Build a GitHub Pages static front end for the reconstructed Next.js guide."""

from __future__ import annotations

import html
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NEXT_ROOT = ROOT.parent / "shenzhen-outdoor-guide"
SOURCE_ORIGIN = "https://shenzhen-outdoor-guide.vercel.app"
PUBLIC_BASE_URL = "https://laypen-netizen.github.io/shenzhen-outdoor-guide-ebook/"
PUBLIC_PATH = "/shenzhen-outdoor-guide-ebook/"

PLATFORM_LABELS = {
    "xiaohongshu": "小红书",
    "douyin": "抖音",
    "bilibili": "B站",
    "wechat_channels": "微信视频号",
    "wechat_official_account": "微信公众号",
    "toutiao": "今日头条",
}

PLATFORM_URLS = {
    "xiaohongshu": "https://www.xiaohongshu.com/",
    "douyin": "https://www.douyin.com/",
    "bilibili": "https://www.bilibili.com/",
    "wechat_channels": "https://channels.weixin.qq.com/",
    "wechat_official_account": "https://mp.weixin.qq.com/",
    "toutiao": "https://www.toutiao.com/",
}

GUIDES = [
    {
        "key": "wutongshan",
        "platform": "bilibili",
        "title": "梧桐山公共交通徒步路线（演示索引）",
        "creator": "山野记录员（演示）",
        "creator_slug": "bilibili-wutongshan",
        "published": "2026-07-10",
        "places": [("梧桐山", "罗湖区"), ("仙湖植物园", "罗湖区")],
        "tags": ["徒步登山", "进阶", "全天", "徒步爱好者", "公共交通"],
        "score": 88,
        "grade": "A",
    },
    {
        "key": "shenzhen-bay",
        "platform": "wechat_official_account",
        "title": "深圳湾亲子散步路线（演示索引）",
        "creator": "周末亲子局（演示）",
        "creator_slug": "wechat_official_account-shenzhen-bay",
        "published": "2026-07-08",
        "places": [("深圳湾公园", "南山区")],
        "tags": ["公园散步", "亲子活动", "轻松", "1–2 小时", "亲子家庭", "公共交通", "停车"],
        "score": 84,
        "grade": "B",
    },
    {
        "key": "dapeng",
        "platform": "douyin",
        "title": "大鹏山海线路注意事项（演示索引）",
        "creator": "山海边界（演示）",
        "creator_slug": "douyin-dapeng",
        "published": "2026-07-06",
        "places": [("大鹏半岛国家地质公园", "大鹏新区")],
        "tags": ["海边沙滩", "摄影打卡", "适中", "全天", "游客"],
        "score": 79,
        "grade": "B",
    },
    {
        "key": "lianhuashan",
        "platform": "wechat_channels",
        "title": "莲花山轻松散步记录（演示索引）",
        "creator": "城市散步计划（演示）",
        "creator_slug": "wechat_channels-lianhuashan",
        "published": "2026-07-05",
        "places": [("莲花山公园", "福田区")],
        "tags": ["公园散步", "轻松", "1–2 小时", "亲子家庭", "公共交通"],
        "score": 76,
        "grade": "B",
    },
    {
        "key": "maluanshan",
        "platform": "xiaohongshu",
        "title": "马峦山周末路线清单（演示索引）",
        "creator": "深圳周末出逃（演示）",
        "creator_slug": "xiaohongshu-maluanshan",
        "published": "2026-07-03",
        "places": [("马峦山郊野公园", "坪山区")],
        "tags": ["徒步登山", "适中", "半天", "徒步爱好者", "停车"],
        "score": 71,
        "grade": "B",
    },
    {
        "key": "qianhai",
        "platform": "toutiao",
        "title": "前海石公园傍晚散步（演示索引）",
        "creator": "城市户外观察（演示）",
        "creator_slug": "toutiao-qianhai",
        "published": "2026-07-01",
        "places": [("前海石公园", "南山区")],
        "tags": ["公园散步", "摄影打卡", "宠物友好", "轻松", "1–2 小时", "游客", "公共交通"],
        "score": None,
        "grade": None,
    },
]

SOURCE_POLICIES = [
    ("xiaohongshu", "未确认可用于第三方搜索和读取任意博主公开笔记的通用官方 API。", ["https://open.xiaohongshu.com/document/api", "https://agora.xiaohongshu.com/doc", "https://redopen.xiaohongshu.com/"]),
    ("douyin", "作者视频能力要求应用权限、账号绑定或用户授权，不能用于任意博主全网发现。", ["https://developer.open-douyin.com/docs/resource/zh-CN/dop/develop/openapi/list/", "https://developer.open-douyin.com/docs/resource/zh-CN/mini-app/develop/server/reach-marketing/mount/self_mount/get-user-video-list"]),
    ("bilibili", "开放能力面向已授权或已关联 UP 主，未确认任意作者内容聚合能力。", ["https://openhome.bilibili.com/doc", "https://openhome.bilibili.com/agreement/developer-service"]),
    ("wechat_channels", "未确认面向第三方的任意视频号内容搜索、列表或聚合 API。", ["https://developers.weixin.qq.com/doc/channels/"]),
    ("wechat_official_account", "素材接口用于管理已授权公众号自身素材，不是任意公众号文章搜索接口。", ["https://developers.weixin.qq.com/doc/offiaccount/Asset_Management/Get_materials_list.html"]),
    ("toutiao", "本轮未找到可验证的任意作者文章搜索或聚合开放 API。", ["https://mp.toutiao.com/profile_v4/"]),
]


def escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def route_url(route: str) -> str:
    if route == "/":
        return PUBLIC_BASE_URL
    return f"{PUBLIC_BASE_URL}{route.strip('/')}/"


def page_head(title: str, description: str, route: str) -> str:
    canonical = route_url(route)
    image = f"{PUBLIC_BASE_URL}assets/shenzhen-nine-scenes-1200.webp"
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <meta name="description" content="{escape(description)}">
  <link rel="canonical" href="{canonical}">
  <meta property="og:type" content="website">
  <meta property="og:locale" content="zh_CN">
  <meta property="og:site_name" content="深圳户外指南">
  <meta property="og:title" content="{escape(title)}">
  <meta property="og:description" content="{escape(description)}">
  <meta property="og:url" content="{canonical}">
  <meta property="og:image" content="{image}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{escape(title)}">
  <meta name="twitter:description" content="{escape(description)}">
  <meta name="twitter:image" content="{image}">
  <link rel="icon" href="{PUBLIC_PATH}assets/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="{PUBLIC_PATH}next-static.css">
</head>"""


def site_header() -> str:
    return f"""<body>
<a class="skip-link" href="#main-content">跳到主要内容</a>
<header class="site-header">
  <div class="site-shell header-inner">
    <a class="brand" href="{PUBLIC_PATH}" aria-label="深圳户外指南首页">
      <span class="brand-mark" aria-hidden="true"><svg viewBox="0 0 36 36" role="img"><circle cx="18" cy="18" r="16"></circle><path d="m13 23 4-11 6 7-10 4Z"></path></svg></span>
      <span><strong>深圳户外指南</strong><small>SHENZHEN FIELD INDEX</small></span>
    </a>
    <nav class="main-nav" aria-label="主导航">
      <a href="{PUBLIC_PATH}#guides">找攻略</a><a href="{PUBLIC_PATH}#places">找地点</a><a href="{PUBLIC_PATH}rating/">评级规则</a><a href="{PUBLIC_PATH}source-status/">来源状态</a><a href="{PUBLIC_PATH}takedown/">纠错 / 下架</a>
    </nav>
  </div>
</header>"""


def site_footer() -> str:
    return f"""<footer class="site-footer"><div class="site-shell footer-grid">
  <div><strong>深圳户外指南</strong><p>只做索引、分类与透明评级，不生产攻略，不完整转载。</p></div>
  <nav aria-label="页脚导航"><a href="{PUBLIC_PATH}source-status/">平台能力</a><a href="{PUBLIC_PATH}rating/">评级规则</a><a href="{PUBLIC_PATH}takedown/">纠错与下架</a></nav>
  <p class="footer-note">原内容权利归原作者及来源平台所有。</p>
</div></footer><script src="{PUBLIC_PATH}static-app.js" defer></script></body></html>"""


def filter_form() -> str:
    district_options = "".join(f"<option>{escape(item)}</option>" for item in ["罗湖区", "福田区", "南山区", "盐田区", "宝安区", "龙岗区", "龙华区", "坪山区", "光明区", "大鹏新区"])
    activity_options = "".join(f"<option>{escape(item)}</option>" for item in ["公园散步", "徒步登山", "绿道骑行", "露营野餐", "海边沙滩", "亲子活动", "摄影打卡", "宠物友好"])
    platform_options = "".join(f'<option value="{key}">{label}</option>' for key, label in PLATFORM_LABELS.items())
    return f"""<form class="filter-form" action="{PUBLIC_PATH}" method="get" role="search">
  <div class="filter-primary">
    <label class="search-field"><span class="sr-only">搜索地点、攻略或博主</span><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6"></circle><path d="m16 16 4 4"></path></svg><input name="q" type="search" enterkeyhint="search" placeholder="搜公园、山海、路线或博主"></label>
    <label><span>区域</span><select name="district"><option value="">全深圳</option>{district_options}</select></label>
    <label><span>玩法</span><select name="activity"><option value="">全部类型</option>{activity_options}</select></label>
    <button type="submit">开始筛选 <span aria-hidden="true">→</span></button>
  </div>
  <details class="advanced-filters"><summary><span>更多筛选条件</span><small>难度、耗时、人群、设施、来源与时间</small></summary>
    <div class="advanced-filter-grid">
      <label><span>难度</span><select name="difficulty"><option value="">全部难度</option><option>轻松</option><option>适中</option><option>进阶</option></select></label>
      <label><span>耗时</span><select name="duration"><option value="">不限耗时</option><option>1–2 小时</option><option>半天</option><option>全天</option></select></label>
      <label><span>适合</span><select name="audience"><option value="">所有人群</option><option>亲子家庭</option><option>徒步爱好者</option><option>游客</option></select></label>
      <label><span>设施</span><select name="feature"><option value="">不限设施</option><option>公共交通</option><option>停车</option></select></label>
      <label><span>来源</span><select name="platform"><option value="">全部平台</option>{platform_options}</select></label>
      <label><span>发布时间</span><select name="days"><option value="">不限时间</option><option value="30">近 30 天</option><option value="90">近 90 天</option><option value="365">近一年</option></select></label>
      <label><span>最近核查</span><select name="checked"><option value="">不限核查时间</option><option value="7">近 7 天</option><option value="30">近 30 天</option></select></label>
      <label><span>排序</span><select name="sort"><option value="quality">高质量优先</option><option value="latest">最新收录</option></select></label>
    </div>
  </details>
</form>"""


def score_badge(guide: dict[str, object]) -> str:
    if guide["score"] is None:
        return '<div class="score-badge unrated" aria-label="暂未评级"><strong>—</strong><span>待评级</span></div>'
    grade = escape(guide["grade"])
    return f'<div class="score-badge grade-{grade.lower()}" aria-label="攻略质量 {guide["score"]} 分，{grade} 级"><strong>{grade}</strong><span>{guide["score"]} 分 · 演示</span></div>'


def guide_card(guide: dict[str, object]) -> str:
    places = guide["places"]
    primary_place = places[0][0]
    districts = "|".join(sorted({place[1] for place in places}))
    tags = guide["tags"]
    shown_tags = "".join(f"<span>{escape(tag)}</span>" for tag in tags[:4])
    search = " ".join([guide["title"], guide["creator"], *(place[0] for place in places), *tags])
    score_details = ""
    if guide["score"] is not None:
        dimensions = [("完整度", "演示评分：结构化字段覆盖", "demo.fields"), ("时效性", "演示评分：发布时间字段", "demo.publishedAt"), ("实用性", "演示评分：实用标签字段", "demo.tags"), ("可验证性", "演示评分：来源字段", "demo.source")]
        score_details = "<ul>" + "".join(f"<li><strong>{label}</strong><span>{reason}<small>依据字段：{evidence}</small></span></li>" for label, reason, evidence in dimensions) + "</ul>"
    else:
        score_details = "<p>合法取得的数据不足，当前不评分。</p>"
    published_label = guide["published"][5:].replace("-", "/")
    return f"""<article class="guide-card platform-{guide['platform']}" data-guide-card data-search="{escape(search.lower())}" data-district="{escape(districts)}" data-tags="{escape('|'.join(tags))}" data-platform="{guide['platform']}" data-published="{guide['published']}" data-checked="2026-07-16" data-score="{guide['score'] if guide['score'] is not None else -1}">
  <div class="guide-card-visual" aria-hidden="true"><span class="visual-platform">{PLATFORM_LABELS[guide['platform']]}</span><strong>{escape(primary_place[:4])}</strong><span class="visual-index">SZ / {escape(guide['key'][:4].upper())}</span></div>
  <div class="guide-card-body">
    <div class="card-meta-row"><span>{published_label} 发布</span><span>07/16 核查</span><span class="demo-label">演示数据</span></div>
    <h3>{escape(guide['title'])}</h3>
    <p class="creator-line">来自 <a href="{SOURCE_ORIGIN}/creators/{escape(guide['creator_slug'])}">{escape(guide['creator'])}</a></p>
    <p class="excerpt muted">未保存原文摘录，仅展示结构化索引。</p>
    <div class="tag-row" aria-label="攻略标签">{shown_tags}</div>
    <details class="score-details"><summary>查看评级依据</summary>{score_details}</details>
    <div class="card-footer-row">{score_badge(guide)}<div class="card-actions"><a href="{SOURCE_ORIGIN}/places/{escape(primary_place)}">地点详情</a><a class="source-button" href="{PLATFORM_URLS[guide['platform']]}" target="_blank" rel="noopener noreferrer nofollow" aria-label="前往平台首页（演示）：{escape(guide['title'])}">平台首页（演示） <span aria-hidden="true">↗</span></a></div></div>
  </div>
</article>"""


def safety_notice() -> str:
    return f"""<aside class="safety-notice" aria-labelledby="safety-notice-title"><span class="safety-marker" aria-hidden="true">!</span><div><p class="section-index">TRAIL CHECK / 出发前复核</p><h2 id="safety-notice-title">出发前，再核对一次。</h2><p>攻略是历史索引，不是实时路况。请以管理方公告、天气预警、潮汐和现场管控为准，并根据自身能力准备装备。</p></div><div class="safety-links"><a href="{PUBLIC_PATH}source-status/">核对来源边界</a><a href="{PUBLIC_PATH}rating/">了解评级规则</a></div></aside>"""


def home_page() -> str:
    cards = "".join(guide_card(guide) for guide in GUIDES)
    place_rows: list[tuple[str, str, int]] = []
    for guide in GUIDES:
        for name, district in guide["places"]:
            existing = next((row for row in place_rows if row[0] == name), None)
            if existing is None:
                place_rows.append((name, district, 1))
    places = "".join(
        f'<a class="place-tile" href="{SOURCE_ORIGIN}/places/{escape(name)}"><span class="place-number">{index:02d}</span><div><small>{district}</small><strong>{name}</strong><span>{count} 条攻略索引</span></div><span class="place-arrow" aria-hidden="true">↗</span></a>'
        for index, (name, district, count) in enumerate(place_rows, start=1)
    )
    return page_head("深圳户外指南｜跨平台户外攻略索引", "按地点、玩法、难度和来源平台查找深圳户外攻略，本站只做结构化索引并跳转原平台。", "/") + site_header() + f"""
<main id="main-content">
  <section class="explorer-hero"><div class="site-shell explorer-grid"><div class="explorer-main">
    <p class="eyebrow"><span>FIELD INDEX 01</span> 深圳户外攻略聚合</p><h1>周末去哪，<br>先查别人走过的路。</h1><p class="hero-copy">跨平台找到近期攻略，只看结构化索引，原内容回原平台。</p>
    {filter_form()}
    <div class="quick-filters" aria-label="快捷筛选"><span>快速找：</span><a href="{PUBLIC_PATH}?activity=徒步登山#guides">徒步登山</a><a href="{PUBLIC_PATH}?activity=亲子活动#guides">亲子活动</a><a href="{PUBLIC_PATH}?activity=海边沙滩#guides">看海</a><a href="{PUBLIC_PATH}?feature=公共交通#guides">地铁公交</a></div>
  </div><aside class="field-status" aria-label="索引状态"><div class="contour-lines" aria-hidden="true"></div><p class="status-kicker">INDEX STATUS</p><strong>06</strong><span>条演示索引</span><dl><div><dt>来源</dt><dd>6 个平台</dd></div><div><dt>接入</dt><dd>IMPORT ONLY</dd></div><div><dt>日更</dt><dd>04:30 CST</dd></div></dl><a href="{PUBLIC_PATH}source-status/">查看平台能力边界 <span aria-hidden="true">↗</span></a></aside></div></section>
  <div class="demo-notice"><div class="site-shell"><strong>当前为合规 MVP 演示数据</strong><span>未接入任何平台凭据；页面不代表真实抓取或真实博主评级。</span></div></div>
  <section class="site-shell content-section" id="guides"><div class="section-heading"><div><p class="section-index">01 / 攻略索引</p><h2 data-result-heading>高质量攻略</h2></div><div class="result-count"><strong data-result-count>6</strong><span> 条结果</span><a data-clear-filters href="{PUBLIC_PATH}#guides" hidden>清除筛选</a></div></div><div class="guide-grid" data-guide-grid>{cards}</div><div class="empty-state" data-empty-state hidden><span aria-hidden="true">⌁</span><h3>暂时没有匹配结果</h3><p>减少一个筛选条件，或查看全部演示索引。</p><a href="{PUBLIC_PATH}#guides">清除筛选</a></div></section>
  <div class="safety-band"><div class="site-shell">{safety_notice()}</div></div>
  <section class="place-section" id="places"><div class="site-shell"><div class="section-heading light-heading"><div><p class="section-index">02 / 地点目录</p><h2>按区域翻地图</h2></div><p>每个地点只聚合已关联攻略，不补写未经验证的信息。</p></div><div class="place-grid">{places}</div></div></section>
</main>""" + site_footer()


def rating_page() -> str:
    dimensions = [("01", "信息完整度", 30, "var(--lime)", "路线、交通、耗时、难度、预约、费用与注意事项等字段是否有明确依据。"), ("02", "内容时效性", 30, "var(--coral)", "发布时间、最近复核时间，以及开放、预约或路线信息是否仍然有效。"), ("03", "实用信息密度", 25, "var(--sky)", "可执行的信息占比；不把情绪表达、画面精美程度或跨平台播放量当成实用性。"), ("04", "来源可验证性", 15, "var(--sand)", "作者、原链接、发布时间和评分依据是否完整、可回到原平台核对。")]
    rows = "".join(f'<article style="--dimension-color:{color}"><span>{number}</span><div><h2>{name}</h2><p>{detail}</p></div><strong>{score}<small>分</small></strong></article>' for number, name, score, color, detail in dimensions)
    return page_head("攻略质量评级规则｜深圳户外指南", "深圳户外指南的透明攻略质量评分维度、等级和数据不足规则。", "/rating") + site_header() + f"""<main id="main-content" class="text-page rating-page"><div class="site-shell narrow-shell"><header class="text-hero"><p class="eyebrow"><span>QUALITY SCORE</span> 规则版本 2026-07-16 · 评分对象是攻略，不是景点</p><h1>100 分，<br>每一分都要有出处。</h1><p>评级帮助用户判断“这篇攻略是否值得点开”，不会替用户判断一个公园或景点好不好玩。</p></header><section class="score-dimensions">{rows}</section><section class="grade-scale"><div><strong>A</strong><span>85–100</span><small>高质量</small></div><div><strong>B</strong><span>70–84</span><small>信息较完整</small></div><div><strong>C</strong><span>55–69</span><small>可作参考</small></div><div><strong>D</strong><span>0–54</span><small>信息有限</small></div><div class="unrated"><strong>—</strong><span>数据不足</span><small>暂未评级</small></div></section><section class="rating-rules"><h2>三条硬规则</h2><ol><li><span>1</span><div><strong>没有证据，不打分</strong><p>任一维度缺少理由或证据字段，整篇攻略显示“暂未评级”。</p></div></li><li><span>2</span><div><strong>不同平台，不比热度</strong><p>点赞、播放、收藏只能在平台内作为辅助信号，不能直接跨平台相加。</p></div></li><li><span>3</span><div><strong>人工修改，要留原因</strong><p>人工覆盖自动评分时，系统保存修改分数、原因和时间。</p></div></li></ol></section></div></main>""" + site_footer()


def sources_page() -> str:
    rows = []
    for index, (platform, limitation, urls) in enumerate(SOURCE_POLICIES, start=1):
        links = "".join(f'<a href="{url}" target="_blank" rel="noopener noreferrer">官方依据 {source_index} ↗</a>' for source_index, url in enumerate(urls, start=1))
        rows.append(f'<article><span class="policy-number">{index:02d}</span><div><div class="policy-title"><h2>{PLATFORM_LABELS[platform]}</h2><span>import-only</span></div><p>{limitation}</p><div class="evidence-links">{links}</div></div></article>')
    return page_head("平台来源与接入状态｜深圳户外指南", "查看深圳户外指南对各内容平台的官方能力核实依据和当前接入边界。", "/source-status") + site_header() + f"""<main id="main-content" class="text-page"><div class="site-shell narrow-shell"><header class="text-hero"><p class="eyebrow"><span>SOURCE POLICY</span> 核实于 2026-07-16</p><h1>六个平台，<br>先把“能不能接”说清楚。</h1><p>公开网页可访问不等于允许自动采集。当前无平台凭据、无创作者授权，所以六个平台全部以 <code>import-only</code> 运行。</p></header><section class="policy-explainer" aria-label="状态说明"><div><strong>LIVE</strong><p>官方能力、应用审核、授权和凭据全部具备后才能启用。</p></div><div class="active"><strong>IMPORT ONLY</strong><p>运营者提交公开链接，系统只校验并保存许可范围内元数据。</p></div><div><strong>DISABLED</strong><p>适配器不得执行发现、请求或更新。</p></div></section><section class="policy-list">{''.join(rows)}</section><aside class="rule-callout"><strong>升级规则</strong><p>平台状态变化时，先更新能力矩阵和数据库中的 <code>source_policies</code>，再启用适配器。每日任务里的 <code>skipped</code> 永远不能记成采集成功。</p></aside></div></main>""" + site_footer()


def takedown_page() -> str:
    return page_head("纠错与下架｜深圳户外指南", "匿名提交深圳户外指南中的错误、失效或侵权索引复核请求。", "/takedown") + site_header() + f"""<main id="main-content" class="text-page takedown-page"><div class="site-shell narrow-shell"><header class="text-hero"><p class="eyebrow"><span>CORRECTION DESK</span> 匿名提交，不收集联系方式</p><h1>发现错误、失效或侵权索引，<br>请直接告诉我们。</h1><p>表单只记录来源链接和处理原因，不要求姓名、电话或邮箱。原平台内容不会被本站修改。</p></header><div class="rule-callout"><strong>服务边界</strong><p>GitHub Pages 不运行数据库。提交将安全转交至深圳户外指南的 Vercel 服务端处理。</p></div><form class="takedown-form" action="{SOURCE_ORIGIN}/api/takedown" method="post"><label><span>需要处理的原平台链接</span><input name="sourceUrl" type="url" inputmode="url" required placeholder="https://..."></label><label><span>原因</span><textarea name="reason" required minlength="10" maxlength="1000" rows="7" placeholder="例如：原作者已删除；地点关联错误；未获许可展示封面……"></textarea></label><label class="honeypot" aria-hidden="true">网站<input name="website" tabindex="-1" autocomplete="off"></label><div class="form-consent"><span aria-hidden="true">✓</span><p>提交即表示该请求仅用于本站索引纠错或下架复核。请勿填写个人隐私或凭据。</p></div><button type="submit">提交复核请求 <span aria-hidden="true">→</span></button></form></div></main>""" + site_footer()


def build_css() -> str:
    source = (NEXT_ROOT / "src/app/globals.css").read_text(encoding="utf-8")
    source = source.replace('@import "tailwindcss";\n', "")
    reset = """html { line-height: 1.5; -webkit-text-size-adjust: 100%; scroll-behavior: smooth; }
h1, h2, h3, h4, p, figure, blockquote, dl, dd { margin: 0; }
ol, ul { margin: 0; padding: 0; }
img, svg { display: block; max-width: 100%; }
[hidden] { display: none !important; }
"""
    return reset + source


def write_page(route: str, markup: str) -> None:
    target = ROOT / "index.html" if route == "/" else ROOT / route.strip("/") / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(markup, encoding="utf-8")


def update_sitemap() -> None:
    sitemap_path = ROOT / "sitemap.xml"
    sitemap = sitemap_path.read_text(encoding="utf-8")
    sitemap = sitemap.replace(
        f"<url><loc>{PUBLIC_BASE_URL}sources/</loc><lastmod>2026-07-19</lastmod></url>",
        "",
    )
    additions = []
    for route in ("rating", "source-status", "takedown"):
        url = f"{PUBLIC_BASE_URL}{route}/"
        if f"<loc>{url}</loc>" not in sitemap:
            additions.append(f"<url><loc>{url}</loc><lastmod>2026-07-19</lastmod></url>")
    if additions:
        sitemap = sitemap.replace("</urlset>", f"{''.join(additions)}</urlset>")
    sitemap_path.write_text(sitemap, encoding="utf-8")


def main() -> None:
    if not (NEXT_ROOT / "src/app/page.tsx").exists():
        raise SystemExit(f"missing Next.js source project: {NEXT_ROOT}")
    (ROOT / "next-static.css").write_text(build_css(), encoding="utf-8")
    write_page("/", home_page())
    write_page("/rating", rating_page())
    write_page("/source-status", sources_page())
    write_page("/takedown", takedown_page())
    update_sitemap()
    print("built static Next.js guide shell: /, /rating/, /source-status/, /takedown/")


if __name__ == "__main__":
    main()
