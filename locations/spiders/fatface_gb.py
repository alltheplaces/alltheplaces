from typing import Any

from scrapy import Request
from scrapy.http import Response

from locations.items import Feature
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

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        store = response.meta["store_info"]
        item["ref"] = store.get("BR")
        item["lat"] = store.get("LT")
        item["lon"] = store.get("LN")
        item["branch"] = item.pop("name").split("-")[0].strip()
        yield item
