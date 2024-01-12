from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.google_url import extract_google_position
from locations.items import Feature
from locations.spiders.vapestore_gb import clean_address


class TacoBellINSpider(Spider):
    name = "taco_bell_in"
    item_attributes = {"brand": "Taco Bell", "brand_wikidata": "Q752941"}
    start_urls = ["https://www.tacobell.co.in/find-us"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//div[@class="find-Us-Branches"]'):
            item = Feature()
            item["image"] = location.xpath('.//img[@class="find-Us-Branch-Img"]/@src').get()
            item["branch"] = location.xpath('normalize-space(.//div[@class="findus-heading"]/text())').get()
            item["addr_full"] = clean_address(location.xpath('.//p[@class="findus_addr"]/text()').getall())
            item["phone"] = location.xpath('.//a[@class="mobile-no"]/@rel').get()
            extract_google_position(item, location)
            item["ref"] = item["website"] = location.xpath('.//a[@class="restro-detail"]/@href').get()

            yield item
