from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class GuessSpider(SitemapSpider, StructuredDataSpider):
    name = "guess"
    item_attributes = {"brand": "Guess", "brand_wikidata": "Q2470307", "extras": Categories.SHOP_CLOTHES.value}
    sitemap_urls = ["https://stores.guess.com/sitemap.xml"]
    sitemap_rules = [(".html", "parse_sd")]
    wanted_types = ["ClothingStore"]
    custom_settings = {"REDIRECT_ENABLED": False}
