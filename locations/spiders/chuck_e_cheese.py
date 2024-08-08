from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class ChuckECheeseSpider(SitemapSpider, StructuredDataSpider):
    name = "chuck_e_cheese"
    item_attributes = {"brand": "Chuck E. Cheese", "brand_wikidata": "Q2438391"}
    allowed_domains = ["locations.chuckecheese.com"]
    sitemap_urls = ["https://locations.chuckecheese.com/sitemap.xml"]
    sitemap_rules = [(r"locations\.chuckecheese\.com(?:\/[a-z]{2}){1,2}(?:\/[\w\-.]{3,}){2}", "parse_sd")]
    wanted_types = ["AmusementPark"]

    def post_process_item(self, item, response, ld_data):
        item.pop("image", None)
        item.pop("facebook", None)
        item.pop("twitter", None)
        item.pop("name", None)
        yield item
