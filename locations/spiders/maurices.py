from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class MauricesSpider(SitemapSpider, StructuredDataSpider):
    name = "maurices"
    item_attributes = {"brand": "Maurices", "brand_wikidata": "Q6793571"}
    sitemap_urls = ["https://locations.maurices.com/sitemap.xml"]
    sitemap_rules = [(r"com/\w\w/\w\w/[^/]+/[^/]+$", "parse_sd")]
    drop_attributes = {"image"}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("maurices ")
        yield item
