# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html
import logging
from datetime import datetime
from enum import Enum
from typing import Iterable

import scrapy

from locations.hours import OpeningHours

logger = logging.getLogger(__name__)


class Feature(scrapy.Item):
    lat = scrapy.Field()
    lon = scrapy.Field()
    geometry = scrapy.Field()
    name = scrapy.Field()
    branch = scrapy.Field()
    addr_full = scrapy.Field()
    housenumber = scrapy.Field()
    street = scrapy.Field()
    street_address = scrapy.Field()
    city = scrapy.Field()
    state = scrapy.Field()
    postcode = scrapy.Field()
    country = scrapy.Field()
    phone = scrapy.Field()
    email = scrapy.Field()
    website = scrapy.Field()
    twitter = scrapy.Field()
    facebook = scrapy.Field()
    opening_hours = scrapy.Field()
    image = scrapy.Field()
    ref = scrapy.Field()
    brand = scrapy.Field()
    brand_wikidata = scrapy.Field()
    operator = scrapy.Field()
    operator_wikidata = scrapy.Field()
    located_in = scrapy.Field()
    located_in_wikidata = scrapy.Field()
    nsi_id = scrapy.Field()
    extras = scrapy.Field()
    spider = scrapy.Field()
    shop = scrapy.Field()
    amenity = scrapy.Field()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self._values.get("extras"):
            self.__setitem__("extras", {})


def get_lat_lon(item: Feature) -> (float, float):
    if geometry := item.get("geometry"):
        if isinstance(geometry, dict):
            if geometry.get("type") == "Point":
                if coords := geometry.get("coordinates"):
                    try:
                        return float(coords[1]), float(coords[0])
                    except (TypeError, ValueError):
                        item["geometry"] = None
    else:
        try:
            return float(item.get("lat")), float(item.get("lon"))
        except (TypeError, ValueError):
            pass
    return None


def set_lat_lon(item: Feature, lat: float, lon: float):
    item.pop("lat", None)
    item.pop("lon", None)
    if lat and lon:
        item["geometry"] = {
            "type": "Point",
            "coordinates": [lon, lat],
        }
    else:
        item["geometry"] = None


class SocialMedia(Enum):
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    MASTODON = "mastodon"
    PINTEREST = "pinterest"
    SNAPCHAT = "snapchat"
    TELEGRAM = "telegram"
    TIKTOK = "tiktok"
    TRIPADVISOR = "tripadvisor"
    TRIP_ADVISOR = TRIPADVISOR
    TWITTER = "twitter"
    VIBER = "viber"
    VK = "vk"
    WHATSAPP = "whatsapp"
    YELP = "yelp"
    YOUTUBE = "youtube"


def get_social_media(item: Feature, service: str | Enum) -> str:
    if isinstance(service, Enum):
        service_str = service.value
    elif isinstance(service, str):
        service_str = service.lower()
    else:
        raise TypeError("string or Enum required")

    if service_str in item.fields:
        return item.get(service_str)
    else:
        return item["extras"].get("contact:{}".format(service_str))


def add_social_media(item: Feature, service: str, account: str):
    """Deprecated, use set_social_media"""
    set_social_media(item, service, account)


def set_social_media(item: Feature, service: str | Enum, account: str):
    if isinstance(service, Enum):
        service_str = service.value
    elif isinstance(service, str):
        service_str = service.lower()
    else:
        raise TypeError("string or Enum required")

    if service_str in item.fields:
        item[service_str] = account
    else:
        item["extras"]["contact:{}".format(service_str)] = account


def set_closed(item: Feature, end_date: datetime = None):
    item["extras"]["end_date"] = end_date.strftime("%Y-%m-%d") if end_date else "yes"


