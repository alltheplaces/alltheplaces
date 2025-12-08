import json
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.linked_data_parser import LinkedDataParser


class YourMoveGBSpider(Spider):
    name = "your_move_gb"
    item_attributes = {"brand": "Your Move", "brand_wikidata": "Q81078416"}
    start_urls = ["https://www.your-move.co.uk/branches"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        items = json.loads(
            response.xpath('//script[@type="application/ld+json"][contains(text(), "RealEstateAgent")]/text()').get()
        )
        for location in items["itemListElement"]:
            item = LinkedDataParser.parse_ld(location)
            item["branch"] = item.pop("name")
            item["image"] = location["image"]["url"]
            item["ref"] = item["website"].split("/")[-1]
            yield item
