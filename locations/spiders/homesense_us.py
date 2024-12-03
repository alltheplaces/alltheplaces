import re
from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class HomesenseUSSpider(CrawlSpider):
    name = "homesense_us"
    item_attributes = {"brand": "HomeSense", "brand_wikidata": "Q16844433"}
    start_urls = ["https://us.homesense.com/all-stores"]
    rules = [Rule(LinkExtractor(allow="/store-details/"), callback="parse")]
    user_agent = BROWSER_DEFAULT

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["branch"] = response.xpath('//div[@id="store-details-hero"]//h2/text()').get()
        item["addr_full"] = response.xpath('//*[@id="store-details-amenities"]//p').xpath("normalize-space()").get()
        item["ref"] = item["website"] = response.url
        item["phone"] = response.xpath('//*[contains(@href,"tel:")]/text()').get()

        if m := re.search(r"initMap\((-?\d+\.\d+),\s*(-?\d+\.\d+)\);", response.text):
            item["lat"], item["lon"] = m.groups()

        yield item