def merge_items(language_dict: dict, main_language: str, matching_key="ref") -> Iterable[Feature]:
    all_item_refs = {language: [ref for ref in items.keys()] for language, items in language_dict.items()}
    for item in language_dict[main_language].values():
        matched_items = {}
        for language, items in language_dict.items():
            if item[matching_key] in items.keys():
                matched_items[language] = items[item[matching_key]]
                all_item_refs[language].remove(item[matching_key])
            else:
                logger.warning(
                    f"No matches found for '{matching_key}': '{item[matching_key]}' in language '{language}'"
                )

        item = get_merged_item(matched_items, main_language, matching_key)
        yield item
    for language, refs in all_item_refs.items():
        if len(refs) > 0:
            logger.warning(f"Failed to match {len(refs)} for language: {language}")
        for ref in refs:
            yield language_dict[language][ref]


KEYS_THAT_SHOULD_MATCH = [
    "lat",
    "lon",
    "geometry",
    "housenumber",
    "postcode",
    "country",
    "image",
    "ref",
    "brand",
    "brand_wikidata",
    "operator",
    "operator_wikidata",
    "located_in",
    "located_in_wikidata",
    "nsi_id",
]

TRANSLATABLE_EXTRA_KEYS = [
    "alt_name",
    "wheelchair:description",
]

TRANSLATABLE_PREFIXES = [
    "website",
    "contact",
]


def get_merged_item(matched_items: dict, main_language: str, matching_key: str) -> dict:
    # Do extras first before we add language keys to it
    item = get_merged_extras(matched_items, main_language, matching_key)

    all_keys = set([key for match in matched_items.values() for key in match.keys()])
    for key, value in {key: item.get(key) for key in all_keys}.items():
        if key == "extras":
            continue
        if all([value == match.get(key) for match in matched_items.values()]):
            continue
        if key == "addr_full":
            for language, match in matched_items.items():
                item["extras"]["addr:full" + language] = match.get(key)
        elif key in ["city", "postcode", "state", "street", "street_address"]:
            for language, match in matched_items.items():
                item["extras"][f"addr:{key}:{language}"] = match.get(key)
        elif key == "opening_hours":
            if isinstance(value, OpeningHours):
                item_oh = value.as_opening_hours()
            else:
                item_oh = value
            match_oh_list = []
            for match in matched_items.values():
                if isinstance(match["opening_hours"], OpeningHours):
                    match_oh_list.append(match["opening_hours"].as_opening_hours())
                else:
                    match_oh_list.append(match["opening_hours"])
            if not all([match_oh == item_oh for match_oh in match_oh_list]):
                logger.warning(
                    f"Opening hours do not match in all items for '{matching_key}': '{item[matching_key]}', using hours from '{main_language}'"
                )
        elif key == "phone":
            matched_phones = [match["phone"] for match in matched_items.values()]
            if not all([value == matched_phone for matched_phone in matched_phones]):
                logger.info(
                    f"Phone numbers do not all match, returning all numbers for '{matching_key}': '{item[matching_key]}'"
                )
                item["phone"] = "; ".join(matched_phones)
        else:
            if key in KEYS_THAT_SHOULD_MATCH:
                logger.warning(f"Key '{key}' does not match in all items")
            for language, match in matched_items.items():
                item["extras"][f"{key}:{language}"] = match.get(key)
    return item


def get_merged_extras(matched_items: dict, main_language: str, matching_key: str) -> dict:
    item = matched_items[main_language]
    extras_keys = set([key for match in matched_items.values() for key in match["extras"].keys()])
    for extras_key, extras_value in {key: item["extras"].get(key) for key in extras_keys}.items():
        if all([extras_value == match["extras"].get(extras_key) for match in matched_items.values()]):
            continue
        if extras_key in TRANSLATABLE_EXTRA_KEYS:
            for language, match in matched_items.items():
                item["extras"][f"{extras_key}:{language}"] = match["extras"].get(extras_key)
        for prefix in TRANSLATABLE_PREFIXES:
            if extras_key.startswith(prefix):
                for language, match in matched_items.items():
                    item["extras"][f"{extras_key}:{language}"] = match["extras"].get(extras_key)
    return item
