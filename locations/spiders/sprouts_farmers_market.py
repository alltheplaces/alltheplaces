from typing import Any

from requests import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.google_url import extract_google_position
from locations.items import Feature


class SproutsFarmersMarketSpider(CrawlSpider):
    name = "sprouts_farmers_market"
    item_attributes = {"brand": "Sprouts Farmers Market", "brand_wikidata": "Q7581369"}
    start_urls = ["https://www.sprouts.com/stores/"]
    rules = [
        Rule(
            LinkExtractor(allow=r"https://www.sprouts.com/stores/[^/]+/"),
        ),
        Rule(LinkExtractor(allow=r"https://www.sprouts.com/store/[^/]+/[^/]+/[^/]+/"), callback="parse"),
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["branch"] = response.xpath('//*[@class="cell store-details"]/h1/text()').get()
        item["street_address"] = response.xpath('//*[@class="store-address"]/a/text()[1]').get()
        item["addr_full"] = response.xpath('//*[@class="store-address"]/a').xpath("normalize-space()").get()
        item["ref"] = item["website"] = response.url
        extract_google_position(item, response)
        yield item
