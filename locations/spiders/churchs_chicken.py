from scrapy.spiders import SitemapSpider
from locations.structured_data_spider import StructuredDataSpider


class ChurchsChickenSpider(SitemapSpider, StructuredDataSpider):
    name = "churchs_chicken"
    item_attributes = {"brand": "Church's Chicken", "brand_wikidata": "Q1089932"}
    sitemap_urls = [
        "https://locations.churchs.com/sitemap1.xml",
    ]
    sitemap_rules = [(r"https://locations.churchs.com/[^/]+/[^/]+/[a-z0-9\.A-Z-]+$", "parse_sd")]
