from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class HdIskenderTRSpider(Spider):
    name = "hd_iskender_tr"
    item_attributes = {"brand": "HD İskender", "brand_wikidata": "Q28940587"}
    start_urls = ["https://www.hdiskender.com/restoranlarimiz"]
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        locations = response.xpath('//li[contains(@class, "store-item")]')
        for location in locations:
            item = Feature()
            item["lat"] = location.xpath("@data-lat").get()
            item["lon"] = location.xpath("@data-lang").get()
            item["branch"] = location.xpath("@data-name").get()
            item["addr_full"] = location.xpath('.//span[@class="restaurant-address"]/text()').get()
            item["phone"] = location.xpath('.//span[@class="restaurant-phone"]/text()').get()
            apply_category(Categories.FAST_FOOD, item)
            yield item
