from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class MassageEnvySpider(SitemapSpider, StructuredDataSpider):
    name = "massage_envy"
    item_attributes = {"brand": "Massage Envy", "brand_wikidata": "Q10327170"}
    allowed_domains = ["locations.massageenvy.com"]
    sitemap_urls = ("https://locations.massageenvy.com/sitemap.xml",)
    sitemap_rules = [
        (r"^https://locations.massageenvy.com/[^/]+/[^/]+/[^/]+.html$", "parse_sd"),
    ]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Massage Envy - ")
        yield item
