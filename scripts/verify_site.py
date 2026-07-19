#!/usr/bin/env python3
"""Verify complete Web/H5 coverage, links, assets and ebook attachments."""

from __future__ import annotations

import hashlib
import html
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_BASE_URL = "https://laypen-netizen.github.io/shenzhen-outdoor-guide-ebook/"
PLACE_ID_REGISTRY = ROOT / "data/place_ids.json"
RESPONSIVE_PLACE_WIDTHS = (720, 960)
REQUIRED_OG_PROPERTIES = ("og:title", "og:description", "og:url", "og:image")
EXPECTED_HASHES = {
    "downloads/shenzhen-outdoor-guide.pdf": "fb858ceaa1752816ee101acae263c7ec5660649f502243436c76c6b7aa5b5c18",
    "downloads/shenzhen-outdoor-guide.docx": "6b47dfae0924ddfb6bb76add24686cc492377500c8a81220a1bcae990b5ec2b4",
}
DETAIL_LABELS = (
    "核心看点",
    "适合谁",
    "第一次怎样看",
    "票务标签",
    "公共交通",
    "自驾停车",
    "季节气候",
    "当前状态",
    "官方参考",
)


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.assets: set[str] = set()
        self.language: str | None = None
        self.title_count = 0
        self.h1_count = 0
        self.viewport_count = 0
        self.descriptions: list[str] = []
        self.canonical_urls: list[str] = []
        self.og_values: dict[str, list[str]] = {
            property_name: [] for property_name in REQUIRED_OG_PROPERTIES
        }

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "html":
            self.language = values.get("lang")
        elif tag == "title":
            self.title_count += 1
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "meta":
            if values.get("name") == "viewport":
                self.viewport_count += 1
            elif values.get("name") == "description":
                self.descriptions.append(values.get("content") or "")
            property_name = values.get("property") or ""
            if property_name in self.og_values:
                self.og_values[property_name].append(values.get("content") or "")
        elif tag == "link" and "canonical" in (values.get("rel") or "").split():
            self.canonical_urls.append(values.get("href") or "")
        for key in ("href", "src"):
            value = values.get(key)
            if value:
                self.assets.add(value)
        srcset = values.get("srcset")
        if srcset:
            for candidate in srcset.split(","):
                value = candidate.strip().split(maxsplit=1)[0]
                if value:
                    self.assets.add(value)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_local_asset(page: Path, value: str) -> Path | None:
    split = urlsplit(value)
    if split.scheme or split.netloc or value.startswith(("#", "mailto:", "tel:")):
        return None
    clean_path = unquote(split.path)
    if not clean_path:
        return None
    if clean_path.startswith("/shenzhen-outdoor-guide-ebook/"):
        target = ROOT / clean_path.removeprefix("/shenzhen-outdoor-guide-ebook/")
    elif clean_path.startswith("/"):
        return None
    else:
        target = page.parent / clean_path
    target = target.resolve()
    if ROOT not in target.parents and target != ROOT:
        raise ValueError(f"asset escapes site root: {value}")
    if clean_path.endswith("/") or target.is_dir():
        target /= "index.html"
    return target


def resolve_published_asset(value: str) -> Path | None:
    if not value.startswith(PUBLIC_BASE_URL):
        return None
    relative = unquote(urlsplit(value).path.removeprefix(urlsplit(PUBLIC_BASE_URL).path))
    if not relative:
        return None
    target = (ROOT / relative).resolve()
    if ROOT not in target.parents and target != ROOT:
        raise ValueError(f"published asset escapes site root: {value}")
    return target


def expected_canonical_url(relative: Path) -> str:
    if relative == Path("index.html"):
        return PUBLIC_BASE_URL
    if relative.name == "index.html":
        return f"{PUBLIC_BASE_URL}{relative.parent.as_posix()}/"
    return f"{PUBLIC_BASE_URL}{relative.as_posix()}"


def responsive_place_image_path(path: str, width: int) -> Path:
    relative = Path(path)
    return ROOT / relative.parent / str(width) / relative.name


def published_place_images() -> set[Path]:
    return {
        path
        for path in (ROOT / "assets/places").glob("*.jpg")
        if not path.name.endswith("_original.jpg")
    }


