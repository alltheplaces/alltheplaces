from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class JdSportsPTSpider(CrawlSpider, StructuredDataSpider):
    name = "jd_sports_pt"
    item_attributes = {"brand": "JD Sports", "brand_wikidata": "Q6108019"}
    start_urls = ["https://www.jdsports.pt/store-locator/all-stores/"]
    rules = [Rule(LinkExtractor(allow="store-locator/", deny="-soon"), callback="parse_sd")]
