from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Rule

from locations.dict_parser import DictParser
from locations.spiders.choices_flooring_au import ChoicesFlooringAUSpider


class ChoicesFlooringNZSpider(ChoicesFlooringAUSpider):
    name = "choices_flooring_nz"
    allowed_domains = ["www.choicesflooring.co.nz"]
    start_urls = [
        "https://www.choicesflooring.co.nz/stores",
    ]
    rules = [Rule(LinkExtractor(allow=r"\/stores\/[^\/]+\/?$"), callback="parse_location_page")]

    def parse_location_details(self, response):
        item = DictParser.parse(response.json())
        item.pop("state", None)
        item["website"] = f"https://{self.allowed_domains[0]}" + response.json()["storeUrl"]
        item["opening_hours"] = response.meta["opening_hours"]
        yield item
