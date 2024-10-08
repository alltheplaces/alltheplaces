import json
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.carls_jr_us import CarlsJrUSSpider


class CarlsJrNZSpider(Spider):
    name = "carls_jr_nz"
    item_attributes = CarlsJrUSSpider.item_attributes
    start_urls = ["https://www.carlsjr.co.nz/stores"]
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath("//@data-block-json").getall():
            store = json.loads(location)["location"]
            item = Feature()
            item["name"] = store.get("addressTitle")
            item["lat"] = store.get("mapLat")
            item["lon"] = store.get("mapLng")
            item["addr_full"] = merge_address_lines([store.get("addressLine1"), store.get("addressLine2")])
            item["website"] = response.url
            yield item
