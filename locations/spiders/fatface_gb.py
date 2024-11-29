from typing import Any

from scrapy import Request
from scrapy.http import Response

from locations.spiders.fatface import FatfaceSpider
from locations.structured_data_spider import StructuredDataSpider


class FatfaceGBSpider(StructuredDataSpider):
    name = "fatface_gb"
    item_attributes = FatfaceSpider.item_attributes
    start_urls = ["https://www.fatface.com/storelocator/data/stores"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["Stores"]:
            slug = f'{store["NA"].replace(" ", "").lower()}/{store["BR"]}'
            yield Request(
                url=response.urljoin(slug).replace("/data", ""), callback=self.parse_sd, meta=dict(store_info=store)
            )
