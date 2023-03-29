from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class PaneraBreadUSSpider(SitemapSpider, StructuredDataSpider):
    name = "panera_bread_us"
    item_attributes = {"brand": "Panera Bread", "brand_wikidata": "Q7130852"}
    allowed_domains = ["panerabread.com"]
    sitemap_urls = ["https://locations.panerabread.com/robots.txt"]
    sitemap_rules = [(r"/\w\w/[-\w]+/[-\w]+\.html$", "parse_sd")]
    wanted_types = ["CafeOrCoffeeShop"]
