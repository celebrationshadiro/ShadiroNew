from __future__ import annotations

from typing import Literal


GroupName = Literal["SERVICE", "RENTAL", "GROCERY"]


SERVICE_CATEGORIES = [
    "photography",
    "catering",
    "decoration",
    "makeup",
    "lighting",
    "videography",
]

RENTAL_CATEGORIES = [
    "venue",
    "tent_furniture",
]

GROCERY_CATEGORIES = [
    "grocery",
]


_ALIASES: dict[str, str] = {
    "decorator": "decoration",
    "decor": "decoration",
    "makeup_artist": "makeup",
    "mehendi": "makeup",
    "venue_hall": "venue",
    "tent": "tent_furniture",
    "furniture_rental": "tent_furniture",
    "wholesale_grocery": "grocery",
}


def normalize_category_slug(category_slug: str) -> str:
    key = str(category_slug or "").strip().lower().replace(" ", "_")
    return _ALIASES.get(key, key)


def get_group(category_slug: str) -> GroupName:
    normalized = normalize_category_slug(category_slug)
    if normalized in SERVICE_CATEGORIES:
        return "SERVICE"
    if normalized in RENTAL_CATEGORIES:
        return "RENTAL"
    if normalized in GROCERY_CATEGORIES:
        return "GROCERY"
    raise ValueError(f"Unsupported category_slug: {category_slug}")


def is_service_category(category_slug: str) -> bool:
    return get_group(category_slug) == "SERVICE"

