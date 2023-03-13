from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class SonicDriveinSpider(SitemapSpider, StructuredDataSpider):
    name = "sonic_drivein"
    item_attributes = {"brand": "Sonic Drive-In", "brand_wikidata": "Q7561808"}
    sitemap_urls = ["https://locations.sonicdrivein.com/robots.txt"]
    sitemap_rules = [(".html", "parse_sd")]

    def pre_process_data(self, ld_data, **kwargs):
        ld_data["name"] = None
        ld_data["image"] = None
