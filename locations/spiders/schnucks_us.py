from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class SchnucksUSSpider(SitemapSpider, StructuredDataSpider):
    name = "schnucks_us"
    item_attributes = {"brand": "Schnucks", "brand_wikidata": "Q7431920"}
    sitemap_urls = ["https://schnucks.com/locations.sitemap.xml"]
    sitemap_rules = [("/locations/", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name")
        yield item
