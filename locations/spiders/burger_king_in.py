from scrapy.spiders import SitemapSpider

from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES
from locations.structured_data_spider import StructuredDataSpider


class BurgerKingINSpider(SitemapSpider, StructuredDataSpider):
    name = "burger_king_in"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    sitemap_urls = ["https://stores.burgerking.in/robots.txt"]
    sitemap_rules = [(r"/burger-king-fast-food-restaurant-[-\w\d]+/Home$", "parse_sd")]
    time_format = "%I:%M %p"
    search_for_twitter = False
    search_for_facebook = False
    wanted_types = ["Restaurant"]  # Duplicate items in SD on each page
