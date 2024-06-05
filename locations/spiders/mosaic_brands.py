from scrapy import Selector, Spider
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class MosaicBrandSpider(Spider):
    name = "mosaic_brands"
    allowed_domains = [
        "www.autographfashion.com.au",
        "www.katies.com.au",
        "www.millers.com.au",
        "www.nonib.com.au",
        "www.rivers.com.au",
        "www.rockmans.com.au",
    ]
    brands = {
        "www.autographfashion.com.au": {
            "brand": "Autograph",
            "brand_wikidata": "Q120646111",
            "extras": Categories.SHOP_CLOTHES.value,
        },
        "www.katies.com.au": {"brand": "Katies", "brand_wikidata": "Q120646115"},
        "www.millers.com.au": {"brand": "Millers", "brand_wikidata": "Q120644857"},
        "www.nonib.com.au": {
            "brand": "Noni B",
            "brand_wikidata": "Q120645737",
            "extras": Categories.SHOP_CLOTHES.value,
        },
        "www.rivers.com.au": {"brand": "Rivers", "brand_wikidata": "Q106224813"},
        "www.rockmans.com.au": {"brand": "Rockmans", "brand_wikidata": "Q120646031"},
    }
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        for brand_domain in self.allowed_domains:
            yield JsonRequest(
                url=f"https://{brand_domain}/on/demandware.store/Sites-mosaic-au-Site/en_AU/Stores-FindStoresInBrand?showMap=false&radius=100000&limit=10000&postalCode=2000"
            )

    def parse(self, response):
        for location in response.json()["stores"]:
            if (
                "ONLINE" in location["name"].upper().split()
                or "ONLINESTORE" in location["name"].upper().split()
                or "PRICING STORE" in location["name"].upper()
                or "CLOSED" in location["name"].upper().split()
            ):
                continue

            item = DictParser.parse(location)
            item["street_address"] = clean_address([location["address1"], location["address2"]])

            if location["stateCode"] == "NZ":
                item["country"] = "NZ"
                item.pop("state", None)
            else:
                item["country"] = "AU"

            for brand_domain, brand_attributes in self.brands.items():
                if brand_domain in response.url:
                    item.update(brand_attributes)
                    break
            if location.get("storeHours"):
                hours_string = " ".join(filter(None, Selector(text=location["storeHours"]).xpath("//text()").getall()))
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_ranges_from_string(hours_string)

            yield item
