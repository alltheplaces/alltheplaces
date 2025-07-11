from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class BisquetsObregonMXSpider(scrapy.Spider):
    name = "bisquets_obregon_mx"
    item_attributes = {"name": "Bisquets Obregon", "brand": "Bisquets Obregon"}
    start_urls = ["https://bisquetsobregon.com/gps/data.php"]
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.xpath("//store//item"):
            item = Feature()
            item["branch"] = store.xpath("./location/text()").get()
            item["addr_full"] = store.xpath("./address/text()").get()
            item["lat"] = store.xpath("./latitude/text()").get()
            item["lon"] = store.xpath("./longitude/text()").get()
            item["phone"] = store.xpath("./telephone/text()").get()
            apply_category(Categories.RESTAURANT, item)
            yield item
