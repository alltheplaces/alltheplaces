from typing import Any

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class PinchAPennyUSSpider(StructuredDataSpider):
    name = "pinch_a_penny_us"
    item_attributes = {"brand": "Pinch A Penny", "brand_wikidata": "Q121436109"}
    start_urls = ["https://pinchapenny.com/api/store/search?lat=28.5&lng=-81.4"]
    wanted_types = ["LocalBusiness"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["data"]:
            yield response.follow(store["url"], callback=self.parse_sd)

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Any:
        item["ref"] = ld_data.get("branchCode")
        item["branch"] = item.pop("name")
        item["lat"] = response.xpath("//@data-lat").get()
        item["lon"] = response.xpath("//@data-lng").get()
        apply_category(Categories.SHOP_SWIMMING_POOL, item)
        yield item