def verify_page(path: Path, errors: list[str]) -> None:
    markup = path.read_text(encoding="utf-8")
    parser = PageParser()
    parser.feed(markup)
    relative = path.relative_to(ROOT)

    if parser.language != "zh-CN":
        errors.append(f"{relative}: missing lang=zh-CN")
    if parser.title_count != 1:
        errors.append(f"{relative}: expected one title, got {parser.title_count}")
    if parser.h1_count != 1:
        errors.append(f"{relative}: expected one h1, got {parser.h1_count}")
    if parser.viewport_count != 1:
        errors.append(f"{relative}: expected one viewport meta")
    if "file://" in markup:
        errors.append(f"{relative}: contains file URL")
    if path.name != "404.html":
        if len(parser.descriptions) != 1 or not parser.descriptions[0].strip():
            errors.append(f"{relative}: expected one non-empty meta description")
        canonical = expected_canonical_url(relative)
        if parser.canonical_urls != [canonical]:
            errors.append(f"{relative}: canonical URL missing or incorrect")
        for property_name in REQUIRED_OG_PROPERTIES:
            values = parser.og_values[property_name]
            if len(values) != 1 or not values[0].strip():
                errors.append(f"{relative}: expected one non-empty {property_name}")
        if parser.og_values["og:url"] != [canonical]:
            errors.append(f"{relative}: og:url missing or incorrect")
        for value in parser.og_values["og:image"]:
            try:
                target = resolve_published_asset(value)
            except ValueError as exc:
                errors.append(f"{relative}: {exc}")
                continue
            if target is not None and not target.exists():
                errors.append(f"{relative}: missing published og:image {value}")

    for value in parser.assets:
        try:
            target = resolve_local_asset(path, value)
        except ValueError as exc:
            errors.append(f"{relative}: {exc}")
            continue
        if target is not None and not target.exists():
            errors.append(f"{relative}: missing linked asset {value}")


