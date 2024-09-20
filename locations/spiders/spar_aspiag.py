import scrapy
from scrapy.http.request import Request

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import DAYS_DE, DAYS_HR, DAYS_HU, DAYS_SI, OpeningHours, sanitise_day

SPAR_SHARED_ATTRIBUTES = {
    "brand": "Spar",
    "brand_wikidata": "Q610492",
    "extras": Categories.SHOP_SUPERMARKET.value,
}


class SparAspiagSpider(scrapy.Spider):
    # Spar stores run by ASPIAG: https://www.aspiag.com/en/countries
    # See also https://github.com/alltheplaces/alltheplaces/pull/9379
    name = "spar_aspiag"

    BRANDS = {
        "CAFE_CAPPUCCINO": {
            "brand": "Cafe Cappuccino",
            "brand_wikidata": "Q15820339",
            "extras": Categories.COFFEE_SHOP.value,
        },
        "CITY SPAR": {"brand": "Spar City", "brand_wikidata": "Q610492", "extras": Categories.SHOP_CONVENIENCE.value},
        "DESPAR": {"brand": "Despar", "brand_wikidata": "Q610492", "extras": Categories.SHOP_SUPERMARKET.value},
        "DESPAR_EXPRESS": {"brand": "Despar", "brand_wikidata": "Q610492", "extras": Categories.SHOP_SUPERMARKET.value},
        "EUROSPAR": {"brand": "Eurospar", "brand_wikidata": "Q12309283", "extras": Categories.SHOP_SUPERMARKET.value},
        "HIPERMARKET SPAR": SPAR_SHARED_ATTRIBUTES,
        "INTERSPAR": {"brand": "Interspar", "brand_wikidata": "Q15820339", "extras": Categories.SHOP_SUPERMARKET.value},
        "INTERSPAR HIPERMARKET": {
            "brand": "Interspar",
            "brand_wikidata": "Q15820339",
            "extras": Categories.SHOP_SUPERMARKET.value,
        },
        "SPAR EXPRESS": {
            "brand": "Spar Express",
            "brand_wikidata": "Q610492",
            "extras": Categories.SHOP_CONVENIENCE.value,
        },
        "SPAR GOURMET": {
            "brand": "SPAR Gourmet",
            "brand_wikidata": "Q610492",
            "extras": Categories.SHOP_SUPERMARKET.value,
        },
        "SPAR MARKET": {"brand": "Spar", "brand_wikidata": "Q610492", "extras": Categories.SHOP_CONVENIENCE.value},
        "SPAR MARKT": {"brand": "Spar", "brand_wikidata": "Q610492", "extras": Categories.SHOP_CONVENIENCE.value},
        "SPAR SZUPERMARKET": SPAR_SHARED_ATTRIBUTES,
        "SPAR SUPERMARKET": SPAR_SHARED_ATTRIBUTES,
        "SUPERMARKET SPAR": SPAR_SHARED_ATTRIBUTES,
        "SPAR SUPERMARKT": SPAR_SHARED_ATTRIBUTES,
        "SPAR PARTNER": SPAR_SHARED_ATTRIBUTES,
        "RESTAVRACIJA INTERSPAR": {
            "brand": "Interspar Restaurant",
            "brand_wikidata": "Q15820339",
            "extras": Categories.RESTAURANT.value,
        },
        "RESTAURANT": {
            "brand": "Interspar Restaurant",
            "brand_wikidata": "Q15820339",
            "extras": Categories.RESTAURANT.value,
        },
    }

    COUNTRIES = [
        {
            "country": "si",
            "path": "trgovine",
            "days": DAYS_SI,
        },
        {
            "country": "hr",
            "path": "lokacije",
            "days": DAYS_HR,
        },
        {"country": "at", "path": "standorte", "days": DAYS_DE},
        {
            "country": "hu",
            "path": "uzletek",
            "days": DAYS_HU,
        },
    ]

    def start_requests(self):
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

            brand = poi.get("plantType").get("name", "").upper()
            if tags := self.BRANDS.get(brand):
                item.update(tags)
            else:
                item["brand"] = brand
                self.crawler.stats.inc_value(f'atp/{self.name}/unknown_brand/{config["country"]}/{brand}')
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
