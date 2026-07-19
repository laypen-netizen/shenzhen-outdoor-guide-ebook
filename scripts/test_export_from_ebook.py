from __future__ import annotations

import sys
import re
import unittest
import json
import inspect
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from export_from_ebook import allocate_stable_place_ids
from build_site import ensure_responsive_place_images, index_body, place_card
import verify_site
from verify_site import PageParser


ROOT = Path(__file__).resolve().parent.parent


class StablePlaceIdTests(unittest.TestCase):
    def test_new_places_append_without_renumbering_existing_places(self) -> None:
        existing = {"莲花山公园": "001", "香蜜公园": "002", "南湾郊野公园": "317"}

        allocated = allocate_stable_place_ids(
            existing,
            ["香蜜公园", "新增小众公园", "莲花山公园", "另一个新景点"],
        )

        self.assertEqual(allocated["莲花山公园"], "001")
        self.assertEqual(allocated["香蜜公园"], "002")
        self.assertEqual(allocated["南湾郊野公园"], "317")
        self.assertEqual(allocated["新增小众公园"], "318")
        self.assertEqual(allocated["另一个新景点"], "319")


class MobileInteractionContractTests(unittest.TestCase):
    def test_mobile_filter_controls_meet_44px_touch_target(self) -> None:
        styles = (ROOT / "styles.css").read_text(encoding="utf-8")

        for selector in (".check-label", ".mobile-filter-button"):
            with self.subTest(selector=selector):
                blocks = re.findall(
                    rf"{re.escape(selector)}\s*\{{(?P<body>[^}}]+)\}}",
                    styles,
                )
                self.assertTrue(blocks, f"missing CSS block for {selector}")
                heights = [
                    int(value)
                    for block in blocks
                    for value in re.findall(r"min-height:\s*(\d+)px", block)
                ]
                self.assertTrue(heights, f"missing min-height for {selector}")
                self.assertGreaterEqual(min(heights), 44)


class PublicationBoundaryTests(unittest.TestCase):
    def test_local_article_captures_are_git_ignored(self) -> None:
        ignored_paths = {
            line.strip()
            for line in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }

        self.assertIn("sources/", ignored_paths)


class StaticSiteRegressionTests(unittest.TestCase):
    def test_featured_places_must_all_be_present(self) -> None:
        data = json.loads((ROOT / "data/places.json").read_text(encoding="utf-8"))
        data["places"] = [
            place for place in data["places"] if place["name"] != "莲花山公园"
        ]

        with self.assertRaisesRegex(ValueError, "featured places are missing"):
            index_body(data)

    def test_card_summary_does_not_render_the_full_detail_intro(self) -> None:
        intro = "深" * 96
        markup = place_card(
            {
                "name": "测试景点",
                "area": "测试片区",
                "district_primary": "福田区",
                "profile_key": "city",
                "profile_label": "城市公园",
                "ticket_kind": "free",
                "ticket": "免费",
                "indoor": False,
                "spot_number": "999",
                "detail_path": "places/999/",
                "intro": intro,
                "image": {
                    "path": "assets/places/999.jpg",
                    "kind": "editorial",
                    "kind_label": "主题编辑配图",
                },
            },
            "",
        )

        self.assertNotIn(intro, markup)
        self.assertIn("深" * 60 + "…", markup)

    def test_parser_collects_all_srcset_candidates(self) -> None:
        parser = PageParser()
        parser.feed(
            '<img src="assets/places/720/001.jpg" '
            'srcset="assets/places/720/001.jpg 720w, assets/places/960/001.jpg 960w">'
        )

        self.assertEqual(
            parser.assets,
            {"assets/places/720/001.jpg", "assets/places/960/001.jpg"},
        )

    def test_parser_collects_required_social_metadata(self) -> None:
        parser = PageParser()
        parser.feed(
            '<meta name="description" content="页面说明">'
            '<meta property="og:title" content="页面标题">'
            '<meta property="og:description" content="页面说明">'
            '<meta property="og:url" content="https://example.com/guide/">'
            '<meta property="og:image" content="https://example.com/guide/assets/share.png">'
            '<link rel="canonical" href="https://example.com/guide/">'
        )

        self.assertEqual(parser.descriptions, ["页面说明"])
        self.assertEqual(parser.canonical_urls, ["https://example.com/guide/"])
        self.assertEqual(
            parser.og_values,
            {
                "og:title": ["页面标题"],
                "og:description": ["页面说明"],
                "og:url": ["https://example.com/guide/"],
                "og:image": ["https://example.com/guide/assets/share.png"],
            },
        )

    def test_browser_check_waits_for_cdp_connections_to_close(self) -> None:
        browser_check = (ROOT / "scripts/browser_check.mjs").read_text(encoding="utf-8")

        self.assertIn("await session.close()", browser_check)

    def test_browser_check_closes_each_created_debug_target(self) -> None:
        browser_check = (ROOT / "scripts/browser_check.mjs").read_text(encoding="utf-8")

        self.assertIn("async function closeTarget(targetId)", browser_check)
        self.assertIn("await closeTarget(target.id)", browser_check)
        self.assertIn("siteTargetsBefore", browser_check)

    def test_browser_check_has_a_catalog_transfer_budget(self) -> None:
        browser_check = (ROOT / "scripts/browser_check.mjs").read_text(encoding="utf-8")

        self.assertIn('check.path === "/places/" && check.initialTransferredBytes', browser_check)

    def test_responsive_asset_builder_uses_the_referenced_place_images(self) -> None:
        parameters = inspect.signature(ensure_responsive_place_images).parameters

        self.assertIn("places", parameters)

    def test_verifier_does_not_stat_a_missing_source_image(self) -> None:
        verifier = (ROOT / "scripts/verify_site.py").read_text(encoding="utf-8")

        self.assertIn(
            "elif image_path.is_file() and responsive.stat().st_size >= image_path.stat().st_size",
            verifier,
        )

    def test_verifier_reports_existing_asset_counts(self) -> None:
        verifier = (ROOT / "scripts/verify_site.py").read_text(encoding="utf-8")

        self.assertIn("existing_detail_pages", verifier)
        self.assertIn("existing_image_paths", verifier)

    def test_local_original_image_backups_are_not_publishable_place_assets(self) -> None:
        self.assertTrue(hasattr(verify_site, "published_place_images"))
        self.assertNotIn(
            ROOT / "assets/places/001_original.jpg",
            verify_site.published_place_images(),
        )

    def test_local_original_image_backups_are_git_ignored(self) -> None:
        ignored_paths = {
            line.strip()
            for line in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }

        self.assertIn("assets/places/*_original.jpg", ignored_paths)
        self.assertIn("assets/places/**/*_original.jpg", ignored_paths)


if __name__ == "__main__":
    unittest.main()
