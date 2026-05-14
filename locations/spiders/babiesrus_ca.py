from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class BabiesrusCASpider(SitemapSpider):
    name = "babiesrus_ca"
    item_attributes = {"brand": "Babies R Us", "brand_wikidata": "Q17232036"}
    sitemap_urls = ["https://www.babiesrus.ca/robots.txt"]
    sitemap_rules = [("ca/storelocator/", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["branch"] = response.xpath("//h1/text()").get().removeprefix("Toy Store in ")
        item["street_address"] = response.xpath('//*[@class="sidebar-section"]//p/text()').get()
        item["addr_full"] = merge_address_lines(
            [item["street_address"], response.xpath('//*[@class="sidebar-section"]//p[2]/text()').get()]
        )
        item["phone"] = response.xpath('//*[contains(@href,"tel:")]/text()').get()
        item["ref"] = item["website"] = response.url
        yield item
