from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, DAYS_FR, OpeningHours, sanitise_day

BRANDS = {
    "Beauty Boutique by Shoppers": None,
    "Pharmaprix": ({"brand": "Pharmaprix", "brand_wikidata": "Q1820137"}, Categories.PHARMACY),
    "Pharmaprix Simplement Santé": None,
    "Shoppers Drug Mart": ({"brand": "Shoppers Drug Mart", "brand_wikidata": "Q1820137"}, Categories.PHARMACY),
    "Shoppers Simply Pharmacy": ({"brand": "Shoppers Drug Mart", "brand_wikidata": "Q1820137"}, Categories.PHARMACY),
    "Specialty Care Centre": None,
    "The Health Clinic by Shoppers<sup>TM</sup>": ({"name": "The Health Clinic by Shoppers"}, Categories.CLINIC),
    "Wellwise": ({"brand": "Wellwise"}, Categories.SHOP_MEDICAL_SUPPLY),
}


class ShoppersDrugMartCASpider(Spider):
    name = "shoppers_drug_mart_ca"
    start_urls = ["https://www.shoppersdrugmart.ca/en/store-locator", "https://www.pharmaprix.ca/en/store-locator"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # Collect cookies
        yield response.follow(
            "/sdmapi/store/getnearbystoresbyminmax?minLat=-90&minLng=-180&maxLat=90&maxLng=180",
            callback=self.parse_api,
        )

    def parse_api(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full")
            item["state"] = location["Province"]["Abbreviation"]
            item["name"] = location["StoreType"]["DisplayName"]
            item["branch"] = location["Name"]
            item["website"] = item["extras"]["website:en"] = response.urljoin(
                "/en/store-locator/store/{}".format(location["StoreID"])
            )
            item["extras"]["website:fr"] = response.urljoin("/fr/store-locator/store/{}".format(location["StoreID"]))

            item["opening_hours"] = OpeningHours()
            for day, times in zip(location["WeekDays"], location["StoreHours"]):
                if times == "CLOSED":
                    continue
                elif times == "24 Hours":
                    times = "12:00 AM - 12:00 AM"
                times = times.replace("Midnight", "12:00 AM")

                item["opening_hours"].add_range(
                    sanitise_day(day, DAYS_FR | DAYS_EN), *times.split(" - "), time_format="%I:%M %p"
                )

            if props := BRANDS.get(location["StoreType"]["DisplayName"]):
                item.update(props[0])
                apply_category(props[1], item)

            yield item
