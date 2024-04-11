from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.items import set_closed
from locations.structured_data_spider import StructuredDataSpider


class BupaGBSpider(SitemapSpider, StructuredDataSpider):
    name = "bupa_gb"
    item_attributes = {"brand": "Bupa", "brand_wikidata": "Q931628", "extras": Categories.DENTIST.value}
    sitemap_urls = ["https://www.bupa.co.uk/robots.txt"]
    sitemap_rules = [(r"/practices/([-\w]+)$", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if "Total Dental Care" in item["name"]:
            item["brand"] = "Total Dental Care"

        if item["name"].lower().endswith(" - closed"):
            set_closed(item)

        yield item
