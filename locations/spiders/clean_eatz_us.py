from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class CleanEatzUSSpider(SitemapSpider, StructuredDataSpider):
    name = "clean_eatz_us"
    item_attributes = {"brand": "Clean Eatz", "brand_wikidata": "Q124412638", "extras": Categories.FAST_FOOD.value}
    sitemap_urls = ["https://locations.cleaneatz.com/robots.txt"]
    sitemap_rules = [(r"com/\w\w/[^/]+/meal-prep-(\d+).html$", "parse")]
    wanted_types = ["Restaurant"]

    def pre_process_data(self, ld_data, **kwargs):
        ld_data["name"] = None
