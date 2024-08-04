from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class LloydsBankGBSpider(SitemapSpider, StructuredDataSpider):
    name = "lloyds_bank_gb"
    item_attributes = {
        "brand": "Lloyds Bank",
        "brand_wikidata": "Q1152847",
        "extras": Categories.BANK.value,
    }
    sitemap_urls = ["https://branches.lloydsbank.com/sitemap.xml"]
    sitemap_rules = [(r"https:\/\/branches\.lloydsbank\.com\/[-\w]+\/[-\/'\w]+$", "parse_sd")]

    def sitemap_filter(self, entries):
        for entry in entries:
            if "event" not in entry["loc"]:
                if "phone" in entry:
                    if entry["phone"].replace(" ", "").startswith("+443"):
                        entry.pop("phone", None)
                yield entry
