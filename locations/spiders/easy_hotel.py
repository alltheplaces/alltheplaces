from typing import Iterable

import scrapy
from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class EasyHotelSpider(SitemapSpider, StructuredDataSpider):
    name = "easy_hotel"
    item_attributes = {"brand": "easyHotel", "brand_wikidata": "Q17011598"}
    sitemap_urls = ["https://www.easyhotel.com/sitemap.xml"]
    sitemap_rules = [(r"https:\/\/www\.easyhotel\.com\/hotels\/[^/]+/[^/]+$", "parse")]
    wanted_types = ["Hotel"]

    def parse(self, response: TextResponse, **kwargs):
        for link in response.xpath('//*[@data-test-id="hotel-card"]/@href').getall():
            yield scrapy.Request(url=response.urljoin(link), callback=self.parse_sd)

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["addr_full"] = response.xpath('//*[@data-test-id="location__address"]/p/text()').get()
        apply_category(Categories.HOTEL, item)
        yield item
