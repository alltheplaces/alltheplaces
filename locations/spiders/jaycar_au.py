from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class JaycarAUSpider(SitemapSpider, StructuredDataSpider):
    name = "jaycar_au"
    item_attributes = {"brand": "Jaycar", "brand_wikidata": "Q6167713"}
    sitemap_urls = ["https://www.jaycar.com.au/sitemap.xml"]
    sitemap_follow = ["/stores"]
    sitemap_rules = [("/stores/", "parse_sd")]
    time_format = "%H:%M:%S"
    wanted_types = ["ElectronicsStore"]
    user_agent = BROWSER_DEFAULT
    requires_proxy = True

    def sitemap_filter(self, entries):
        for entry in entries:
            if "_STK" not in entry["loc"]:
                # Filter out resellers
                yield entry

    def post_process_item(self, item, response, ld_data):
        if "RESELLER | " in item["name"]:
            return
        item.pop("facebook", None)
        yield item
