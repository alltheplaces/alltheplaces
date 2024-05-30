import json
from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.dict_parser import DictParser


class TowerLoanUSSpider(CrawlSpider):
    name = "tower_loan_us"
    item_attributes = {"brand": "Tower Loan", "brand_wikidata": "Q126195732"}
    start_urls = ["https://www.towerloan.com/branch-locations/alabama-locations/"]
    rules = [Rule(LinkExtractor(r"/branch-locations/[^/]+/$"), "parse", follow=True)]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(response.xpath("//@data-branches").get()):
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["website"] = "https://www.towerloan.com/branch/{}/".format(location["slug"])

            yield item
