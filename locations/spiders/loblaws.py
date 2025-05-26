from typing import Any, Iterable

import scrapy
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import clean_address


class LoblawsSpider(scrapy.Spider):
    name = "loblaws"
    BRANDS = {
        "loblaw": ("Loblaws", "Q3257626"),
        "dominion": ("Dominion", "Q5291079"),
        "extrafoods": ("Extra Foods", "Q5422144"),
        "fortinos": ("Fortinos", "Q5472662"),
        "independent": ("Your Independent Grocer", "Q8058833"),
        "independentcitymarket": ("Independent City Market", None),
        "maxi": ("Maxi", "Q3302441"),
        "nofrills": ("No Frills", "Q3342407"),
        "provigo": ("Provigo", "Q3408306"),
        "rass": ("Real Canadian Superstore", "Q7300856"),
        "superstore": ("Atlantic Superstore", "Q4816566"),
        "valumart": ("Valu-mart", "Q7912687"),
        "wholesaleclub": ("Wholesale Club", "Q7997568"),
        "zehrs": ("Zehrs", "Q8068546"),
    }
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self) -> Iterable[JsonRequest]:
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
                item["brand"], item["brand_wikidata"] = self.BRANDS.get(
                    location.get("storeBannerId"), (location.get("storeBannerName"), None)
                )
                yield item
