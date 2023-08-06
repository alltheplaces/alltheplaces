from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class CartersUSSpider(SitemapSpider, StructuredDataSpider):
    name = "carters_us"
    item_attributes = {"brand": "Carter's", "brand_wikidata": "Q5047083"}
    allowed_domains = ["locations.carters.com"]
    sitemap_urls = ["https://locations.carters.com/robots.txt"]
    sitemap_rules = [
        (r"https://locations\.carters\.com/.*/.*/.*", "parse"),
    ]
