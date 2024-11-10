from typing import Any

from scrapy.http import Response
from scrapy.spiders import Spider
from urllib.parse import urljoin
from locations.dict_parser import DictParser


class PopeyesGBSpider(Spider):
    name = "popeyes_gb"
    item_attributes = {"brand": "Popeyes", "brand_wikidata": "Q1330910"}

    start_urls = ["https://pe-uk-ordering-api-fd-eecsdkg6btfeg0cc.z01.azurefd.net/api/v2/restaurants"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]:
            item = DictParser.parse(location)
            item["geometry"] = location["storeLocation"]["coordinates"]
            item["branch"] = item["name"]
            item["name"] = "Popeyes"
            slug = location["slug"]
            item["website"] = urljoin('https://popeyesuk.com/restaurants/',slug)
            yield item
