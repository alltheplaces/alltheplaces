from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class BlazePizzaSpider(SitemapSpider, StructuredDataSpider):
    name = "blaze_pizza"
    item_attributes = {"brand": "Blaze Pizza", "brand_wikidata": "Q23016666"}
    sitemap_urls = ["https://locations.blazepizza.com/sitemap.xml"]
    sitemap_rules = [(r"https://locations.blazepizza.com/[^/]+/[^/]+/[a-zA-z0-9-]+", "parse_sd")]
