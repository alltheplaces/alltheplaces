from copy import deepcopy
from typing import AsyncIterator

import pycountry
from scrapy.http import Request

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import SocialMedia, set_social_media
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address
from locations.spiders.toyota_au import TOYOTA_SHARED_ATTRIBUTES

LEXUS_SHARED_ATTRIBUTES = {"brand": "Lexus", "brand_wikidata": "Q35919"}


class ToyotaEUSpider(JSONBlobSpider):
    name = "toyota_eu"
    BRAND_MAPPING = {"Lexus": LEXUS_SHARED_ATTRIBUTES, "Toyota": TOYOTA_SHARED_ATTRIBUTES}
    locations_key = "dealers"
    custom_settings = {"DOWNLOAD_TIMEOUT": 60}
    SHOP_ATTRIBUTES = ["ShowRoom", "UsedCars", "BusinessCenter"]
    SERVICE_ATTRIBUTES = ["WorkShop", "BodyShop", "PaintShop"]
    all_countries = [country.alpha_2.lower() for country in pycountry.countries]
    exclude_countries = [
        "au",  # toyota_au
        "bf",  # toyota_africa
        "bj",  # toyota_africa
        "br",  # toyota_br
        "bw",  # toyota_sacu
        "cd",  # toyota_africa
        "cf",  # toyota_africa
        "cg",  # toyota_africa
        "ci",  # toyota_africa
        "cm",  # toyota_africa
        "gm",  # toyota_africa
        "gn",  # toyota_africa
        "gq",  # toyota_africa
        "gw",  # toyota_africa
        "ke",  # toyota_africa
        "lr",  # toyota_africa
        "ls",  # toyota_sacu
        "mg",  # toyota_africa
        "ml",  # toyota_africa
        "mr",  # toyota_africa
        "mz",  # toyota_africa
        "na",  # toyota_sacu
        "ne",  # toyota_africa
        "ng",  # toyota_africa
        "nz",  # toyota_nz
        "rw",  # toyota_africa
        "sl",  # toyota_africa
        "sn",  # toyota_africa
        "sz",  # toyota_sacu
        "td",  # toyota_africa
        "tg",  # toyota_africa
        "tw",  # toyota_tw
        "ug",  # toyota_africa
        "us",  # toyota_us
        "za",  # toyota_sacu
        "zw",  # toyota_africa
    ]

    async def start(self) -> AsyncIterator[Request]:
        available_countries = [c for c in self.all_countries if c not in self.exclude_countries]
        for brand in ["toyota", "lexus"]:
            for country in available_countries:
                yield Request(
                    f"https://kong-proxy-intranet.toyota-europe.com/dxp/dealers/api/{brand}/{country}/en/all",
                    callback=self.parse,
                )

    def pre_process_data(self, feature):
        feature["geo"] = feature["address"].pop("geo", None)
        feature["email"] = feature.pop("eMail")

    def post_process_item(self, item, response, location):
        if match := self.BRAND_MAPPING.get(location["brand"]):
            item["brand"] = match["brand"]
            item["brand_wikidata"] = match["brand_wikidata"]
        else:
            self.crawler.stats.inc_value(f"atp/{self.name}/unknown_brand/{location['brand']}")
        item["country"] = location["country"]
        item["street_address"] = clean_address(
            [location["address"].get("address1"), location["address"].get("address")]
        )
        set_social_media(item, SocialMedia.WHATSAPP, location.get("whatsapp"))
        services = [i["service"] for i in location["services"]]
        # Some locations have no services listed, so fall back to shop=car
        if not services:
            services.append("ShowRoom")
        shop_match = next((attr for attr in self.SHOP_ATTRIBUTES if attr in services), None)
        service_match = next((attr for attr in self.SERVICE_ATTRIBUTES if attr in services), None)
        if shop_match:
            shop_item = deepcopy(item)
            shop_item["ref"] = f"{item['ref']}-SHOP"
            shop_item["opening_hours"] = self.parse_hours(location["openingDays"], shop_match)
            apply_category(Categories.SHOP_CAR, shop_item)
            yield shop_item
        if service_match:
            service_item = deepcopy(item)
            service_item["ref"] = f"{item['ref']}-SERVICE"
            service_item["opening_hours"] = self.parse_hours(location["openingDays"], service_match)
            apply_category(Categories.SHOP_CAR_REPAIR, service_item)
            yield service_item
        if "PartsShop" in services and not shop_match and not service_match:
            parts_item = deepcopy(item)
            parts_item["ref"] = f"{item['ref']}-PARTS"
            parts_item["opening_hours"] = self.parse_hours(location["openingDays"], "PartsShop")
            apply_category(Categories.SHOP_CAR_PARTS, parts_item)
            yield parts_item

    def parse_hours(self, schedule: list[dict], service: str) -> OpeningHours:
        oh = OpeningHours()
        for day in schedule:
            if day["originalService"] == service:
                for hours in day["hours"]:
                    oh.add_ranges_from_string(
                        f"{day['startDayCode']}-{day['endDayCode']} {hours['startTime']}-{hours['endTime']}"
                    )
        return oh
