from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature
from locations.structured_data_spider import extract_phone


class KokoroGBSpider(Spider):
    name = "kokoro_gb"
    item_attributes = {"brand": "Kokoro", "brand_wikidata": "Q117050264"}
    start_urls = ["https://kokorouk.com/branches/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath("//article"):
            item = Feature()
            item["ref"] = item["branch"] = location.xpath("h4/text()").get()
            item["addr_full"] = (
                location.xpath('p[contains(text(), "Address: ")]/text()').get().removeprefix("Address: ")
            )
            extract_phone(item, location)
            extract_google_position(item, location)

            apply_category(Categories.FAST_FOOD, item)

            yield item
