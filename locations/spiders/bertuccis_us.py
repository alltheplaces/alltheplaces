import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


class BertuccisUSSpider(Spider):
    name = "bertuccis_us"
    item_attributes = {"brand": "Bertucci's", "brand_wikidata": "Q4895917"}
    start_urls = ["https://www.bertuccis.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = json.loads(
            re.search(
                r"features\":(\[.*\])};", response.xpath('//*[contains(text(),"address_line_1")]/text()').get()
            ).group(1)
        )

        for location in data:
            location.update(location.pop("properties"))
            item = DictParser.parse(location)
            item["ref"] = item["website"] = location["location_url"]
            item["branch"] = item.pop("name")
            item["street_address"] = location.get("address_line_1")
            item["addr_full"] = location.get("address_formatted")
            yield item
