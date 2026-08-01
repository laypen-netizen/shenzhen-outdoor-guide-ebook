from __future__ import annotations

import sys
import re
import unittest
import json
import inspect
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from export_from_ebook import allocate_stable_place_ids
from build_site import (
    district_body,
    ensure_responsive_place_images,
    index_body,
    place_card,
)
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
    def test_district_boundaries_ticket_count_and_dynamic_status_are_explicit(self) -> None:
        data = json.loads((ROOT / "data/places.json").read_text(encoding="utf-8"))
        dapeng = [place for place in data["places"] if place["district_slug"] == "dapeng"]

        trail = next(place for place in data["places"] if place["name"] == "阳台山环线")
        self.assertEqual(trail["district_primary"], "龙华区")
        self.assertEqual(trail["district_slug"], "longhua")
        self.assertIn("跨龙华、宝安和南山", trail["area"])

        self.assertEqual(sum(place["ticket_kind"] == "paid" for place in dapeng), 5)
        self.assertEqual(sum(place["name"] == "东山寺" for place in dapeng), 1)

        qiniang = next(place for place in data["places"] if place["name"] == "七娘山")
        self.assertIn("临时", qiniang["status"])
        self.assertIn("天气", qiniang["status"])
        self.assertNotIn("全线封闭", qiniang["status"])

        bay = next(place for place in data["places"] if place["name"] == "深圳湾公园")
        self.assertIn("福田区", bay["area"])
        self.assertIn("南山区", bay["area"])

        wutong = next(
            place for place in data["places"] if place["name"] == "梧桐山风景名胜区"
        )
        self.assertIn("盐田", wutong["area"])
        self.assertIn("龙岗", wutong["area"])

    def test_district_page_reports_explicit_paid_count(self) -> None:
        data = json.loads((ROOT / "data/places.json").read_text(encoding="utf-8"))
        district = next(item for item in data["districts"] if item["slug"] == "dapeng")
        spots = [place for place in data["places"] if place["district_slug"] == "dapeng"]

        markup = district_body(district, spots)

        self.assertIn("票务概览：明确标注收费 5 个", markup)

    def test_homepage_labels_museum_count_as_site_collection(self) -> None:
        data = json.loads((ROOT / "data/places.json").read_text(encoding="utf-8"))

        markup = index_body(data)

        self.assertIn("家已收录博物馆", markup)

    def test_shenzhen_natural_history_museum_is_in_pingshan_public_data(self) -> None:
        data = json.loads((ROOT / "data/places.json").read_text(encoding="utf-8"))
        museum = next(
            place for place in data["places"] if place["name"] == "深圳自然博物馆"
        )

        self.assertEqual(data["meta"]["place_count"], 353)
        self.assertEqual(data["meta"]["museum_count"], 69)
        self.assertEqual(
            next(district for district in data["districts"] if district["name"] == "坪山区")["count"],
            19,
        )
        self.assertEqual(museum["district_primary"], "坪山区")
        self.assertEqual(museum["spot_number"], "331")
        self.assertEqual(museum["detail_path"], "places/331/")
        self.assertIn("沙壆站", museum["transport"])
        self.assertIn("步行约8—10分钟", museum["transport"])
        self.assertIn("M151", museum["transport"])
        self.assertIn("D53", museum["transport"])
        self.assertIn("深圳自然博物馆停车场", museum["parking"])
        self.assertIn("官方公告", museum["status"])
        self.assertIn("工作日、周末均可前往", museum["ticket"])
        self.assertIn("成人普通票80元", museum["ticket"])
        self.assertIn("优待票60元", museum["ticket"])
        self.assertIn("免票人群也需", museum["ticket"])
        self.assertIn("预约0元门票", museum["ticket"])

    def test_a_level_attractions_are_appended_without_duplicate_names(self) -> None:
        data = json.loads((ROOT / "data/places.json").read_text(encoding="utf-8"))
        expected = {
            "世界之窗": ("南山区", "332"),
            "锦绣中华民俗文化村": ("南山区", "333"),
            "欢乐谷": ("南山区", "334"),
            "欢乐海岸": ("南山区", "335"),
            "青青世界": ("南山区", "336"),
            "深圳市野生动物园": ("南山区", "337"),
            "观澜山水田园旅游文化园": ("龙华区", "338"),
            "地王观光·深港之窗": ("罗湖区", "339"),
            "光明红木文化小镇": ("光明区", "340"),
        }

        self.assertEqual(len(data["places"]), data["meta"]["place_count"])
        names = [place["name"] for place in data["places"]]
        self.assertEqual(len(names), len(set(names)))
        for name, (district, spot_number) in expected.items():
            with self.subTest(name=name):
                place = next(place for place in data["places"] if place["name"] == name)
                self.assertEqual(place["district_primary"], district)
                self.assertEqual(place["spot_number"], spot_number)
                self.assertEqual(place["detail_path"], f"places/{spot_number}/")
                self.assertEqual(place["image"]["kind"], "editorial_illustration")
                self.assertEqual(place["source_url"], "https://wtl.sz.gov.cn/ggfw/lyl/jqjdylb/index.html")

        self.assertEqual(data["meta"]["museum_count"], 69)
        self.assertEqual(data["meta"]["real_photo_count"], 69)

    def test_official_a_level_aliases_are_mapped_without_new_duplicate_pages(self) -> None:
        data = json.loads((ROOT / "data/places.json").read_text(encoding="utf-8"))
        names = {place["name"] for place in data["places"]}
        places = {place["name"]: place for place in data["places"]}
        official_source = "https://wtl.sz.gov.cn/ggfw/lyl/jqjdylb/index.html"

        self.assertEqual(len(names), data["meta"]["place_count"])
        self.assertNotIn("观澜湖旅游休闲度假区", names)
        self.assertNotIn("东山鹿嘴旅游区", names)
        self.assertNotIn("水底山旅游度假区", names)

        guanlan = places["观澜湖生态运动公社"]
        self.assertIn("观澜湖旅游休闲度假区", guanlan["intro"])
        self.assertEqual(guanlan["source_url"], official_source)
        self.assertIn("观澜湖旅游休闲度假区", guanlan["source_label"])

        luzui = places["鹿嘴山庄海岸"]
        self.assertIn("东山鹿嘴旅游区", luzui["intro"])
        self.assertEqual(luzui["source_url"], official_source)
        self.assertIn("东山鹿嘴旅游区", luzui["source_label"])

        for name in ("世界之窗", "锦绣中华民俗文化村", "欢乐谷", "欢乐海岸"):
            with self.subTest(name=name):
                self.assertIn(name, names)

    def test_missing_official_art_spaces_are_appended_without_alias_duplicates(self) -> None:
        data = json.loads((ROOT / "data/places.json").read_text(encoding="utf-8"))
        expected = {
            "旭生美术馆": ("宝安区", "341"),
            "一雍美术馆": ("宝安区", "342"),
            "越众历史影像馆": ("罗湖区", "343"),
            "祥山艺术馆": ("龙岗区", "344"),
            "泓岭美术馆": ("福田区", "345"),
            "袁机美术馆": ("罗湖区", "346"),
            "鳌湖美术馆": ("龙华区", "347"),
            "禾花美术馆": ("龙岗区", "348"),
            "天空美术馆": ("福田区", "349"),
            "至美术馆": ("宝安区", "350"),
            "梅沙艺术中心": ("盐田区", "351"),
            "徐悲鸿文化艺术中心": ("南山区", "352"),
            "华润大厦艺术中心美术馆": ("南山区", "353"),
        }

        self.assertEqual(data["meta"]["place_count"], 353)
        self.assertEqual(data["meta"]["art_count"], 33)
        names = [place["name"] for place in data["places"]]
        self.assertEqual(len(names), len(set(names)))
        for name, (district, spot_number) in expected.items():
            with self.subTest(name=name):
                place = next(place for place in data["places"] if place["name"] == name)
                self.assertEqual(place["district_primary"], district)
                self.assertEqual(place["spot_number"], spot_number)
                self.assertEqual(place["category"], "美术馆 / 艺术空间")
                self.assertEqual(place["detail_path"], f"places/{spot_number}/")
                self.assertEqual(place["image"]["kind"], "editorial_illustration")
                self.assertEqual(
                    place["source_url"],
                    "https://wtl.sz.gov.cn/ggfw/whl/msgylb/index_2.html",
                )

        self.assertIn("海上世界", names)
        self.assertNotIn("海上世界文化艺术中心", names)

    def test_shenzhen_natural_history_museum_uses_one_submitted_image(self) -> None:
        data = json.loads((ROOT / "data/places.json").read_text(encoding="utf-8"))
        museum = next(
            place for place in data["places"] if place["name"] == "深圳自然博物馆"
        )

        self.assertEqual(museum["image"]["kind"], "user_provided_photo")
        self.assertEqual(museum["image"]["path"], "assets/places/331.jpg")
        self.assertNotIn("gallery", museum)
        self.assertIn("用户提供", museum["image"]["kind_label"])

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
