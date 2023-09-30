from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class CaribouCoffeeUSSpider(SitemapSpider, StructuredDataSpider):
    name = "caribou_coffee_us"
    item_attributes = {"brand": "Caribou Coffee", "brand_wikidata": "Q5039494"}
    allowed_domains = ["locations.cariboucoffee.com"]
    sitemap_urls = ["https://locations.cariboucoffee.com/sitemap.xml"]
    sitemap_rules = [(r"\.com/.+/.+/.+/.+$", "parse_sd")]
    wanted_types = ["CafeOrCoffeeShop"]
