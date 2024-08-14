from typing import Any
from urllib.parse import urljoin

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.items import Feature


class JoulesSpider(Spider):
    name = "joules"
    item_attributes = {"brand": "Joules", "brand_wikidata": "Q25351738"}
    start_urls = ["https://www.joules.com/storelocator/data/stores"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["Stores"]:
            item = Feature()
            item["ref"] = location["BR"]
            item["lat"] = location["LT"]
            item["lon"] = location["LN"]
            item["branch"] = location["NA"]
            s = location["NA"]
            name = "".join(s.split()).lower() + "/" + location["BR"]
            item["website"] = urljoin("https://www.joules.com/storelocator/", name)
            yield item
