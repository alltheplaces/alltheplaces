import json
import re
from typing import Any

from scrapy import Request, Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class DiskaDESpider(Spider):
    name = "diska_de"
    item_attributes = {"brand": "diska", "brand_wikidata": "Q62390177"}
    start_urls = ["https://diska.de/marktsuche/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for url in response.xpath('//select[@onchange="window.location.href=this.value"]/option/@value').getall():
            yield Request(url, callback=self.parse_location)

    def parse_location(self, response: Response, **kwargs: Any) -> Any:
        data = json.loads(re.search(r"wpslMap_0 = (\{.+\});", response.text).group(1))
        for location in data["locations"]:
            item = DictParser.parse(location)
            item["addr_full"] = None
            item["street_address"] = merge_address_lines([location["address"], location["address2"]])
            item["website"] = response.url
            yield item
