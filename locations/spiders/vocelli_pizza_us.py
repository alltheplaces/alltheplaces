from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class VocelliPizzaUSSpider(SitemapSpider, StructuredDataSpider):
    name = "vocelli_pizza_us"
    item_attributes = {"brand": "Vocelli Pizza", "brand_wikidata": "Q7939247"}
    sitemap_urls = ["https://www.vocellipizza.com/stores-sitemap.xml"]
    sitemap_rules = [(r"/stores/", "parse_sd")]
    wanted_types = ["store"]
    search_for_twitter = False
    search_for_facebook = False
    drop_attributes = {"name"}
