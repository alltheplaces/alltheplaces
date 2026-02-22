from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class Pizzeria105PLSpider(SitemapSpider, StructuredDataSpider):
    name = "pizzeria_105_pl"
    allowed_domains = ["105.pl"]
    item_attributes = {"brand": "Pizzeria 105", "brand_wikidata": "Q123090276"}
    sitemap_urls = ["https://105.pl/sitemap.xml"]
    sitemap_rules = [(r"https://105.pl/pizzeria-(.*)/", "parse_sd")]
    wanted_types = ["Place"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["website"] = item["ref"] = response.url
        yield item
