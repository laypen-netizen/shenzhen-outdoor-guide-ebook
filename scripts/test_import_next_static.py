from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from import_next_static import (
    PUBLIC_BASE_URL,
    PUBLIC_PATH,
    SOURCE_ORIGIN,
    home_page,
    sources_page,
    takedown_page,
)


class NextStaticTransformTests(unittest.TestCase):
    def test_home_is_framework_free_and_contains_the_six_demo_guides(self) -> None:
        result = home_page()

        self.assertNotIn("/_next/", result)
        self.assertIn(f'href="{PUBLIC_PATH}next-static.css"', result)
        self.assertIn(f'src="{PUBLIC_PATH}static-app.js"', result)
        self.assertEqual(result.count("data-guide-card"), 6)
        self.assertIn("周末去哪", result)
        self.assertIn("出发前，再核对一次。", result)

    def test_static_navigation_keeps_dynamic_pages_on_vercel(self) -> None:
        result = home_page()

        self.assertIn(f'href="{PUBLIC_PATH}rating/"', result)
        self.assertIn(f'href="{PUBLIC_PATH}source-status/"', result)
        self.assertIn(f'href="{SOURCE_ORIGIN}/places/梧桐山"', result)
        self.assertIn(f'href="{SOURCE_ORIGIN}/creators/bilibili-wutongshan"', result)

    def test_public_metadata_uses_the_github_pages_source_status_route(self) -> None:
        result = sources_page()

        self.assertIn(f'href="{PUBLIC_BASE_URL}source-status/"', result)
        self.assertIn(f'content="{PUBLIC_BASE_URL}source-status/"', result)
        self.assertIn('name="twitter:image"', result)

    def test_takedown_submission_uses_the_vercel_backend(self) -> None:
        result = takedown_page()

        self.assertIn(f'action="{SOURCE_ORIGIN}/api/takedown"', result)
        self.assertIn("GitHub Pages 不运行数据库", result)


if __name__ == "__main__":
    unittest.main()
