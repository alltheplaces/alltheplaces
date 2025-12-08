from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class BusyBeesGBSpider(SitemapSpider, StructuredDataSpider):
    name = "busy_bees_gb"
    item_attributes = {"brand": "Busy Bees", "brand_wikidata": "Q28134563"}
    sitemap_urls = ["https://www.busybeeschildcare.co.uk/sitemap.xml"]
    sitemap_rules = [("", "parse_sd")]

    def sitemap_filter(self, entries):
        for entry in entries:
            if "/nursery" in entry["loc"] and "meet-the-team" not in entry["loc"]:
                yield entry
