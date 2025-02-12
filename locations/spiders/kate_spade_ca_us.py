from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.spiders.kate_spade import KateSpadeSpider
from locations.structured_data_spider import StructuredDataSpider


class KateSpadeCAUSSpider(SitemapSpider, StructuredDataSpider):
    name = "kate_spade_ca_us"
    item_attributes = KateSpadeSpider.item_attributes
    sitemap_urls = ["https://www.katespade.com/robots.txt"]
    sitemap_rules = [(r"/stores/\w\w/\w\w/[-\w]+/[-\w]+$", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Kate Spade ")
        yield item
