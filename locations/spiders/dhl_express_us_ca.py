import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class DhlExpressUsSpider(SitemapSpider, StructuredDataSpider):
    name = "dhl_express_us_ca"
    item_attributes = {
        "brand": "DHL",
        "brand_wikidata": "Q489815",
    }
    sitemap_urls = [
        "https://locations.us.express.dhl.com/sitemap.xml",
        "https://locations.ca.express.dhl.com/sitemap.xml",
    ]
    sitemap_rules = [(r"/[0-9]+", "parse_sd")]
    wanted_types = ["Store"]

    def post_process_item(self, item, response, ld_data):
        item["country"] = re.findall(r"\.ca|\.us", response.url)[0][1:].upper()
        apply_category(Categories.POST_OFFICE, item)
        yield item
