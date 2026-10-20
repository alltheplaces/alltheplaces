import re
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider

CATEGORIES = [
    # Shell branded stations are collected by the shell spider
    (r"Shell", None),
    (r"Tankstelle|Tankautomat", Categories.FUEL_STATION),
    (r"Werkst", Categories.SHOP_CAR_REPAIR),
    (r"Autohaus", Categories.SHOP_CAR),
    (r"Bau|Garten", Categories.SHOP_DOITYOURSELF),
    (r"Agrar|Technik|TECHNIK|Steyr Center", Categories.SHOP_AGRARIAN),
    (r"Reifen", Categories.SHOP_TYRES),
    (r"Elektrotechnik", Categories.SHOP_ELECTRONICS),
    (
        r"Verwaltung|Zentrale|Silo|Online|Mühle|Mischfutter|Energie|Edelstahl"
        r"|\bArena\b|\bLager |GmbH|eGen|\bWein|\bSPAR|\bSpar",
        None,
    ),
]


class LagerhausATSpider(SitemapSpider, StructuredDataSpider):
    name = "lagerhaus_at"
    item_attributes = {"brand": "Lagerhaus", "brand_wikidata": "Q1232873"}
    sitemap_urls = ["https://lagerhaus.at/sitemap/index.xml"]
    sitemap_rules = [("/standort/", "parse_sd")]
    sitemap_follow = ["locations"]
    wanted_types = ["LocalBusiness"]
    time_format = "%H:%M:%S"
    search_for_twitter = False
    search_for_facebook = False
    search_for_image = False

    def pre_process_data(self, ld_data: dict, **kwargs: Any) -> None:
        ld_data["openingHoursSpecification"] = [
            rule for rule in ld_data.get("openingHoursSpecification", []) if "validFrom" not in rule
        ]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        name = item.pop("name")
        if "geschlossen" in name:
            return
        for pattern, category in CATEGORIES:
            if re.search(pattern, name):
                if not category:
                    return
                apply_category(category, item)
                break
        else:
            apply_category(Categories.SHOP_DOITYOURSELF, item)
        item["branch"] = re.sub(r"^RGO\||\bLagerhaus\b-?", "", name).strip(" -")
        item.pop("facebook", None)
        item.pop("image", None)
        yield item
