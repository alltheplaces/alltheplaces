from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class BadcockUSSpider(Spider):
    name = "badcock_us"
    item_attributes = {"brand": "Badcock", "brand_wikidata": "Q4840663"}
    start_urls = ["https://www.badcock.com/StoreLocator/GetRemainingShops"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath("//li[@data-shopid]"):
            item = Feature()
            item["ref"] = location.xpath("@data-shopid").get()
            item["website"] = response.urljoin(location.xpath('.//a[@class="shop-link"]/@href').get())
            item["branch"] = location.xpath(".//@data-shop-title").get()
            item["lat"] = location.xpath(".//@data-latitude").get()
            item["lon"] = location.xpath(".//@data-longitude").get()
            item["street_address"] = location.xpath('.//div[@class="short-description"]/p[1]/text()').get()
            item["addr_full"] = merge_address_lines(
                location.xpath('.//div[@class="short-description"]/p[position()<3]/text()').getall()
            )

            yield item
