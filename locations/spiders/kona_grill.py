import json
from typing import Any

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.dict_parser import DictParser


class KonaGrillSpider(Spider):
    name = "kona_grill"
    item_attributes = {
        "brand": "Kona Grill",
        "brand_wikidata": "Q6428706",
    }
    allowed_domains = ["konagrill.com"]
    start_urls = ["https://konagrill.com/locations"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = response.xpath('//div[@id="map"]/@data-locations').get()
        for location in json.loads(data):
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full")
            item["website"] = location["order_online_url"]

            yield item
