from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class SuitDirectGBSpider(Spider):
    name = "suit_direct_gb"
    item_attributes = {"name": "Suit Direct", "brand": "Suit Direct"}
    start_urls = ["https://www.suitdirect.co.uk/store-locator"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath("//div[@data-storeid]"):
            item = Feature()
            item["ref"] = location.xpath("@data-storeid").get()
            item["lat"] = location.xpath(".//@data-storelatitude").get()
            item["lon"] = location.xpath(".//@data-storelongitude").get()
            item["branch"] = location.xpath('//h5[contains(@class, "store-name")]/text()').get()
            item["street_address"] = location.xpath('.//span[@class="store-single-line"]/text()').get()
            item["postcode"] = location.xpath('.//span[@class="store-postcode"]/text()').get()
            item["website"] = response.urljoin(location.xpath('.//span[@class="store-url"]/text()').get())
            item["phone"] = location.xpath('.//span[@class="store-telephone"]/text()').get()

            apply_category(Categories.SHOP_CLOTHES, item)

            yield item
