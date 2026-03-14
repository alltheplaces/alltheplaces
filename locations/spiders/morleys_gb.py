from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class MorleysGBSpider(Spider):
    name = "morleys_gb"
    item_attributes = {"brand": "Morley's", "brand_wikidata": "Q21008528"}
    start_urls = ["https://www.morleyschicken.com/stores"]
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//div[@role="listitem"]'):
            item = Feature()
            item["branch"] = location.xpath(".//h3/span/text()").get().removeprefix("Morley's ")
            item["addr_full"] = merge_address_lines(location.xpath(".//h2/span//text()").getall())

            apply_category(Categories.FAST_FOOD, item)

            yield item
