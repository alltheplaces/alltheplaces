from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class CaribouCoffeeSpider(SitemapSpider, StructuredDataSpider):
    name = "caribou_coffee"
    item_attributes = {"brand": "Caribou Coffee", "brand_wikidata": "Q5039494"}
    allowed_domains = ["locations.cariboucoffee.com"]
    sitemap_urls = ["https://locations.cariboucoffee.com/robots.txt"]
    sitemap_rules = [(r"\.com/.+/.+/.+/.+$", "parse_sd")]
    wanted_types = ["CafeOrCoffeeShop"]
