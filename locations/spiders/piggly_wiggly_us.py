import json
import re
from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class PigglyWigglyUSSpider(CrawlSpider):
    name = "piggly_wiggly_us"
    item_attributes = {"brand": "Piggly Wiggly", "brand_wikidata": "Q3388303"}
    start_urls = ["https://www.pigglywiggly.com/store-locations/"]
    rules = [
        Rule(
            LinkExtractor(allow=r"^https://www\.pigglywiggly\.com/store-locations/[^/]+/$"),
            callback="parse_state",
        )
    ]

    def parse_state(self, response: Response, **kwargs: Any) -> Any:
        locations = json.loads(re.search(r"locations = (\[?{.+}\]?);", response.text).group(1))
        if isinstance(locations, dict):
            locations = locations.values()

        for location in locations:
            item = DictParser.parse(location)
            item["name"] = None
            item.pop("email")
            apply_category(Categories.SHOP_SUPERMARKET, item)
            yield item
