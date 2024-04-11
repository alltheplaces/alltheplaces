from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.google_url import extract_google_position
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.spiders.taco_bell import TACO_BELL_SHARED_ATTRIBUTES
from locations.structured_data_spider import extract_phone


class TacoBellAUSpider(CrawlSpider):
    name = "taco_bell_au"
    item_attributes = TACO_BELL_SHARED_ATTRIBUTES
    start_urls = ["https://tacobell.com.au/order-now-locations/"]
    rules = [Rule(LinkExtractor(restrict_xpaths=['//a[text()="Order Now"]']), callback="parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["name"] = clean_address(response.xpath('//h1[@class="location-title"]/text()').getall())
        item["addr_full"] = clean_address(response.xpath('//div[@class="dir"]/text()').getall())
        if addr := response.xpath('//p[contains(text(), "Address: ")]/text()').get():
            item["addr_full"] = clean_address(addr).removeprefix("Address: ")

        extract_google_position(item, response)
        extract_phone(item, response)
        if item.get("phone").startswith("Phone: "):
            item["phone"] = item["phone"].removeprefix("Phone: ")

        yield item
