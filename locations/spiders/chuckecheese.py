from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class ChuckECheeseSpider(SitemapSpider, StructuredDataSpider):
    name = "chuckecheese"
    item_attributes = {"brand": "Chuck E. Cheese", "brand_wikidata": "Q2438391"}
    allowed_domains = ["locations.chuckecheese.com"]
    sitemap_urls = ["https://locations.chuckecheese.com/sitemap.xml"]
    sitemap_rules = [(r"locations\.chuckecheese\.com(?:\/[a-z]{2}){1,2}(?:\/[\w\-.]{3,}){2}", "parse_sd")]

    def post_process_item(self, item, response, ld_data):
        item.pop("image", None)
        item.pop("facebook", None)
        item.pop("twitter", None)
        yield item
