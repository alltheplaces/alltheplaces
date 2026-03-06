import json
from typing import Any

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.dict_parser import DictParser


class AllbirdsSpider(Spider):
    name = "allbirds"
    item_attributes = {"brand": "Allbirds", "brand_wikidata": "Q30591057"}
    start_urls = ["https://www.allbirds.com/pages/stores"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(
            response.xpath("//*[@id='store-locator-data-template--16112999661648__store_locator_pdFFMK']/text()").get()
        )["stores"]:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["ref"] = location["handle"]
            item["postcode"] = location["zipPostalCode"]
            item["state"] = location["stateProvince"]
            item["website"] = "https://www.allbirds.com/pages/stores/" + item["ref"]
            yield item
