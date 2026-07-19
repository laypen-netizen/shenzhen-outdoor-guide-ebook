#!/usr/bin/env python3
"""Export the reviewed ebook content into the public Web/H5 data contract."""

from __future__ import annotations

import argparse
import importlib
import json
import re
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLACE_ID_REGISTRY = ROOT / "data/place_ids.json"
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


def load_stable_place_ids(registry_path: Path, baseline_path: Path | None) -> dict[str, str]:
    source = registry_path if registry_path.exists() else baseline_path
    if source is None or not source.exists():
        raise FileNotFoundError(
            "stable place ID registry is missing; bootstrap it with --id-baseline <historical places.json>"
        )

    payload = json.loads(source.read_text(encoding="utf-8"))
    rows = payload.get("places", [])
    place_ids: dict[str, str] = {}
    used_ids: set[str] = set()
    for row in rows:
        name = row.get("name", "")
        spot_number = row.get("spot_number", "")
        if not name or not re.fullmatch(r"\d{3}", spot_number):
            raise ValueError(f"invalid place ID row in {source}: {row!r}")
        if name in place_ids or spot_number in used_ids:
            raise ValueError(f"duplicate place name or ID in {source}: {row!r}")
        place_ids[name] = spot_number
        used_ids.add(spot_number)
    if not place_ids:
        raise ValueError(f"stable place ID source is empty: {source}")
    return place_ids


def write_stable_place_ids(registry_path: Path, place_ids: dict[str, str]) -> None:
    rows = [
        {"name": name, "spot_number": spot_number}
        for name, spot_number in sorted(place_ids.items(), key=lambda item: int(item[1]))
    ]
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "contract": "Existing public IDs are permanent; newly discovered places receive the next unused ID.",
                "places": rows,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def export(
    source_dir: Path,
    registry_path: Path = PLACE_ID_REGISTRY,
    baseline_path: Path | None = None,
) -> dict[str, object]:
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
    source_places = list(place_enrichment.unique_place_rows())
    stable_ids = load_stable_place_ids(registry_path, baseline_path)
    source_names = {spot["name"] for spot in source_places}
    missing_names = set(stable_ids) - source_names
    if missing_names:
        sample = ", ".join(sorted(missing_names)[:5])
        raise ValueError(f"source removed registered places without an ID migration: {sample}")

    next_id = max(int(spot_number) for spot_number in stable_ids.values()) + 1
    for spot in source_places:
        name = spot["name"]
        if name not in stable_ids:
            stable_ids[name] = f"{next_id:03d}"
            next_id += 1

    exported_places: list[dict[str, object]] = []
    image_dir = ROOT / "assets/places"
    image_dir.mkdir(parents=True, exist_ok=True)

    for spot in source_places:
        name = spot["name"]
        stable_number = stable_ids[name]
        image_record = image_manifest[name]
        image_name = f"{stable_number}.jpg"
        source_image = source_dir / image_record["file"]
        target_image = image_dir / image_name
        shutil.copy2(source_image, target_image)

        description = str(image_record["description"]).strip()
        if image_record["kind"] == "real_photo" and name not in description:
            description = f"{name}实景：{description}"
        image = {
            "path": f"assets/places/{image_name}",
            "kind": image_record["kind"],
            "kind_label": "授权实景图" if image_record["kind"] == "real_photo" else "编辑配图·非现场实景",
            "description": description,
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
                "spot_number": stable_number,
                "highlights": list(spot["highlights"]),
                "district_primary": district,
                "district_slug": DISTRICT_SLUGS[district],
                "profile_label": PROFILE_LABELS[spot["profile_key"]],
                "ticket_kind": ticket_kind(spot["ticket"]),
                "indoor": spot["profile_key"] in {"museum", "art", "science"},
                "detail_path": f"places/{stable_number}/",
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

    payload = {
        "meta": {
            "title": "深圳户外景点指南",
            "edition": "2026 年 7 月版",
            "updated_at": "2026-07-19",
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
    write_stable_place_ids(registry_path, stable_ids)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "data/places.json")
    parser.add_argument("--registry", type=Path, default=PLACE_ID_REGISTRY)
    parser.add_argument(
        "--id-baseline",
        type=Path,
        help="historical places.json used only to bootstrap a missing stable ID registry",
    )
    args = parser.parse_args()

    payload = export(args.source_dir, args.registry, args.id_baseline)
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
