from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature


class DedemanSpider(CrawlSpider):
    name = "dedeman"
    start_urls = ["https://www.dedeman.com/"]
    rules = [Rule(LinkExtractor(r"/oteller/[^/]+$"), "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = response.xpath('//input[@id="id"]/@value').get()
        item["name"] = response.xpath('//input[@id="name"]/@value').get()
        item["addr_full"] = response.xpath('//div[@class="desc"]/div[@class="text"]/text()').get()
        item["website"] = response.url
        item["email"] = response.xpath('//div[@class="emt"]//div[contains(text(), "@")]/text()').get()

        extract_google_position(item, response)

        apply_category(Categories.HOTEL, item)

        if "/oteller/dedeman-" in response.url:
            item["brand"] = "Dedeman"
        elif "/oteller/park-dedeman-" in response.url:
            item["brand"] = "Park Dedeman"

        yield item
