import re
from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class GapTradeGBSpider(CrawlSpider):
    name = "gap_trade_gb"
    item_attributes = {"brand": "Gap", "brand_wikidata": "Q125624088"}
    start_urls = ["https://www.gap.uk.com/depot-network"]
    rules = [Rule(LinkExtractor(r"/depot-network/[^/]+$"), "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = response.url.split("/")[-1]
        item["branch"] = response.xpath('//h1[@class="unique"]/text()').get().removeprefix("GAP ")
        item["street_address"] = merge_address_lines(response.xpath('//span[@class="street"]/text()').getall())
        item["city"] = response.xpath('//input[@id="City"]/@value').get()
        item["postcode"] = response.xpath('//input[@id="PostCode"]/@value').get()
        item["website"] = response.url
        item["phone"] = response.xpath('//input[@id="PhoneNumber"]/@value').get()
        item["extras"]["fax"] = response.xpath('//input[@id="FaxNumber"]/@value').get()
        item["email"] = response.xpath('//input[@id="EmailAddress"]/@value').get()

        if m := re.search(r"initDepotMap\('.+?', (-?\d+\.\d+), (-?\d+\.\d+)\);", response.text):
            item["lat"], item["lon"] = m.groups()

        yield item
