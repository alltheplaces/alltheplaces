from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.structured_data_spider import StructuredDataSpider


class CitiTrendsUSSpider(SitemapSpider, StructuredDataSpider):
    name = "citi_trends_us"
    item_attributes = {"brand": "Citi Trends", "brand_wikidata": "Q5122438"}
    allowed_domains = ["locations.cititrends.com"]
    sitemap_urls = ["https://locations.cititrends.com/sitemap.xml"]
    sitemap_rules = [(r"com/(?!es)\w\w/[^/]+/[^/]+\.html$", "parse_sd")]
    wanted_types = ["ClothingStore"]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["name"] = None  # "Citi Trends" or "CITITRENDS", inconsistent
        item["street_address"] = merge_address_lines(
            response.xpath('//span[@itemprop="streetAddress"]/span/text()').getall()
        )
        item["branch"] = response.xpath('//span[@class="location-name-geo"]/text()').get()
        item["website"] = item["extras"]["website:en"] = response.url
        item["extras"]["website:es"] = response.url.replace(".com/", ".com/es/")
        apply_category(Categories.SHOP_CLOTHES, item)

        if response.xpath('//span[@class="location-name-brand"][contains(text(), "Coming Soon!")]').get():
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].set_closed(DAYS)

        yield item
