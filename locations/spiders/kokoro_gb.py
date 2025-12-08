from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class KokoroGBSpider(Spider):
    name = "kokoro_gb"
    item_attributes = {"brand_wikidata": "Q117050264"}
    start_urls = ["https://kokorouk.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//div[contains(@class, "wp-block-group-is-layout-flex")]'):
            item = Feature()
            item["ref"] = item["branch"] = location.xpath("h2/text()").get()
            item["addr_full"] = merge_address_lines(location.xpath("p/text()").getall())

            apply_category(Categories.FAST_FOOD, item)

            yield item
