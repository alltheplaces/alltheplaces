from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider


class JdSportsDESpider(CrawlSpider, StructuredDataSpider, PlaywrightSpider):
    name = "jd_sports_de"
    item_attributes = {"brand": "JD Sports", "brand_wikidata": "Q6108019"}
    start_urls = ["https://www.jdsports.de/store-locator/all-stores/"]
    rules = [Rule(LinkExtractor(allow="store-locator/", deny="-soon"), callback="parse_sd")]
    requires_proxy = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS
