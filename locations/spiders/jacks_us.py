from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class JacksUSSpider(CrawlSpider, StructuredDataSpider):
    name = "jacks_us"
    item_attributes = {"brand": "Jack's", "brand_wikidata": "Q6110826"}
    drop_attributes = {"name"}
    start_urls = ["https://locations.eatatjacks.com/locations-list/"]
    rules = [
        Rule(LinkExtractor(r"/locations-list/\w\w$")),
        Rule(LinkExtractor(r"/locations-list/\w\w/[^/]+/$")),
        Rule(LinkExtractor(r"com/\w\w/[^/]+/[^/]+/$"), "parse"),
    ]
    wanted_types = ["LocalBusiness"]
    search_for_facebook = False
    search_for_twitter = False
