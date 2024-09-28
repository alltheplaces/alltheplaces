from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider
from locations.pipelines.address_clean_up import merge_address_lines



class JaycarAUSpider(SitemapSpider, StructuredDataSpider):
    name = "jaycar_au"
    item_attributes = {"brand": "Jaycar", "brand_wikidata": "Q6167713"}
    sitemap_urls = ["https://www.jaycar.com.au/sitemap.xml"]
    sitemap_follow = ["/stores"]
    sitemap_rules = [("/stores/", "parse_sd")]
    requires_proxy = True
    time_format = "%H:%M:%S"
    wanted_types = ["ElectronicsStore"]

    def sitemap_filter(self, entries):
        for entry in entries:
            if "_STK" not in entry["loc"]:
                # Filter out resellers
                yield entry

    def post_process_item(self, item, response, ld_data):
        if "RESELLER | " in item["name"]:
            return

        yield item
