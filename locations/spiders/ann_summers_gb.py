import json
from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.dict_parser import DictParser


class AnnSummersGBSpider(CrawlSpider):
    name = "ann_summers_gb"
    item_attributes = {"brand": "Ann Summers", "brand_wikidata": "Q579524"}
    allowed_domains = ["annsummers.com"]
    start_urls = ["https://www.annsummers.com/stores"]
    rules = [Rule(LinkExtractor(allow="/stores/"), callback="parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        store = json.loads(response.xpath("//@data-locations").get())[0]
        item = DictParser.parse(store)
        item["branch"] = item.pop("name").rsplit(" (", 1)[0]
        item["website"] = response.url
        yield item
