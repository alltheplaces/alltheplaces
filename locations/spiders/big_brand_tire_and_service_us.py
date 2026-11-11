from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class BigBrandTireAndServiceUSSpider(SitemapSpider, StructuredDataSpider):
    name = "big_brand_tire_and_service_us"
    item_attributes = {"brand": "Big Brand Tire & Service", "brand_wikidata": "Q120784816"}
    allowed_domains = ["www.bigbrandtire.com"]
    sitemap_urls = ["https://www.bigbrandtire.com/sitemap.xml"]
    sitemap_rules = [("/locations/", "parse_sd")]
    wanted_types = ["TireShop"]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Big Brand Tire & Service - ")
        yield item
