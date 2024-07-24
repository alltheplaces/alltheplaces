from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class HalifaxGBSpider(SitemapSpider, StructuredDataSpider):
    name = "halifax_gb"
    item_attributes = {
        "brand": "Halifax",
        "brand_wikidata": "Q3310164",
        "extras": Categories.BANK.value,
    }
    sitemap_urls = ["https://branches.halifax.co.uk/sitemap.xml"]
    sitemap_rules = [(r"https:\/\/branches\.halifax\.co\.uk\/[-'\w]+\/[-'\/\w]+$", "parse_sd")]

    def sitemap_filter(self, entries):
        for entry in entries:
            if "event" not in entry["loc"].lower():
                yield entry
