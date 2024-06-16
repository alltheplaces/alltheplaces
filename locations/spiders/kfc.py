from scrapy.spiders import SitemapSpider

from locations.items import set_closed
from locations.structured_data_spider import StructuredDataSpider

KFC_SHARED_ATTRIBUTES = {"brand": "KFC", "brand_wikidata": "Q524757"}


class KFCSpider(SitemapSpider, StructuredDataSpider):
    name = "kfc"
    item_attributes = KFC_SHARED_ATTRIBUTES
    sitemap_urls = ["https://locations.kfc.com/sitemap.xml"]
    sitemap_rules = [(r"com/\w\w/[^/]+/[^/]+$", "parse")]
    download_delay = 0.5
    wanted_types = ["FoodEstablishment"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"] = None
        if all(rule.endswith(" Closed") for rule in ld_data.get("openingHours", [])):
            set_closed(item)

        yield item
