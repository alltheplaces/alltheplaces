from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class KokoroGBSpider(Spider):
    name = "kokoro_gb"
    item_attributes = {"brand_wikidata": "Q117050264"}
    start_urls = ["https://kokorouk.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//*[@class="location-collapse-list"]'):
            item = Feature()
            item["branch"] = item["ref"] = location.xpath('.//*[@class="body-1"]/text()').get()
            item["addr_full"] = location.xpath('.//*[@class="body-3"]/text()').get()
            item["lat"], item["lon"] = (
                response.xpath('//*[@class="location"]/text()').get().replace("{", "").replace("}", "").split(",")
            )
            apply_category(Categories.FAST_FOOD, item)

            yield item
