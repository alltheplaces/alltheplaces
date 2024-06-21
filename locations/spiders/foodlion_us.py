from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class FoodLionUSSpider(SitemapSpider, StructuredDataSpider):
    name = "foodlion_us"
    item_attributes = {"brand": "Food Lion", "brand_wikidata": "Q1435950"}
    sitemap_urls = ["https://stores.foodlion.com/sitemap.xml"]
    sitemap_rules = [(r"https://stores.foodlion.com/\w{2}/[-\w]+/[-\w]+", "parse_sd")]
    requires_proxy = True
