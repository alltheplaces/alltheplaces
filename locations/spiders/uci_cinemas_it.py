import re
from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.user_agents import BROWSER_DEFAULT


class UciCinemasITSpider(CrawlSpider):
    name = "uci_cinemas_it"
    item_attributes = {"brand": "UCI", "brand_wikidata": "Q521922"}
    start_urls = ["https://ucicinemas.it/cinema/"]
    rules = [Rule(LinkExtractor(allow=r"/cinema/uci-.*"), callback="parse")]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}
    requires_proxy = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["name"] = response.xpath("//h1/text()").get()
        item["addr_full"] = clean_address(
            response.xpath('//*[@class="text-gray-1 text-base"]').xpath("normalize-space()").get()
        )
        item["lat"], item["lon"] = re.search(r"\"(-?\d+\.\d+)\",\"(-?\d+\.\d+)\"", response.text).groups()
        item["ref"] = item["website"] = response.url
        yield item
