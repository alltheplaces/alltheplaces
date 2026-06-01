from typing import Any

from chompjs import chompjs
from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class PizzaRanchUSSpider(CrawlSpider):
    name = "pizza_ranch_us"
    item_attributes = {"brand": "Pizza Ranch", "brand_wikidata": "Q7199978"}
    allowed_domains = ["pizzaranch.com"]
    start_urls = ["https://pizzaranch.com/all-locations"]
    rules = [Rule(LinkExtractor(allow=r"/all-locations/[^/]+$"), callback="parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "var locations =")]/text()').get()
        ):
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            apply_category(Categories.RESTAURANT, item)
            yield item
