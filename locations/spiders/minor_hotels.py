from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class MinorHotelsSpider(SitemapSpider, StructuredDataSpider):
    name = "minor_hotels"
    item_attributes = {"operator": "Minor Hotels", "operator_wikidata": "Q25108728"}
    sitemap_urls = ["https://www.minorhotels.com/en/sitemap_minor_en.xml"]
    sitemap_rules = [(r"/en/destinations/[-\w]+/[-\w]+/[-\w]+$", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        apply_category(Categories.HOTEL, item)
        yield item
