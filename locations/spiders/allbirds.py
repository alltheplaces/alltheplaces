import json
from typing import Any

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class AllbirdsSpider(Spider):
    name = "allbirds"
    item_attributes = {"brand": "Allbirds", "brand_wikidata": "Q30591057"}
    start_urls = ["https://www.allbirds.com/pages/stores"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(response.xpath('//script[contains(@id, "store-locator-data")]/text()').get())[
            "stores"
        ]:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["ref"] = location["handle"]
            item["state"] = location.get("stateProvince")
            item["postcode"] = location["zipPostalCode"]
            item["country"] = location["countryRegion"]
            item["website"] = "https://www.allbirds.com/pages/stores/" + item["ref"]

            apply_category(Categories.SHOP_SHOES, item)

            yield item
