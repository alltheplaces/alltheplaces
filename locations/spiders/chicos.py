from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


# Sitemap is not available for all brands, hence CrawlSpider is used.
class ChicosSpider(CrawlSpider, StructuredDataSpider):
    name = "chicos"
    BRANDS = {
        "chico's": ("Chico's", "Q5096393"),
        "chico's off the rack": ("Chico's Off The Rack", "Q5096393"),
        "white house black market": ("White House Black Market", "Q7994858"),
        "soma": ("Soma", "Q69882213"),
    }
    start_urls = [
        "https://www.chicos.com/locations/locations-list/",
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
    search_for_email = False
    search_for_facebook = False
    search_for_twitter = False

    def post_process_item(self, item, response, ld_data, **kwargs):
        if brand_tags := self.BRANDS.get(item["name"].casefold()):
            item["brand"], item["brand_wikidata"] = brand_tags
        full_name = response.xpath("//h1/text()").get()
        item["branch"] = full_name[full_name.casefold().find(" at ") + 4 :]
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
