from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature, set_closed
from locations.structured_data_spider import StructuredDataSpider

BUPA = {"brand": "Bupa", "brand_wikidata": "Q931628"}


class BupaGBSpider(SitemapSpider, StructuredDataSpider):
    name = "bupa_gb"
    sitemap_urls = ["https://www.bupa.co.uk/robots.txt"]
    sitemap_rules = [(r"/practices/([-\w]+)$", "parse_sd")]
    time_format = "%I:%M %p"

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        if "Total Dental Care" in item["name"]:
            item["brand"] = "Total Dental Care"
        elif "Bupa" in item["name"]:
            item.update(BUPA)

        if item["name"].lower().endswith(" - closed"):
            set_closed(item)

        apply_category(Categories.DENTIST, item)

        yield item
