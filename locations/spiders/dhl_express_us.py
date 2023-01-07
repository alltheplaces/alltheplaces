from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class DhlExpressUsSpider(SitemapSpider, StructuredDataSpider):
    name = "dhl_express_us"
    item_attributes = {
        "brand": "DHL",
        "brand_wikidata": "Q489815",
    }
    sitemap_urls = ["https://locations.us.express.dhl.com/sitemap.xml"]
    sitemap_rules = [("/[0-9]+", "parse_sd")]
    wanted_types = ["Store"]
