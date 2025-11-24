from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import clean_address


class LoblawsSpider(Spider):
    name = "loblaws"
    BRANDS = {
        "loblaw": ("Loblaws", "Q3257626", "loblaws"),
        "dominion": ("Dominion", "Q5291079", "newfoundlandgrocerystores"),
        "extrafoods": ("Extra Foods", "Q5422144", "extrafoods"),
        "fortinos": ("Fortinos", "Q5472662", "fortinos"),
        "independent": ("Your Independent Grocer", "Q8058833", "yourindependentgrocer"),
        "independentcitymarket": ("Independent City Market", None, "independentcitymarket"),
        "maxi": ("Maxi", "Q3302441", "maxi"),
        "nofrills": ("No Frills", "Q3342407", "nofrills"),
        "provigo": ("Provigo", "Q3408306", "provigo"),
        "superstore": ("Real Canadian Superstore", "Q7300856", "realcanadiansuperstore"),
        "rass": ("Atlantic Superstore", "Q4816566", "atlanticsuperstore"),
        "valumart": ("Valu-mart", "Q7912687", "valumart"),
        "wholesaleclub": ("Wholesale Club", "Q7997568", "wholesaleclub"),
        "zehrs": ("Zehrs", "Q8068546", "zehrs"),
    }
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[JsonRequest]:
        for banner_id in self.BRANDS:
            yield JsonRequest(
                url=f"https://api.pcexpress.ca/pcx-bff/api/v1/pickup-locations?bannerIds={banner_id}",
                headers={"x-apikey": "C1xujSegT5j3ap3yexJjqhOfELwGKYvz"},
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        results = response.json()
        if isinstance(results, dict) and "errors" in results:  # bannerId might be invalid/changed.
            self.logger.error(f'Error message: {results["errors"][0]["message"]}')
        else:
            for location in results:
                if location.get("visible") is False:
                    continue
                item = DictParser.parse(location)
                item["street_address"] = clean_address(
                    [location["address"].get("line1"), location["address"].get("line2")]
                )
                if brand_details := self.BRANDS.get(location.get("storeBannerId")):
                    item["brand"], item["brand_wikidata"], slug = brand_details
                    item["website"] = f'https://www.{slug}.ca/en/store-locator/details/{location["storeId"]}'

                apply_category(Categories.SHOP_SUPERMARKET, item)
                yield item
