# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html
from datetime import datetime
from enum import Enum

import scrapy


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
