from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class BusyBeesGBSpider(SitemapSpider, StructuredDataSpider):
    name = "busy_bees_gb"
    item_attributes = {"brand": "Busy Bees", "brand_wikidata": "Q28134563"}
    sitemap_urls = ["https://www.busybeeschildcare.co.uk/sitemap.xml"]
    sitemap_rules = [("", "parse_sd")]
    requires_proxy = True

    def sitemap_filter(self, entries):
        for entry in entries:
            if "/nursery" in entry["loc"] and not "meet-the-team" in entry["loc"]:
                yield entry
