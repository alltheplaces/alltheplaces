from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class RockBottomSpider(CrawlSpider, StructuredDataSpider):
    name = "rock_bottom"
    item_attributes = {"brand": "Rock Bottom", "brand_wikidata": "Q73504866", "extras": Categories.RESTAURANT.value}
    allowed_domains = ["rockbottom.com"]
    download_delay = 0.5
    start_urls = ["https://www.rockbottom.com/locations"]
    rules = [Rule(LinkExtractor(allow="/locations/"), callback="parse_sd")]
    wanted_types = [["Restaurant", "LocalBusiness"]]
