from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class ItsFashionsUSSpider(SitemapSpider, StructuredDataSpider):
    name = "its_fashions_us"
    item_attributes = {"brand": "It's Fashion", "brand_wikidata": "Q122762765", "extras": Categories.SHOP_CLOTHES.value}
    sitemap_urls = ["https://stores.itsfashions.com/robots.txt"]
    sitemap_rules = [(r"\.com/\w\w/[-.\w]+/[-.\w]+$", "parse_sd")]
    wanted_types = ["ClothingStore"]
    drop_attributes = {"image"}
