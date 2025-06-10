from typing import Iterable

from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class MyerAUSpider(StructuredDataSpider):
    name = "myer_au"
    item_attributes = {"brand": "Myer", "brand_wikidata": "Q1110323"}
    allowed_domains = ["www.myer.com.au"]
    start_urls = ["https://www.myer.com.au/store-locator"]

    def parse(self, response: Response) -> Iterable[Request]:
        for store in response.xpath('//a[contains(@class, "store-locator-click")]'):
            url = "https://www.myer.com.au" + store.xpath('./@href').get()
            yield Request(url=url, callback=self.parse_sd)

    def post_process_item(self, item: Feature, response: Response, ld_data: dict) -> Iterable[Feature]:
        item["ref"] = response.url
        item["branch"] = item.pop("name", None).removeprefix("Myer ")
        item.pop("facebook", None)
        item.pop("twitter", None)
        item.pop("image", None)
        apply_category(Categories.SHOP_DEPARTMENT_STORE, item)
        yield item
