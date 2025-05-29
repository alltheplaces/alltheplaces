from typing import Any

import chompjs
from scrapy.http import Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class PolomarketPLSpider(Spider):
    name = "polomarket_pl"
    item_attributes = {"brand": "POLOmarket", "brand_wikidata": "Q11821937"}
    start_urls = ["https://polomarket.pl/sklepy"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in chompjs.parse_js_object(
            response.xpath('//script[contains(text(),"latitude")]/text()').re_first(r"stores:\s*(\[.+?\])")
        ):
            # Don't use DictParser, only few data fields are consistent with valid values, others contain variables instead of desired values.
            item = Feature()
            item["ref"] = location.get("id")
            item["lat"] = location.get("latitude")
            item["lon"] = location.get("longitude")
            item["street_address"] = clean_address(location.get("street"), min_length=3)
            apply_category(Categories.SHOP_SUPERMARKET, item)
            yield item
