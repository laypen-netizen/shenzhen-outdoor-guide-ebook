#!/usr/bin/env python3
"""Verify the static ebook site without third-party dependencies."""

from __future__ import annotations

import hashlib
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_HASHES = {
    "downloads/shenzhen-outdoor-guide.pdf": (
        "fda410a403f8fc91adcaa6febdadcbc644b545ab8b927652d3d1b3f0d1f5c32b"
    ),
    "downloads/shenzhen-outdoor-guide.docx": (
        "d54f14db6638adfd54f7bd11fc683a45039630e50cc97e6c5511205d5bfd6e96"
    ),
}
REQUIRED_TEXT = (
    "229 个景点",
    "深圳十区",
    "68",
    "20",
    "自驾停车",
    "季节与气候匹配",
    "授权实景图",
)


class AssetParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.assets: set[str] = set()
        self.language: str | None = None
        self.title_count = 0
        self.description_count = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "html":
            self.language = values.get("lang")
        if tag == "title":
            self.title_count += 1
        if tag == "meta" and values.get("name") == "description":
            self.description_count += 1
        for key in ("href", "src"):
            value = values.get(key)
            if value:
                self.assets.add(value)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_local_asset(value: str) -> Path | None:
    split = urlsplit(value)
    if split.scheme or split.netloc or value.startswith("#"):
        return None
    clean_path = unquote(split.path)
    if clean_path in ("", "./"):
        return ROOT / "index.html"
    if clean_path.startswith("/shenzhen-outdoor-guide-ebook/"):
        clean_path = clean_path.removeprefix("/shenzhen-outdoor-guide-ebook/")
    elif clean_path.startswith("/"):
        return None
    return ROOT / clean_path


def main() -> None:
    index = ROOT / "index.html"
    markup = index.read_text(encoding="utf-8")
    parser = AssetParser()
    parser.feed(markup)

    errors: list[str] = []
    if parser.language != "zh-CN":
        errors.append("index.html must declare lang=zh-CN")
    if parser.title_count != 1:
        errors.append("index.html must contain exactly one title")
    if parser.description_count != 1:
        errors.append("index.html must contain one meta description")
    if "<iframe" in markup:
        errors.append("PDF iframe must be inserted on demand, not loaded in initial HTML")

    for phrase in REQUIRED_TEXT:
        if phrase not in markup:
            errors.append(f"missing required copy: {phrase}")

    for value in sorted(parser.assets):
        target = resolve_local_asset(value)
        if target is not None and not target.exists():
            errors.append(f"missing linked asset: {value}")

    for relative, expected in EXPECTED_HASHES.items():
        path = ROOT / relative
        if not path.exists():
            errors.append(f"missing ebook file: {relative}")
            continue
        actual = sha256(path)
        if actual != expected:
            errors.append(f"hash mismatch for {relative}: {actual}")

    if errors:
        raise SystemExit("\n".join(f"ERROR: {error}" for error in errors))

    print(
        "site verification: ok\n"
        f"local assets checked: {len(parser.assets)}\n"
        "ebook hashes: ok\n"
        "lazy PDF loading: ok"
    )


if __name__ == "__main__":
    main()
