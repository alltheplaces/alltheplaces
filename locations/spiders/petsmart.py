from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class PetsmartSpider(SitemapSpider, StructuredDataSpider):
    name = "petsmart"
    item_attributes = {"brand": "PetSmart", "brand_wikidata": "Q3307147"}
    sitemap_urls = [
        "https://www.petsmart.com/sitemap_index.xml",
        "https://www.petsmart.ca/sitemap_index.xml",
    ]
    sitemap_rules = [(r"/stores/[^/]+/[^/]+/[^/]+html$", "parse_sd")]
    time_format = "%H:%M:%S"

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name")
        extract_google_position(item, response)
        yield item
