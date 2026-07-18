#!/usr/bin/env python3
"""Export the reviewed ebook content into the public Web/H5 data contract."""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DISTRICT_SLUGS = {
    "福田区": "futian",
    "罗湖区": "luohu",
    "南山区": "nanshan",
    "盐田区": "yantian",
    "宝安区": "baoan",
    "龙岗区": "longgang",
    "龙华区": "longhua",
    "坪山区": "pingshan",
    "光明区": "guangming",
    "大鹏新区": "dapeng",
}
PROFILE_LABELS = {
    "mountain": "山野步道",
    "coast": "海岸滨水",
    "wetland": "湿地生态",
    "city": "城市公园",
    "waterway": "河湖绿道",
    "museum": "博物馆",
    "art": "美术艺术",
    "science": "科技科普",
    "heritage": "古村人文",
    "family": "亲子田园",
}


def ticket_kind(ticket: str) -> str:
    if ticket.startswith("免费"):
        return "free"
    if ticket.startswith("收费"):
        return "paid"
    if ticket.startswith("暂不开放"):
        return "closed"
    return "reservation"


def reset_source_modules() -> None:
    for name in tuple(sys.modules):
        if name in {"district_places", "place_enrichment", "supplemental_places"} or name.startswith("place_content"):
            del sys.modules[name]


def export(source_dir: Path) -> dict[str, object]:
    source_dir = source_dir.resolve()
    if not (source_dir / "place_enrichment.py").exists():
        raise FileNotFoundError(f"not an ebook source directory: {source_dir}")

    reset_source_modules()
    sys.path.insert(0, str(source_dir))
    try:
        district_places = importlib.import_module("district_places")
        place_enrichment = importlib.import_module("place_enrichment")
    finally:
        sys.path.pop(0)

    image_manifest = json.loads(
        (source_dir / "assets/image_manifest.json").read_text(encoding="utf-8")
    )
    exported_places: list[dict[str, object]] = []
    image_dir = ROOT / "assets/places"
    image_dir.mkdir(parents=True, exist_ok=True)

    for spot in place_enrichment.unique_place_rows():
        name = spot["name"]
        image_record = image_manifest[name]
        image_name = f'{spot["spot_number"]}.jpg'
        source_image = source_dir / image_record["file"]
        target_image = image_dir / image_name
        shutil.copy2(source_image, target_image)

        image = {
            "path": f"assets/places/{image_name}",
            "kind": image_record["kind"],
            "kind_label": "授权实景图" if image_record["kind"] == "real_photo" else "编辑配图·非现场实景",
            "description": image_record["description"],
            "detail_url": image_record.get("detail_url", ""),
            "artist": image_record.get("artist", ""),
            "license": image_record.get("license", ""),
            "license_url": image_record.get("license_url", ""),
        }
        district = spot["district"].split(" / ")[0]
        public_spot = {key: value for key, value in spot.items() if key != "note"}
        exported_places.append(
            {
                **public_spot,
                "highlights": list(spot["highlights"]),
                "district_primary": district,
                "district_slug": DISTRICT_SLUGS[district],
                "profile_label": PROFILE_LABELS[spot["profile_key"]],
                "ticket_kind": ticket_kind(spot["ticket"]),
                "indoor": spot["profile_key"] in {"museum", "art", "science"},
                "detail_path": f'places/{spot["spot_number"]}/',
                "image": image,
            }
        )

    districts = []
    for district in district_places.DISTRICT_ORDER:
        district_spots = [spot for spot in exported_places if spot["district_primary"] == district]
        meta = district_places.DISTRICT_META[district]
        districts.append(
            {
                "name": district,
                "slug": DISTRICT_SLUGS[district],
                "tagline": meta["tagline"],
                "route": meta["route"],
                "small_pick": meta["small_pick"],
                "count": len(district_spots),
            }
        )

    return {
        "meta": {
            "title": "深圳户外景点指南",
            "edition": "2026 年 7 月版",
            "updated_at": "2026-07-18",
            "place_count": len(exported_places),
            "district_count": len(districts),
            "museum_count": sum(spot["profile_key"] == "museum" for spot in exported_places),
            "art_count": sum(spot["category"] == "美术馆 / 艺术空间" for spot in exported_places),
            "real_photo_count": sum(spot["image"]["kind"] == "real_photo" for spot in exported_places),
        },
        "districts": districts,
        "profiles": PROFILE_LABELS,
        "places": exported_places,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "data/places.json")
    args = parser.parse_args()

    payload = export(args.source_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f'exported {payload["meta"]["place_count"]} places, '
        f'{payload["meta"]["district_count"]} districts and '
        f'{payload["meta"]["real_photo_count"]} real photos'
    )


if __name__ == "__main__":
    main()
