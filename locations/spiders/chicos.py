from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


# Sitemap is not available for all brands, hence CrawlSpider is used.
class ChicosSpider(CrawlSpider, StructuredDataSpider):
    name = "chicos"
    BRANDS = {
        "chicos": ("Chico's", "Q5096393"),
        "chicosofftherack": ("Chico's Off The Rack", "Q5096393"),
        "whitehouseblackmarket": ("White House Black Market", "Q7994858"),
        "soma": ("Soma", "Q69882213"),
    }
    start_urls = [
        "https://www.chicos.com/locations/locations-list/",
        "https://www.chicosofftherack.com/locations/locations-list/",
        "https://www.soma.com/locations/locations-list/",
        "https://www.whitehouseblackmarket.com/locations/locations-list/",
    ]
    rules = [
        Rule(LinkExtractor(allow=r"/locations/locations-list/\w{2}/?$")),
        Rule(LinkExtractor(allow=r"/locations/locations-list/\w{2}/[-\w]+/?$")),
        Rule(
            LinkExtractor(allow=r"/locations/\w{2}/\w{2}/[-\w]+/[-\w]+/?$"),
            callback="parse_sd",
        ),
    ]
    time_format = "%H:%M:%S"

    def post_process_item(self, item, response, ld_data, **kwargs):
        brand = response.url.split(".")[1]
        if brand_details := self.BRANDS.get(brand):
            item["brand"], item["brand_wikidata"] = brand_details
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
