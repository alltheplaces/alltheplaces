from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class EatnParkUSSpider(SitemapSpider, StructuredDataSpider):
    name = "eatn_park_us"
    item_attributes = {"brand": "Eat'n Park", "brand_wikidata": "Q5331211"}
    sitemap_urls = ["https://locations.eatnpark.com/robots.txt"]
    sitemap_rules = [(r"/restaurants-(\d+)\.html", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Eat'n Park Restaurant").strip(" -")
        yield item
