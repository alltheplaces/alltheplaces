from json import dumps
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class LouvreHotelsSpider(Spider):
    name = "louvre_hotels"
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}
    brand_mappings = {
        "CA": {"brand": "Campanile", "brand_wikidata": "Q2412064"},
        "PC": {"brand": "Hôtel Première Classe", "brand_wikidata": "Q5964551"},
        "GT": {"brand": "Golden Tulip", "brand_wikidata": "Q19725996"},
        "RT": {"brand": "Golden Tulip", "brand_wikidata": "Q19725996"},
        "TI": {"brand": "Golden Tulip", "brand_wikidata": "Q19725996"},
        "TX": {"brand": "Golden Tulip", "brand_wikidata": "Q19725996"},
        "KY": {"brand": "Kyriad Hotels", "brand_wikidata": "Q11751808"},
        "KD": {"brand": "Kyriad Hotels", "brand_wikidata": "Q11751808"},
        "KP": {"brand": "Kyriad Hotels", "brand_wikidata": "Q11751808"},
        "KE": {"brand": "Kyriad Hotels", "brand_wikidata": "Q11751808"},
    }

    async def start(self) -> AsyncIterator[JsonRequest]:
        query = """
            query resortsSearchByBrandsV2($locale: String! $brandCode: String! $withCrossSell: Boolean!)
            {
                resortsSearchByBrandsV2(locale: $locale brandCode: $brandCode withCrossSell: $withCrossSell)
                {
                    resortCode resortName brandCode adress city country zipCode location {latitude longitude}
                }
            }
        """

        headers = {
            "Content-Type": "application/json",
        }

        payload = {
            "operationName": "resortsSearchByBrandsV2",
            "variables": {"locale": "en-us", "brandCode": "LHG", "withCrossSell": False},
            "query": query,
        }

        yield JsonRequest(
            url="https://api.louvrehotels.com/api/v1/graphql",
            method="POST",
            body=dumps(payload),
            headers=headers,
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        resorts = response.json()["data"]["resortsSearchByBrandsV2"]

        for resort in resorts:
            item = DictParser.parse(resort)
            item["ref"] = resort["resortCode"]
            item["branch"] = resort["resortName"]
            item["street_address"] = resort["adress"]

            if brand := self.brand_mappings.get(resort["brandCode"]):
                item.update(brand)
            else:
                self.logger.warning(f"unknown brand: {resort['brandCode']}")

            apply_category(Categories.HOTEL, item)

            yield item
