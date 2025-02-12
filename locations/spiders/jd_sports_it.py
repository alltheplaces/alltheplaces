from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class JdSportsITSpider(CrawlSpider, StructuredDataSpider):
    name = "jd_sports_it"
    item_attributes = {"brand": "JD Sports", "brand_wikidata": "Q6108019"}
    start_urls = ["https://www.jdsports.it/store-locator/all-stores/"]
    rules = [Rule(LinkExtractor(allow="store-locator/", deny="-soon"), callback="parse_sd")]
