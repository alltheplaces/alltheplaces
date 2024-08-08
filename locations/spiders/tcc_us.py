from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class TccUSSpider(SitemapSpider, StructuredDataSpider):
    name = "tcc_us"
    item_attributes = {
        "brand": "Verizon",
        "brand_wikidata": "Q919641",
        "operator": "The Cellular Connection",
        "operator_wikidata": "Q121336519",
    }
    drop_attributes = {"image"}
    sitemap_urls = ["https://locations.tccrocks.com/sitemap.xml"]
    sitemap_rules = [(r"https://locations.tccrocks.com/\w\w/.+/.+\.html", "parse_sd")]
    wanted_types = ["MobilePhoneStore"]
