from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import Request

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_DE, DAYS_HR, DAYS_HU, DAYS_SI, OpeningHours, sanitise_day

SPAR_SHARED_ATTRIBUTES = {"brand": "Spar", "brand_wikidata": "Q610492"}

BRANDS = {
    "CAFE_CAPPUCCINO": (
        "Cafe Cappuccino",
        {"brand": "Cafe Cappuccino", "brand_wikidata": "Q117317760"},
        Categories.COFFEE_SHOP,
    ),
    "CITY SPAR": ("Spar City", SPAR_SHARED_ATTRIBUTES, Categories.SHOP_CONVENIENCE),
    "DESPAR": ("Despar", SPAR_SHARED_ATTRIBUTES, Categories.SHOP_SUPERMARKET),
    "DESPAR_EXPRESS": ("Despar", SPAR_SHARED_ATTRIBUTES, Categories.SHOP_CONVENIENCE),
    "EUROSPAR": ("Eurospar", SPAR_SHARED_ATTRIBUTES, Categories.SHOP_SUPERMARKET),
    "HIPERMARKET SPAR": (None, SPAR_SHARED_ATTRIBUTES, Categories.SHOP_SUPERMARKET),
    "INTERSPAR": ("Interspar", SPAR_SHARED_ATTRIBUTES, Categories.SHOP_SUPERMARKET),
    "INTERSPAR HIPERMARKET": ("Interspar", SPAR_SHARED_ATTRIBUTES, Categories.SHOP_SUPERMARKET),
    "SPAR EXPRESS": ("Spar Express", SPAR_SHARED_ATTRIBUTES, Categories.SHOP_CONVENIENCE),
    "SPAR GOURMET": ("SPAR Gourmet", SPAR_SHARED_ATTRIBUTES, Categories.SHOP_SUPERMARKET),
    "SPAR MARKET": (None, SPAR_SHARED_ATTRIBUTES, Categories.SHOP_CONVENIENCE),
    "SPAR MARKT": (None, SPAR_SHARED_ATTRIBUTES, Categories.SHOP_CONVENIENCE),
    "SPAR SZUPERMARKET": (None, SPAR_SHARED_ATTRIBUTES, Categories.SHOP_SUPERMARKET),
    "SPAR SUPERMARKET": (None, SPAR_SHARED_ATTRIBUTES, Categories.SHOP_SUPERMARKET),
    "SUPERMARKET SPAR": (None, SPAR_SHARED_ATTRIBUTES, Categories.SHOP_SUPERMARKET),
    "SPAR SUPERMARKT": (None, SPAR_SHARED_ATTRIBUTES, Categories.SHOP_SUPERMARKET),
    "SPAR PARTNER": (None, SPAR_SHARED_ATTRIBUTES, Categories.SHOP_SUPERMARKET),
    "RESTAVRACIJA INTERSPAR": (
        "Interspar Restaurant",
        {"brand": "Interspar Restaurant", "brand_wikidata": "Q15820339"},
        Categories.RESTAURANT,
    ),
    "RESTAURANT": (
        "Interspar Restaurant",
        {"brand": "Interspar Restaurant", "brand_wikidata": "Q15820339"},
        Categories.RESTAURANT,
    ),
}


class SparAspiagSpider(Spider):
    # Spar stores run by ASPIAG: https://www.aspiag.com/en/countries
    # See also https://github.com/alltheplaces/alltheplaces/pull/9379
    name = "spar_aspiag"

    COUNTRIES = [
        {"country": "si", "path": "trgovine", "days": DAYS_SI},
        {"country": "hr", "path": "lokacije", "days": DAYS_HR},
        {"country": "at", "path": "standorte", "days": DAYS_DE},
        {"country": "hu", "path": "uzletek", "days": DAYS_HU},
    ]

    async def start(self) -> AsyncIterator[Request]:
        for config in self.COUNTRIES:
            yield Request(
                f'https://www.spar.{config["country"]}/{config["path"]}/_jcr_content.stores.v2.html',
                cb_kwargs=dict(
                    config=config,
                ),
            )

    def parse(self, response, config):
        for poi in response.json():
            item = DictParser.parse(poi)
            item["opening_hours"] = self.parse_open_hours(poi["shopHours"], config["days"]) or None

            base_url = f'https://www.spar.{config["country"]}/'
            item["website"] = item["ref"] = base_url + poi.get("pageUrl")

            if image_url := poi.get("image"):
                if "defaultlocationbanner.jpg" not in image_url:
                    item["image"] = base_url + image_url

            name, brand, category = BRANDS.get(poi.get("plantType").get("name", "").upper())
            if name:
                item["name"] = name

            if brand:
                item.update(brand)
            else:
                item["brand"] = poi.get("plantType").get("name", "")
                self.crawler.stats.inc_value(f'atp/{self.name}/unknown_brand/{config["country"]}/{brand}')

            if category:
                apply_category(category, item)

            yield item

    def parse_open_hours(self, hours, days: list):
        opening_hours = OpeningHours()
        for interval in hours:
            day = sanitise_day(interval.get("openingHours").get("dayType").title(), days)

            if interval["openingHours"]["from1"]:
                opening_hours.add_range(
                    day=day,
                    open_time=f'{interval["openingHours"]["from1"]["hourOfDay"]}:{interval["openingHours"]["from1"]["minute"]}',
                    close_time=f'{interval["openingHours"]["to1"]["hourOfDay"]}:{interval["openingHours"]["to1"]["minute"]}',
                )

            if interval["openingHours"]["from2"]:
                opening_hours.add_range(
                    day=day,
                    open_time=f'{interval["openingHours"]["from2"]["hourOfDay"]}:{interval["openingHours"]["from2"]["minute"]}',
                    close_time=f'{interval["openingHours"]["to2"]["hourOfDay"]}:{interval["openingHours"]["to2"]["minute"]}',
                )

        return opening_hours
