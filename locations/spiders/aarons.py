from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class AaronsSpider(CrawlSpider, StructuredDataSpider):
    name = "aarons"
    item_attributes = {"brand": "Aaron's", "brand_wikidata": "Q10397787", "extras": Categories.SHOP_FURNITURE.value}
    start_urls = ["https://www.aarons.com/locations/us", "https://www.aarons.com/locations/ca"]
    rules = [
        Rule(LinkExtractor(allow=r"/[a-z]{2}/[a-z]{2}/?$")),
        Rule(LinkExtractor(allow=r"/[a-z]{2}/[a-z]{2}/[-\w]+/[-\w]+"), callback="parse_sd"),
    ]
    drop_attributes = {"name", "image"}
    wanted_types = ["Store"]
    search_for_twitter = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        if not item.get("street_address"):
            return
        yield item
