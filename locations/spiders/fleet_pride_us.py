from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class FleetPrideUSSpider(SitemapSpider, StructuredDataSpider):
    name = "fleet_pride_us"
    item_attributes = {"brand": "FleetPride", "brand_wikidata": "Q121436710"}
    sitemap_urls = ["https://branches.fleetpride.com/robots.txt"]
    sitemap_rules = [(r"com/\w\w/[^/]+/[^/]+(?<!-sc)\.html$", "parse")]
    wanted_types = ["AutoPartsStore"]

    def pre_process_data(self, ld_data, **kwargs):
        ld_data["name"] = None