def main() -> None:
    data = json.loads((ROOT / "data/places.json").read_text(encoding="utf-8"))
    places = data["places"]
    districts = data["districts"]
    expected_places = data["meta"]["place_count"]
    errors: list[str] = []

    if not PLACE_ID_REGISTRY.exists():
        errors.append("missing stable place ID registry: data/place_ids.json")
    else:
        registry = json.loads(PLACE_ID_REGISTRY.read_text(encoding="utf-8"))
        registry_rows = registry.get("places", [])
        registry_map = {row["name"]: row["spot_number"] for row in registry_rows}
        exported_map = {spot["name"]: spot["spot_number"] for spot in places}
        if len(registry_rows) != len(registry_map):
            errors.append("stable place ID registry contains duplicate names")
        if len(set(registry_map.values())) != len(registry_map):
            errors.append("stable place ID registry contains duplicate IDs")
        if registry_map != exported_map:
            errors.append("exported place IDs do not match the stable registry")

    if len(places) != expected_places:
        errors.append(f"place count: expected {expected_places}, got {len(places)}")
    if len({spot["name"] for spot in places}) != expected_places:
        errors.append("place names are not unique")
    if len({spot["spot_number"] for spot in places}) != expected_places:
        errors.append("place numbers are not unique")
    if len(districts) != 10:
        errors.append(f"district count: expected 10, got {len(districts)}")
    museum_count = sum(spot["profile_key"] == "museum" for spot in places)
    art_count = sum(spot["category"] == "美术馆 / 艺术空间" for spot in places)
    if data["meta"]["museum_count"] != museum_count or museum_count < 68:
        errors.append(f"museum count invalid: {data['meta']['museum_count']} / {museum_count}")
    if data["meta"]["art_count"] != art_count or art_count < 20:
        errors.append(f"official art-space count invalid: {data['meta']['art_count']} / {art_count}")

    catalog_markup = (ROOT / "places/index.html").read_text(encoding="utf-8")
    catalog_ids = re.findall(r'data-place-id="(\d{3})"', catalog_markup)
    if len(catalog_ids) != expected_places or len(set(catalog_ids)) != expected_places:
        errors.append(f"catalog card coverage invalid: {len(catalog_ids)} cards")
    for phrase in ("关键词", "区域", "主题类型", "票务", "只看室内场馆", "只看我的收藏"):
        if phrase not in catalog_markup:
            errors.append(f"catalog missing filter: {phrase}")

    home_markup = (ROOT / "index.html").read_text(encoding="utf-8")
    if "iframe" in home_markup.lower():
        errors.append("homepage must not embed the PDF")
    for phrase in ("完整 Web / H5", f"{expected_places} 个景点", f"浏览全部 {expected_places} 个景点", "十区各有自己的深圳"):
        if phrase not in home_markup:
            errors.append(f"homepage missing Web/H5 promise: {phrase}")

    detail_paths: list[Path] = []
    existing_detail_pages: list[Path] = []
    image_paths: set[Path] = set()
    existing_image_paths: set[Path] = set()
    for spot in places:
        detail = ROOT / spot["detail_path"] / "index.html"
        detail_paths.append(detail)
        if not detail.is_file():
            errors.append(f'missing detail page: {spot["name"]}')
        else:
            existing_detail_pages.append(detail)
            markup = detail.read_text(encoding="utf-8")
            if html.escape(spot["name"]) not in markup:
                errors.append(f'{spot["name"]}: name missing from detail')
            if html.escape(spot["intro"]) not in markup:
                errors.append(f'{spot["name"]}: intro missing from detail')
            for label in DETAIL_LABELS:
                if label not in markup:
                    errors.append(f'{spot["name"]}: missing detail label {label}')
            if 'width="1200" height="540"' not in markup:
                errors.append(f'{spot["name"]}: detail image dimensions do not match exported card')
            if 'srcset="' not in markup or "/720/" not in markup or "/960/" not in markup:
                errors.append(f'{spot["name"]}: detail image is missing responsive srcset variants')
            if spot["image"]["kind_label"] not in markup:
                errors.append(f'{spot["name"]}: missing image-kind disclosure')
            if spot["image"]["kind"] == "real_photo":
                for field in ("description", "detail_url", "artist", "license", "license_url"):
                    value = spot["image"].get(field, "")
                    if not value:
                        errors.append(f'{spot["name"]}: real photo missing {field}')
                    elif html.escape(value, quote=True) not in markup:
                        errors.append(f'{spot["name"]}: real photo attribution missing from detail ({field})')
            elif not spot["image"].get("description"):
                errors.append(f'{spot["name"]}: editorial image missing description')
        image_path = ROOT / spot["image"]["path"]
        image_paths.add(image_path)
        if not image_path.is_file():
            errors.append(f'{spot["name"]}: missing image')
        else:
            existing_image_paths.add(image_path)
        for width in RESPONSIVE_PLACE_WIDTHS:
            responsive = responsive_place_image_path(str(spot["image"]["path"]), width)
            if not responsive.exists():
                errors.append(f'{spot["name"]}: missing responsive image {responsive.relative_to(ROOT)}')
            elif image_path.is_file() and responsive.stat().st_size >= image_path.stat().st_size:
                errors.append(
                    f'{spot["name"]}: responsive image {responsive.relative_to(ROOT)} is not smaller than source'
                )

    if len(existing_detail_pages) != expected_places:
        errors.append(f"detail page count invalid: {len(existing_detail_pages)}")
    if len(image_paths) != expected_places:
        errors.append(f"image mapping count invalid: {len(image_paths)}")
    if len(existing_image_paths) != expected_places:
        errors.append(f"place image count invalid: {len(existing_image_paths)}")
    actual_images = published_place_images()
    if actual_images != image_paths:
        errors.append("assets/places does not exactly match place image mapping")

    for district in districts:
        page = ROOT / "districts" / district["slug"] / "index.html"
        if not page.exists():
            errors.append(f'missing district page: {district["name"]}')
        elif f'{district["name"]}全部 {district["count"]} 个景点' not in page.read_text(encoding="utf-8"):
            errors.append(f'{district["name"]}: district count copy missing')

    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    sitemap_count = sitemap.count("<url>")
    expected_sitemap_urls = expected_places + len(districts) + 3
    if sitemap_count != expected_sitemap_urls:
        errors.append(f"sitemap URLs: expected {expected_sitemap_urls}, got {sitemap_count}")

    html_pages = sorted(ROOT.glob("*.html"))
    html_pages += sorted((ROOT / "places").glob("**/index.html"))
    html_pages += sorted((ROOT / "districts").glob("**/index.html"))
    html_pages += [ROOT / "downloads/index.html"]
    unique_html_pages = sorted(set(html_pages))
    expected_update_label = f"更新于 {data['meta']['updated_at']}"
    for page in unique_html_pages:
        verify_page(page, errors)
        markup = page.read_text(encoding="utf-8")
        if page != ROOT / "404.html" and expected_update_label not in markup:
            errors.append(f"{page.relative_to(ROOT)}: stale or missing update date")
        card_image_count = markup.count('class="place-card-image"')
        if card_image_count and markup.count('width="1200" height="540"') < card_image_count:
            errors.append(
                f"{page.relative_to(ROOT)}: place-card images do not match the exported 20:9 card ratio"
            )
        if card_image_count and markup.count('srcset="') < card_image_count:
            errors.append(f"{page.relative_to(ROOT)}: place-card images are missing responsive srcset")

    for relative, expected in EXPECTED_HASHES.items():
        path = ROOT / relative
        if not path.exists():
            errors.append(f"missing ebook attachment: {relative}")
        elif sha256(path) != expected:
            errors.append(f"ebook hash mismatch: {relative}")

    if errors:
        raise SystemExit("\n".join(f"ERROR: {error}" for error in errors[:100]))

    print(
        json.dumps(
            {
                "status": "ok",
                "places": len(places),
                "districts": len(districts),
                "detail_pages": len(existing_detail_pages),
                "place_images": len(existing_image_paths),
                "html_pages_checked": len(unique_html_pages),
                "catalog_cards": len(catalog_ids),
                "sitemap_urls": sitemap_count,
                "museums": data["meta"]["museum_count"],
                "art_spaces": data["meta"]["art_count"],
                "real_photos": data["meta"]["real_photo_count"],
                "ebook_hashes": "ok",
                "errors": [],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
