from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class GoodfeetSpider(SitemapSpider, StructuredDataSpider):
    name = "goodfeet"
    item_attributes = {"brand": "The Good Feet Store"}
    sitemap_urls = ["https://www.goodfeet.com/sitemap.xml"]
    sitemap_rules = [(r"/locations/(.*)$", "parse_sd")]
