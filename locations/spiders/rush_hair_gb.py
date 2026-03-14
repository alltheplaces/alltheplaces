import re
from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines

# Microdata is malformed


class RushHairGBSpider(CrawlSpider):
    name = "rush_hair_gb"
    item_attributes = {"brand": "Rush Hair", "brand_wikidata": "Q132737191"}
    start_urls = ["https://www.rush.co.uk/salon-finder"]
    rules = [Rule(LinkExtractor(r"/salons/([^/]+)$"), callback="parse")]
    sitemap_urls = ["https://www.rush.co.uk/robots.txt"]
    sitemap_rules = [(r"/salons/([^/]+)$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["phone"] = response.xpath('//div[@class="phone"]/a/text()').get()
        item["name"] = response.xpath("//h1/text()").get()
        item["addr_full"] = merge_address_lines(response.xpath('//span[@itemprop="streetAddress"]/text()').getall())

        if m := re.search(r"LatLng\((-?\d+\.\d+),\s?(-?\d+\.\d+)\)", response.text):
            item["lat"], item["lon"] = m.groups()

        yield item
